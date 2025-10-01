"""
Base DTO
모든 DTO의 기본 클래스입니다.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, TypeVar

T = TypeVar("T", bound="BaseDTO")


@dataclass
class BaseDTO:
    """
    모든 DTO의 기본 클래스

    공통 메서드를 제공하여 보일러플레이트 코드를 제거합니다.

    Examples:
        >>> @dataclass
        >>> class UserDTO(BaseDTO):
        ...     name: str
        ...     age: int
        >>>
        >>> user = UserDTO(name="John", age=30)
        >>> user.to_dict()
        {'name': 'John', 'age': 30}
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        DTO를 딕셔너리로 변환합니다.

        Returns:
            딕셔너리 형태의 데이터
        """
        return asdict(self)

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """
        딕셔너리로부터 DTO 인스턴스를 생성합니다.

        Args:
            data: 딕셔너리 데이터

        Returns:
            DTO 인스턴스
        """
        return cls(**data)

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        fields = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"
