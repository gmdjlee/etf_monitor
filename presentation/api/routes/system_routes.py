"""
System Routes
시스템 관리 관련 API 라우트를 정의합니다.
"""

from flask import Blueprint


def register_system_routes(api_bp: Blueprint):
    """
    시스템 관리 관련 라우트를 등록합니다.

    Args:
        api_bp: API Blueprint
    """

    @api_bp.route("/system/initialize", methods=["POST"])
    def initialize():
        """
        시스템 초기화

        데이터베이스가 비어있을 경우 기본 설정과 초기 데이터를 수집합니다.
        """
        controller = api_bp.system_controller
        return controller.initialize()

    @api_bp.route("/system/update", methods=["POST"])
    def update_data():
        """
        데이터 업데이트

        최신 날짜부터 현재까지의 데이터를 수집하여 업데이트합니다.
        """
        controller = api_bp.system_controller
        return controller.update_data()

    @api_bp.route("/system/status", methods=["GET"])
    def get_system_status():
        """
        시스템 상태 조회

        데이터베이스 상태, 초기화 여부 등의 정보를 반환합니다.
        """
        controller = api_bp.system_controller
        return controller.get_system_status()

    @api_bp.route("/system/health", methods=["GET"])
    def health_check():
        """
        헬스 체크

        시스템이 정상적으로 작동하는지 확인합니다.
        """
        controller = api_bp.system_controller
        return controller.health_check()
