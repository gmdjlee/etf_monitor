"""
Controller Decorators
API 컨트롤러에서 사용하는 공통 데코레이터들입니다.
"""

from functools import wraps
from typing import Callable

from config.logging_config import get_logger
from flask import jsonify

logger = get_logger(__name__)


def handle_controller_errors(
    default_message: str = "요청 처리 중 오류가 발생했습니다.",
):
    """
    컨트롤러 메서드의 에러를 자동으로 처리하는 데코레이터

    모든 예외를 잡아서 일관된 에러 응답을 반환합니다.

    Args:
        default_message: 사용자에게 표시할 기본 에러 메시지

    Examples:
        >>> @handle_controller_errors("ETF를 조회할 수 없습니다.")
        >>> def get_etf(self, ticker):
        ...     etf = self.etf_repo.find_by_ticker(ticker)
        ...     return jsonify(etf.to_dict()), 200
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ValueError as e:
                # 비즈니스 로직 검증 오류 (400)
                logger.warning(f"Validation error in {func.__name__}: {e}")
                return jsonify({"status": "error", "message": str(e)}), 400
            except Exception as e:
                # 예상치 못한 오류 (500)
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                return jsonify({"status": "error", "message": default_message}), 500

        return wrapper

    return decorator


def log_api_call(func: Callable) -> Callable:
    """
    API 호출을 자동으로 로깅하는 데코레이터

    Examples:
        >>> @log_api_call
        >>> def get_all_etfs(self):
        ...     return jsonify(etfs), 200
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from flask import request

        logger.info(f"{request.method} {request.path} - {func.__name__}")
        return func(self, *args, **kwargs)

    return wrapper


def require_etf_exists(func: Callable) -> Callable:
    """
    ETF 존재 여부를 자동으로 확인하는 데코레이터

    ticker 파라미터가 있는 메서드에서 사용합니다.

    Examples:
        >>> @require_etf_exists
        >>> def get_etf_detail(self, ticker: str):
        ...     # ETF 존재 확인은 이미 완료됨
        ...     return jsonify(details), 200
    """

    @wraps(func)
    def wrapper(self, ticker: str, *args, **kwargs):
        if not self.etf_repo.exists(ticker):
            return jsonify(
                {"status": "error", "message": f"ETF를 찾을 수 없습니다: {ticker}"}
            ), 404
        return func(self, ticker, *args, **kwargs)

    return wrapper
