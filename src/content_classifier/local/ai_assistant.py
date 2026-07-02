import pickle
import threading
import time
from pathlib import Path
from typing import Any, Protocol

_GB = 1073741824  # 1024 ** 3 bytes
_DEFAULT_IDLE_TIMEOUT_SECONDS = 167.0


class _ScikitLearnModel(Protocol):
    classes_: Any

    def predict_proba(self, texts: list[str]) -> Any:
        """Return label probabilities for input texts."""


def _idle_timeout_seconds(model_path: Path) -> float:
    """Estimate how long the model can stay idle before it is unloaded."""
    try:
        size_bytes = model_path.stat().st_size
    except OSError:
        return _DEFAULT_IDLE_TIMEOUT_SECONDS

    if size_bytes <= 0:
        return _DEFAULT_IDLE_TIMEOUT_SECONDS

    timeout = _DEFAULT_IDLE_TIMEOUT_SECONDS * (size_bytes / _GB)
    return max(1.0, timeout)


class LocalAI:
    def __init__(self, model_path: str | Path) -> None:
        """Create a lazy-loading scikit-learn wrapper with idle cleanup."""
        self._model_path: Path = Path(model_path)
        self._model: _ScikitLearnModel | None = None
        self._lock: threading.RLock = threading.RLock()
        self._stop_event: threading.Event = threading.Event()
        self._last_used_at: float = time.monotonic()
        self._idle_timeout: float = _idle_timeout_seconds(self._model_path)
        self._monitor_thread: threading.Thread = threading.Thread(
            target=self._monitor_idle_time,
            name="LocalAIIdleMonitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def predict(
        self, text: str, k: int = -1, threshold: float = 0.0
    ) -> dict[str, float]:
        """Load the model if needed and return normalized label probabilities."""

        model = self._load_model()
        probabilities = model.predict_proba([text])[0]
        with self._lock:
            self._last_used_at = time.monotonic()

        ranked_predictions = sorted(
            zip(model.classes_, probabilities),
            key=lambda prediction: float(prediction[1]),
            reverse=True,
        )
        selected_predictions = ranked_predictions if k < 0 else ranked_predictions[:k]

        return {
            str(label): float(probability)
            for label, probability in selected_predictions
            if float(probability) >= threshold
        }

    def _load_model(self) -> _ScikitLearnModel:
        """Load the model once and keep it cached until it is unloaded."""
        with self._lock:
            if self._model is not None:
                self._last_used_at = time.monotonic()
                return self._model

            with self._model_path.open("rb") as model_file:
                self._model = pickle.load(model_file)
            return self._model

    def _unload_model(self) -> None:
        """Drop the cached model reference."""
        with self._lock:
            self._model = None

    def _monitor_idle_time(self) -> None:
        """Background loop that unloads the model after it stays idle."""
        while not self._stop_event.wait(0.67):
            with self._lock:
                if self._model is None:
                    continue

            idle_seconds = time.monotonic() - self._last_used_at
            if idle_seconds >= self._idle_timeout:
                self._unload_model()

    def close(self) -> None:
        """Stop background monitoring and unload the model."""
        self._stop_event.set()
        self._unload_model()
