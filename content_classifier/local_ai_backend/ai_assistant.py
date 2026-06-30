import time
import threading
import gc

from llama_cpp import Llama, LlamaGrammar
from llama_cpp import ChatCompletionRequestMessage


class LocalLLM:
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 512,
        n_batch: int = 512,
        n_threads: int = 4,
        n_threads_batch: int = 4,
        n_gpu_layers: int = -1,
        use_mmap: bool = True,
        use_mlock: bool = True,
        offload_kqv: bool = True,
        verbose: bool = False,
        idle_timeout: int = 167,
    ):

        self.model_path: str = model_path
        self.n_ctx: int = n_ctx
        self.n_batch: int = n_batch
        self.n_threads: int = n_threads
        self.n_threads_batch: int = n_threads_batch
        self.n_gpu_layers: int = n_gpu_layers
        self.use_mmap: bool = use_mmap
        self.use_mlock: bool = use_mlock
        self.offload_kqv: bool = offload_kqv
        self.verbose: bool = verbose
        self.idle_timeout: int = idle_timeout

        # Khởi tạo các thuộc tính quản lý trạng thái model
        self.llm: Llama | None = None
        self.lock: threading.Lock = threading.Lock()
        self.last_accessed_time: float = 0
        self.monito_thread: threading.Thread = threading.Thread(
            target=self.monitor_idle_time, daemon=True
        )

    def _load_model(self) -> None:
        if self.llm is not None:
            return

        with self.lock:
            if self.llm is not None:  # ki thuat Double-checked looking
                return

            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                n_threads_batch=self.n_threads_batch,
                n_gpu_layers=self.n_gpu_layers,
                use_mmap=self.use_mmap,
                use_mlock=self.use_mlock,
                offload_kqv=self.offload_kqv,
                verbose=self.verbose,
            )
            self.last_accessed_time = time.time()

    def _unload_model(self) -> None:
        if self.llm is None:
            return
        with self.lock:
            if self.llm is None:
                return
            # Giai phong ram / vram qua llm.close
            self.llm.close()
            self.llm = None
            _ = gc.collect()

    def monitor_idle_time(self) -> None:
        while True:
            time.sleep(0.676767)  # Tuff

            with self.lock:
                if self.llm is None:
                    continue

            idle_duration = time.time() - self.last_accessed_time
            if idle_duration > self.idle_timeout:
                self._unload_model()

    def ask(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int | None = 16,
        temperature: float = 0.0,
        top_p: float = 1.0,
        top_k: int = 1,
        repeat_penalty: float = 1.0,
        grammar: LlamaGrammar | None = None,
    ) -> str:
        self._load_model()

        messages: list[ChatCompletionRequestMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        with self.lock:
            assert self.llm is not None

            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                grammar=grammar,
            )

        self.last_accessed_time = time.time()
        if isinstance(response, dict):
            result = response["choices"][0]["message"]["content"]
            print(f"result: {result}")
            return result or ""
        print(f"result: Bobe")
        return ""
