"""Day la khung logger trung tam cua ung dung
Dau vao: Path(__file__)
Dau ra: logging.Logger da duoc cau hinh san(formatter, file handler,v.v).
Module can log goi get_logger de lay logger rieng. log tong hop vao logs/app.log
Mac dinh cai gi cung ghi log het, bat ke info, warning, err, critical.

Module khac khong can biet handler, formatter hay config nam o dau. Chi can:

    from logger import get_logger
    log = get_logger(__file__)
    log.debug("message=%s", value)

neu file goi log o project_root/foo/eubebhy.py log
log vo logs/foo/eubebhy.py.log

Logic hoat dong:
1. `setup_log()` reset root logger va tao cac file log tong hop.
2. `get_logger(__file__)` dang ky logger rieng cho file dang goi.
3. Logger rieng vua ghi vao file module, vua propagate len root logger.
4. Root logger ghi tiep vao `app.log`, `error.log`, va print ra console neu config bat.

Quy uoc file log:
- `logs/app.log`: moi log di qua root logger.
- `logs/error.log`: log muc `ERROR` tro len.
- `logs/<relative_source_path>.log`: log rieng cua tung file source.
- Vi du `tests/logger.py` -> `logs/tests/logger.py.log`.

Khi them log cho module moi:
- Dat `log = get_logger(__file__)` gan dau file sau import.
- Dung `log.debug/info/warning/error/critical(...)` nhu logger chuan cua Python.
- Dung `%s`/`%r` thay vi f-string neu message co du lieu tinh toan, de logging tu
  xu ly format khi level do that su duoc ghi.
"""

import logging
import sys
from pathlib import Path
from typing import ClassVar

from config import AppConfig, Config


LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class Logger:
    _is_setup: ClassVar[bool] = False
    _registered_names: ClassVar[set[str]] = set()
    _module_handler_paths: ClassVar[set[Path]] = set()

    @classmethod
    def setup(cls, config: AppConfig | None = None) -> None:
        """Khoi tao handler tong hop cua he thong.

        Note cho nguoi tap code:
        Root logger la diem gom log chung. Moi logger rieng cua module van propagate
        len root logger, nen mot dong log co the xuat hien o ca file module va
        `app.log`. Khi setup lai trong test, phai go handler module cu de tranh ghi
        lap vao file log tam da bi xoa.
        """

        active_config = config or Config.getconfig()
        active_config.logs_dir.mkdir(parents=True, exist_ok=True)
        cls._remove_module_file_handlers()
        cls._module_handler_paths.clear()

        root_logger = logging.getLogger()
        root_logger.setLevel(_log_level(active_config.log_level))
        root_logger.handlers.clear()

        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        app_log_path = active_config.logs_dir / active_config.log_file_name
        app_file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
        app_file_handler.setLevel(_log_level(active_config.log_level))
        app_file_handler.setFormatter(formatter)
        root_logger.addHandler(app_file_handler)

        error_log_path = active_config.logs_dir / active_config.error_log_file_name
        error_file_handler = logging.FileHandler(error_log_path, encoding="utf-8")
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        root_logger.addHandler(error_file_handler)

        if active_config.critical_log_to_console and not active_config.log_to_console:
            critical_console_handler = logging.StreamHandler(sys.stderr)
            critical_console_handler.setLevel(logging.CRITICAL)
            critical_console_handler.setFormatter(formatter)
            root_logger.addHandler(critical_console_handler)

        if active_config.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(_log_level(active_config.log_level))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        cls._is_setup = True

    @classmethod
    def registry(cls, module_file_path: str | Path) -> logging.Logger:
        """Dang ky va tra ve logger cho mot file source.

        Ham nay la API cap thap hon `get_logger()`. Module ung dung nen goi
        `get_logger(__file__)`; test hoac code ha tang co the goi truc tiep ham nay
        khi can truyen `Path` gia lap.
        """

        if not cls._is_setup:
            cls.setup()

        logger_name = _module_logger_name(Path(module_file_path))
        cls._registered_names.add(logger_name)
        logger = logging.getLogger(logger_name)
        cls._attach_module_file_handler(logger, Path(module_file_path))
        return logger

    @classmethod
    def registered_names(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._registered_names))

    @classmethod
    def _attach_module_file_handler(
        cls,
        logger: logging.Logger,
        module_file_path: Path,
    ) -> None:
        """Gan FileHandler rieng cho logger module neu chua co.

        Moi module chi nen co mot handler rieng. `_module_handler_paths` dung de
        chan viec goi `get_logger(__file__)` nhieu lan lam mot dong log bi ghi lap
        nhieu lan vao cung mot file.
        """

        config = Config.getconfig()
        if not config.module_log_enabled:
            return

        log_path = _module_log_path(module_file_path)
        if log_path in cls._module_handler_paths:
            return

        log_path.parent.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        module_file_handler = logging.FileHandler(log_path, encoding="utf-8")
        module_file_handler.setLevel(_log_level(config.module_log_level))
        module_file_handler.setFormatter(formatter)
        setattr(module_file_handler, "_sag_module_log_path", log_path)
        logger.addHandler(module_file_handler)
        logger.setLevel(
            min(logger.level or logging.CRITICAL, _log_level(config.module_log_level))
        )
        cls._module_handler_paths.add(log_path)

    @classmethod
    def _remove_module_file_handlers(cls) -> None:
        """Go cac handler module khi setup lai logger.

        Test thuong setup logger voi `logs_dir` tam thoi nhieu lan. Neu khong go
        handler cu, logger se tiep tuc giu file handle toi log dir cu va lam ket qua
        test kho doan.
        """

        for logger_name in cls._registered_names:
            logger = logging.getLogger(logger_name)
            for handler in list(logger.handlers):
                if getattr(handler, "_sag_module_log_path", None) is None:
                    continue
                logger.removeHandler(handler)
                handler.close()


def setup_log(config: AppConfig | None = None) -> None:
    Logger.setup(config=config)


def get_logger(module_file_path: str | Path) -> logging.Logger:
    """Tra ve logger rieng cho file goi ham.

    Input nen la `__file__` cua module dang can log. Logger tu tao file log rieng
    theo duong dan source, vi du `src/a.py` -> `logs/src/a.py.log`.
    """

    return Logger.registry(module_file_path)


def _log_level(level_name: str) -> int:
    return logging.getLevelNamesMapping().get(level_name.upper(), logging.INFO)


def _module_logger_name(module_file_path: Path) -> str:
    config = Config.getconfig()
    resolved_path = module_file_path.resolve()

    try:
        relative_path = resolved_path.relative_to(config.project_root)
    except ValueError:
        relative_path = resolved_path

    if relative_path.suffix == ".py":
        relative_path = relative_path.with_suffix("")

    return ".".join(relative_path.parts)


def _module_log_path(module_file_path: Path) -> Path:
    """Tao path log rieng tu path source.

    Quy tac quan trong: khong replace `.py` bang `.log`, ma them `.log` vao sau ten
    file goc. Cach nay giu lien ket truc quan giua source va log:

        src/foo.py -> logs/src/foo.py.log
    """

    config = Config.getconfig()
    resolved_path = module_file_path.resolve()

    try:
        relative_path = resolved_path.relative_to(config.project_root)
    except ValueError:
        relative_path = Path(resolved_path.name)

    return config.logs_dir / relative_path.with_name(f"{relative_path.name}.log")
