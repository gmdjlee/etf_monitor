"""
로깅 설정
애플리케이션 전체의 로깅을 구성합니다.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import settings


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    애플리케이션 로깅 설정

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 안함)
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
    """
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포맷터 생성
    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT, datefmt=settings.LOG_DATE_FORMAT
    )

    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 생성

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        설정된 로거 인스턴스

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    클래스에 로거를 추가하는 믹스인

    Examples:
        >>> class MyService(LoggerMixin):
        ...     def do_something(self):
        ...         self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """클래스별 로거 반환"""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


def log_function_call(func):
    """
    함수 호출을 로깅하는 데코레이터

    Examples:
        >>> @log_function_call
        ... def my_function(x, y):
        ...     return x + y
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(
                f"{func.__name__} raised {type(e).__name__}: {e}", exc_info=True
            )
            raise

    return wrapper


def log_execution_time(func):
    """
    함수 실행 시간을 로깅하는 데코레이터

    Examples:
        >>> @log_execution_time
        ... def slow_function():
        ...     time.sleep(1)
    """
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} executed in {elapsed:.2f} seconds")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f} seconds: {e}")
            raise

    return wrapper


class LogContext:
    """
    컨텍스트 매니저로 로그 레벨을 일시적으로 변경

    Examples:
        >>> with LogContext(logging.DEBUG):
        ...     # 이 블록에서는 DEBUG 레벨 로그가 출력됨
        ...     logger.debug("This will be shown")
    """

    def __init__(self, level: int, logger: Optional[logging.Logger] = None):
        self.level = level
        self.logger = logger or logging.getLogger()
        self.original_level = None

    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """
    예외를 상세하게 로깅

    Args:
        logger: 로거 인스턴스
        exception: 발생한 예외
        context: 추가 컨텍스트 정보
    """
    error_type = type(exception).__name__
    error_msg = str(exception)

    log_message = f"{error_type}: {error_msg}"
    if context:
        log_message = f"{context} - {log_message}"

    logger.error(log_message, exc_info=True)


# 애플리케이션 시작 시 기본 로깅 설정
def initialize_logging():
    """애플리케이션 시작 시 호출되는 로깅 초기화 함수"""
    log_file = None

    # 운영 환경에서는 파일 로깅 활성화
    if settings.is_production():
        log_dir = os.path.join(settings.BASE_DIR, "logs")
        log_file = os.path.join(log_dir, "app.log")

    setup_logging(log_file=log_file)
