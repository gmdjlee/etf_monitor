"""
System Controller (개선됨)
✅ 데코레이터로 중복 코드 제거
"""

from application.use_cases.initialize_system import InitializeSystemUseCase
from application.use_cases.update_etf_data import UpdateETFDataUseCase
from flask import jsonify

from presentation.api.decorators import handle_controller_errors, log_api_call


class SystemController:
    """
    시스템 컨트롤러

    ✅ 개선사항:
    - 데코레이터로 에러 처리 자동화
    """

    def __init__(
        self,
        initialize_system_use_case: InitializeSystemUseCase,
        update_etf_data_use_case: UpdateETFDataUseCase,
    ):
        self.initialize_system_uc = initialize_system_use_case
        self.update_etf_data_uc = update_etf_data_use_case

    @log_api_call
    @handle_controller_errors("시스템 초기화 중 오류가 발생했습니다.")
    def initialize(self):
        """시스템을 초기화합니다."""
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

    @log_api_call
    @handle_controller_errors("데이터 업데이트 중 오류가 발생했습니다.")
    def update_data(self):
        """데이터를 업데이트합니다."""
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

    @log_api_call
    @handle_controller_errors("시스템 상태 조회 중 오류가 발생했습니다.")
    def get_system_status(self):
        """시스템 상태를 조회합니다."""
        from infrastructure.database.connection import db_connection
        from infrastructure.database.migrations import DatabaseMigrations

        migrations = DatabaseMigrations(db_connection)
        db_info = migrations.get_database_info()
        is_empty = migrations.is_database_empty()

        status = {
            "database": {"is_empty": is_empty, "tables": db_info},
            "initialized": not is_empty,
        }

        return jsonify(status), 200

    @log_api_call
    def health_check(self):
        """헬스 체크 엔드포인트"""
        from infrastructure.database.connection import db_connection

        is_connected = db_connection.is_connected()

        if is_connected:
            return jsonify({"status": "healthy", "database": "connected"}), 200
        else:
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
