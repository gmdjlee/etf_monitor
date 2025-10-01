"""
Base Repository
모든 리포지토리의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

# 제네릭 타입 변수
T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepository(ABC, Generic[T, ID]):
    """
    기본 리포지토리 인터페이스

    CRUD 작업의 기본 메서드를 정의합니다.
    모든 구체적인 리포지토리는 이 인터페이스를 구현해야 합니다.

    Type Parameters:
        T: 엔티티 타입
        ID: 식별자 타입
    """

    @abstractmethod
    def save(self, entity: T) -> None:
        """
        엔티티를 저장합니다.

        Args:
            entity: 저장할 엔티티
        """
        pass

    @abstractmethod
    def save_all(self, entities: List[T]) -> None:
        """
        여러 엔티티를 일괄 저장합니다.

        Args:
            entities: 저장할 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_by_id(self, id: ID) -> Optional[T]:
        """
        ID로 엔티티를 조회합니다.

        Args:
            id: 엔티티 식별자

        Returns:
            찾은 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        모든 엔티티를 조회합니다.

        Returns:
            엔티티 리스트
        """
        pass

    @abstractmethod
    def exists(self, id: ID) -> bool:
        """
        ID에 해당하는 엔티티가 존재하는지 확인합니다.

        Args:
            id: 엔티티 식별자

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    def delete(self, id: ID) -> None:
        """
        ID에 해당하는 엔티티를 삭제합니다.

        Args:
            id: 엔티티 식별자
        """
        pass

    @abstractmethod
    def delete_all(self) -> None:
        """모든 엔티티를 삭제합니다."""
        pass

    @abstractmethod
    def count(self) -> int:
        """
        전체 엔티티 개수를 반환합니다.

        Returns:
            엔티티 개수
        """
        pass


class ReadOnlyRepository(ABC, Generic[T, ID]):
    """
    읽기 전용 리포지토리 인터페이스

    조회 작업만 필요한 경우 사용합니다.
    """

    @abstractmethod
    def find_by_id(self, id: ID) -> Optional[T]:
        """ID로 엔티티를 조회합니다."""
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """모든 엔티티를 조회합니다."""
        pass

    @abstractmethod
    def exists(self, id: ID) -> bool:
        """엔티티 존재 여부를 확인합니다."""
        pass

    @abstractmethod
    def count(self) -> int:
        """전체 엔티티 개수를 반환합니다."""
        pass


class TransactionalRepository(ABC):
    """
    트랜잭션을 지원하는 리포지토리 인터페이스

    트랜잭션이 필요한 작업에 사용합니다.
    """

    @abstractmethod
    def begin_transaction(self) -> None:
        """트랜잭션을 시작합니다."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """트랜잭션을 커밋합니다."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """트랜잭션을 롤백합니다."""
        pass


class RepositoryException(Exception):
    """리포지토리 작업 중 발생하는 예외의 기본 클래스"""

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class EntityNotFoundError(RepositoryException):
    """엔티티를 찾을 수 없을 때 발생하는 예외"""

    def __init__(self, entity_type: str, id: any):
        message = f"{entity_type} with id '{id}' not found"
        super().__init__(message)
        self.entity_type = entity_type
        self.id = id


class DuplicateEntityError(RepositoryException):
    """중복된 엔티티가 존재할 때 발생하는 예외"""

    def __init__(self, entity_type: str, id: any):
        message = f"{entity_type} with id '{id}' already exists"
        super().__init__(message)
        self.entity_type = entity_type
        self.id = id


class RepositoryConnectionError(RepositoryException):
    """데이터 저장소 연결 오류"""

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(f"Repository connection error: {message}", original_exception)
