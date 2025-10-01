"""
Result 타입 - 명시적 에러 처리를 위한 모나드 패턴
성공/실패를 타입으로 표현하여 예외 처리를 명확하게 만듭니다.
"""

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T]):
    """
    연산의 성공 또는 실패를 나타내는 불변 객체

    Examples:
        >>> result = Result.ok(42)
        >>> result.is_success()
        True
        >>> result.value
        42

        >>> error = Result.fail("Something went wrong")
        >>> error.is_success()
        False
        >>> error.error
        "Something went wrong"
    """

    _success: bool
    _value: Optional[T] = None
    _error: Optional[str] = None

    @staticmethod
    def ok(value: T) -> "Result[T]":
        """성공 결과 생성"""
        return Result(_success=True, _value=value, _error=None)

    @staticmethod
    def fail(error: str) -> "Result[T]":
        """실패 결과 생성"""
        return Result(_success=False, _value=None, _error=error)

    def is_success(self) -> bool:
        """성공 여부 확인"""
        return self._success

    def is_failure(self) -> bool:
        """실패 여부 확인"""
        return not self._success

    @property
    def value(self) -> T:
        """성공 시 값 반환, 실패 시 예외 발생"""
        if not self._success:
            raise ValueError(f"Cannot get value from failed result: {self._error}")
        return self._value

    @property
    def error(self) -> str:
        """실패 시 에러 메시지 반환, 성공 시 예외 발생"""
        if self._success:
            raise ValueError("Cannot get error from successful result")
        return self._error

    def value_or(self, default: T) -> T:
        """성공 시 값, 실패 시 기본값 반환"""
        return self._value if self._success else default

    def map(self, func: Callable[[T], "Result[T]"]) -> "Result[T]":
        """성공 시 함수 적용, 실패 시 그대로 반환 (모나드 패턴)"""
        if self._success:
            try:
                return func(self._value)
            except Exception as e:
                return Result.fail(str(e))
        return self

    def __repr__(self) -> str:
        if self._success:
            return f"Result.ok({self._value})"
        return f"Result.fail({self._error})"
