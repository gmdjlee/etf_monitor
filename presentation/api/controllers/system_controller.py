"""
System Controller
시스템 관리 관련 API 요청을 처리하는 컨트롤러입니다.
"""

from application.use_cases.initialize_system import InitializeSystemUseCase
from application.use_cases.update_etf_data import UpdateETFDataUseCase
from config.logging_config import LoggerMixin
from flask import jsonify


class SystemController(LoggerMixin):
    """
    시스템 컨트롤러

    시스템 초기화, 데이터 업데이트 등의 관리 API를 처리합니다.

    Args:
        initialize_system_use_case: 시스템 초기화 유스케이스
        update_etf_data_use_case: 데이터 업데이트 유스케이스
    """

    def __init__(
        self,
        initialize_system_use_case: InitializeSystemUseCase,
        update_etf_data_use_case: UpdateETFDataUseCase,
    ):
        self.initialize_system_uc = initialize_system_use_case
        self.update_etf_data_uc = update_etf_data_use_case

    def initialize(self):
        """시스템을 초기화합니다."""
        try:
            self.logger.info("POST /api/system/initialize")

            # 유스케이스 실행
            result = self.initialize_system_uc.execute()

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            data = result.value

            return jsonify(
                {
                    "status": "success",
                    "initialized": data["initialized"],
                    "stocks_collected": data["stocks_collected"],
                    "etfs_collected": data["etfs_collected"],
                    "days_collected": data["days_collected"],
                    "message": data["message"],
                }
            ), 200

        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": f"시스템 초기화 중 오류가 발생했습니다: {str(e)}",
                }
            ), 500

    def update_data(self):
        """데이터를 업데이트합니다."""
        try:
            self.logger.info("POST /api/system/update")

            # 유스케이스 실행
            result = self.update_etf_data_uc.execute()

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            data = result.value

            return jsonify(
                {
                    "status": "success",
                    "updated": data["updated"],
                    "etfs_updated": data["etfs_updated"],
                    "days_updated": data["days_updated"],
                    "start_date": data["start_date"],
                    "end_date": data["end_date"],
                    "message": data["message"],
                }
            ), 200

        except Exception as e:
            self.logger.error(f"Failed to update data: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": f"데이터 업데이트 중 오류가 발생했습니다: {str(e)}",
                }
            ), 500

    def get_system_status(self):
        """시스템 상태를 조회합니다."""
        try:
            self.logger.info("GET /api/system/status")

            # 데이터베이스 정보 조회
            from infrastructure.database.connection import db_connection
            from infrastructure.database.migrations import DatabaseMigrations

            migrations = DatabaseMigrations(db_connection)
            db_info = migrations.get_database_info()
            is_empty = migrations.is_database_empty()

            # 최신 날짜 조회
            # 실제 리포지토리 인스턴스가 필요하지만, 여기서는 간단히 처리

            status = {
                "database": {"is_empty": is_empty, "tables": db_info},
                "initialized": not is_empty,
            }

            return jsonify(status), 200

        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "시스템 상태 조회 중 오류가 발생했습니다.",
                }
            ), 500

    def health_check(self):
        """헬스 체크 엔드포인트"""
        try:
            self.logger.debug("GET /api/system/health")

            # 데이터베이스 연결 확인
            from infrastructure.database.connection import db_connection

            is_connected = db_connection.is_connected()

            if is_connected:
                return jsonify({"status": "healthy", "database": "connected"}), 200
            else:
                return jsonify({"status": "unhealthy", "database": "disconnected"}), 503

        except Exception as e:
            self.logger.error(f"Health check failed: {e}", exc_info=True)
            return jsonify({"status": "unhealthy", "error": str(e)}), 503
