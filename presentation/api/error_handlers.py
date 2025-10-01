"""
Global Error Handlers
전역 예외 처리 및 에러 응답 표준화
✅ Medium Priority: 에러 처리 일관성 개선
"""

from config.logging_config import LoggerMixin
from flask import Flask, jsonify
from shared.exceptions import (
    ApplicationException,
    BusinessRuleViolationException,
    DatabaseException,
    DomainException,
    EntityNotFoundException,
    ETFMonitorException,
    ExternalAPIException,
    InfrastructureException,
    InvalidEntityException,
    PresentationException,
    ValidationException,
    map_exception_to_http_status,
)
from werkzeug.exceptions import HTTPException


class ErrorHandlers(LoggerMixin):
    """
    전역 예외 핸들러 등록 클래스

    Flask 앱에 모든 예외 핸들러를 등록하고,
    일관된 에러 응답 형식을 제공합니다.
    """

    @staticmethod
    def register_all_handlers(app: Flask) -> None:
        """
        모든 에러 핸들러를 Flask 앱에 등록합니다.

        Args:
            app: Flask 애플리케이션 인스턴스
        """
        handler = ErrorHandlers()

        # HTTP 예외 (400, 404, 500 등)
        app.register_error_handler(HTTPException, handler.handle_http_exception)

        # 도메인 예외
        app.register_error_handler(
            EntityNotFoundException, handler.handle_entity_not_found
        )
        app.register_error_handler(
            InvalidEntityException, handler.handle_invalid_entity
        )
        app.register_error_handler(
            BusinessRuleViolationException, handler.handle_business_rule_violation
        )
        app.register_error_handler(DomainException, handler.handle_domain_exception)

        # 애플리케이션 예외
        app.register_error_handler(
            ApplicationException, handler.handle_application_exception
        )

        # 인프라 예외
        app.register_error_handler(DatabaseException, handler.handle_database_exception)
        app.register_error_handler(
            ExternalAPIException, handler.handle_external_api_exception
        )
        app.register_error_handler(
            InfrastructureException, handler.handle_infrastructure_exception
        )

        # 프레젠테이션 예외
        app.register_error_handler(
            ValidationException, handler.handle_validation_exception
        )
        app.register_error_handler(
            PresentationException, handler.handle_presentation_exception
        )

        # 기본 애플리케이션 예외
        app.register_error_handler(
            ETFMonitorException, handler.handle_etf_monitor_exception
        )

        # 모든 예외의 최종 처리
        app.register_error_handler(Exception, handler.handle_generic_exception)

        handler.logger.info("All error handlers registered successfully")

    def handle_http_exception(self, error: HTTPException):
        """
        HTTP 예외 처리 (404, 405, 500 등)
        """
        self.logger.warning(f"HTTP Exception: {error.code} - {error.description}")

        return jsonify(
            {
                "status": "error",
                "error_type": "HTTPException",
                "message": error.description,
                "code": error.code,
            }
        ), error.code

    def handle_entity_not_found(self, error: EntityNotFoundException):
        """엔티티를 찾을 수 없는 경우"""
        self.logger.warning(f"Entity not found: {error.message}")

        return jsonify(
            {
                "status": "error",
                "error_type": "EntityNotFound",
                "message": error.message,
                "details": error.details,
            }
        ), 404

    def handle_invalid_entity(self, error: InvalidEntityException):
        """엔티티 유효성 검증 실패"""
        self.logger.warning(f"Invalid entity: {error.message}")

        return jsonify(
            {
                "status": "error",
                "error_type": "InvalidEntity",
                "message": error.message,
                "details": error.details,
            }
        ), 400

    def handle_business_rule_violation(self, error: BusinessRuleViolationException):
        """비즈니스 규칙 위반"""
        self.logger.warning(f"Business rule violation: {error.message}")

        return jsonify(
            {
                "status": "error",
                "error_type": "BusinessRuleViolation",
                "message": error.message,
                "details": error.details,
            }
        ), 422

    def handle_domain_exception(self, error: DomainException):
        """도메인 레이어 예외"""
        self.logger.error(f"Domain exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "DomainException",
                "message": error.message,
                "details": error.details,
            }
        ), map_exception_to_http_status(error)

    def handle_application_exception(self, error: ApplicationException):
        """애플리케이션 레이어 예외"""
        self.logger.error(f"Application exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "ApplicationException",
                "message": error.message,
                "details": error.details,
            }
        ), map_exception_to_http_status(error)

    def handle_database_exception(self, error: DatabaseException):
        """데이터베이스 예외"""
        self.logger.error(f"Database exception: {error.message}", exc_info=True)

        # 사용자에게는 일반적인 메시지만 표시
        return jsonify(
            {
                "status": "error",
                "error_type": "DatabaseError",
                "message": "데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "details": {"operation": error.details.get("operation")}
                if error.details
                else {},
            }
        ), 500

    def handle_external_api_exception(self, error: ExternalAPIException):
        """외부 API 호출 예외"""
        self.logger.error(f"External API exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "ExternalAPIError",
                "message": "외부 서비스 연동 중 오류가 발생했습니다.",
                "details": {"api": error.details.get("api_name")}
                if error.details
                else {},
            }
        ), 502

    def handle_infrastructure_exception(self, error: InfrastructureException):
        """인프라 레이어 예외"""
        self.logger.error(f"Infrastructure exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "InfrastructureError",
                "message": "시스템 오류가 발생했습니다.",
                "details": {},
            }
        ), 500

    def handle_validation_exception(self, error: ValidationException):
        """입력 검증 예외"""
        self.logger.warning(f"Validation exception: {error.message}")

        return jsonify(
            {
                "status": "error",
                "error_type": "ValidationError",
                "message": error.message,
                "details": error.details,
            }
        ), 400

    def handle_presentation_exception(self, error: PresentationException):
        """프레젠테이션 레이어 예외"""
        self.logger.error(f"Presentation exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "PresentationError",
                "message": error.message,
                "details": error.details,
            }
        ), map_exception_to_http_status(error)

    def handle_etf_monitor_exception(self, error: ETFMonitorException):
        """기본 애플리케이션 예외"""
        self.logger.error(f"ETF Monitor exception: {error.message}", exc_info=True)

        return jsonify(
            {
                "status": "error",
                "error_type": "ApplicationError",
                "message": error.message,
                "details": error.details,
            }
        ), 500

    def handle_generic_exception(self, error: Exception):
        """
        모든 예외의 최종 처리

        예상하지 못한 예외를 처리하고 로깅합니다.
        """
        self.logger.critical(
            f"Unhandled exception: {type(error).__name__} - {str(error)}", exc_info=True
        )

        # 개발 환경에서는 상세 정보 제공
        from config.settings import settings

        response_data = {
            "status": "error",
            "error_type": "UnexpectedError",
            "message": "예기치 않은 오류가 발생했습니다. 관리자에게 문의해주세요.",
        }

        # 디버그 모드에서는 상세 에러 정보 포함
        if settings.FLASK_DEBUG:
            response_data["details"] = {
                "type": type(error).__name__,
                "message": str(error),
            }

        return jsonify(response_data), 500


def create_error_response(
    message: str,
    error_type: str = "Error",
    details: dict = None,
    status_code: int = 400,
) -> tuple:
    """
    표준화된 에러 응답을 생성하는 헬퍼 함수

    Args:
        message: 에러 메시지
        error_type: 에러 타입
        details: 추가 상세 정보
        status_code: HTTP 상태 코드

    Returns:
        (response_dict, status_code) 튜플
    """
    response = {"status": "error", "error_type": error_type, "message": message}

    if details:
        response["details"] = details

    return jsonify(response), status_code


def create_success_response(
    data: dict = None, message: str = None, status_code: int = 200
) -> tuple:
    """
    표준화된 성공 응답을 생성하는 헬퍼 함수

    Args:
        data: 응답 데이터
        message: 성공 메시지
        status_code: HTTP 상태 코드

    Returns:
        (response_dict, status_code) 튜플
    """
    response = {"status": "success"}

    if message:
        response["message"] = message

    if data:
        response["data"] = data

    return jsonify(response), status_code
