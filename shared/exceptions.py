"""
커스텀 예외 클래스들
애플리케이션 전반에서 사용되는 도메인 특화 예외들을 정의합니다.
"""


class ETFMonitorException(Exception):
    """모든 애플리케이션 예외의 기본 클래스"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Domain Layer Exceptions
class DomainException(ETFMonitorException):
    """도메인 레이어 예외"""

    pass


class EntityNotFoundException(DomainException):
    """엔티티를 찾을 수 없을 때"""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(
            f"{entity_type} not found: {identifier}",
            {"entity_type": entity_type, "identifier": identifier},
        )


class InvalidEntityException(DomainException):
    """엔티티가 유효하지 않을 때"""

    def __init__(self, entity_type: str, reason: str):
        super().__init__(
            f"Invalid {entity_type}: {reason}",
            {"entity_type": entity_type, "reason": reason},
        )


class BusinessRuleViolationException(DomainException):
    """비즈니스 규칙 위반"""

    def __init__(self, rule: str, reason: str):
        super().__init__(
            f"Business rule violated - {rule}: {reason}",
            {"rule": rule, "reason": reason},
        )


# Application Layer Exceptions
class ApplicationException(ETFMonitorException):
    """애플리케이션 레이어 예외"""

    pass


class UseCaseException(ApplicationException):
    """유스케이스 실행 중 발생하는 예외"""

    pass


class DataCollectionException(ApplicationException):
    """데이터 수집 중 발생하는 예외"""

    def __init__(self, source: str, reason: str):
        super().__init__(
            f"Data collection failed from {source}: {reason}",
            {"source": source, "reason": reason},
        )


# Infrastructure Layer Exceptions
class InfrastructureException(ETFMonitorException):
    """인프라 레이어 예외"""

    pass


class DatabaseException(InfrastructureException):
    """데이터베이스 관련 예외"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Database operation '{operation}' failed: {reason}",
            {"operation": operation, "reason": reason},
        )


class ExternalAPIException(InfrastructureException):
    """외부 API 호출 관련 예외"""

    def __init__(self, api_name: str, reason: str):
        super().__init__(
            f"External API '{api_name}' call failed: {reason}",
            {"api_name": api_name, "reason": reason},
        )


# Presentation Layer Exceptions
class PresentationException(ETFMonitorException):
    """프레젠테이션 레이어 예외"""

    pass


class ValidationException(PresentationException):
    """입력 검증 실패"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Validation failed for '{field}': {reason}",
            {"field": field, "reason": reason},
        )


class AuthorizationException(PresentationException):
    """권한 부족"""

    def __init__(self, resource: str):
        super().__init__(
            f"Access denied to resource: {resource}", {"resource": resource}
        )


# Utility function for exception mapping
def map_exception_to_http_status(exception: Exception) -> int:
    """예외를 HTTP 상태 코드로 매핑"""
    exception_map = {
        EntityNotFoundException: 404,
        ValidationException: 400,
        AuthorizationException: 403,
        BusinessRuleViolationException: 422,
        DatabaseException: 500,
        ExternalAPIException: 502,
    }

    for exc_type, status_code in exception_map.items():
        if isinstance(exception, exc_type):
            return status_code

    return 500  # Internal Server Error
