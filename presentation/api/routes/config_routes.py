"""
Config Routes
설정 관리 관련 API 라우트를 정의합니다.
"""

from flask import Blueprint


def register_config_routes(api_bp: Blueprint):
    """
    설정 관리 관련 라우트를 등록합니다.

    Args:
        api_bp: API Blueprint
    """

    # 테마 관리

    @api_bp.route("/config/themes", methods=["GET"])
    def get_themes():
        """모든 테마 조회"""
        controller = api_bp.config_controller
        return controller.get_themes()

    @api_bp.route("/config/themes", methods=["POST"])
    def add_theme():
        """
        테마 추가

        Request Body:
            {
                "name": "테마명"
            }
        """
        controller = api_bp.config_controller
        return controller.add_theme()

    @api_bp.route("/config/themes", methods=["PUT"])
    def set_themes():
        """
        테마 일괄 설정 (기존 데이터 삭제 후 추가)

        Request Body:
            {
                "themes": ["테마1", "테마2", ...]
            }
        """
        controller = api_bp.config_controller
        return controller.set_themes()

    @api_bp.route("/config/themes/<theme_name>", methods=["DELETE"])
    def delete_theme(theme_name):
        """테마 삭제"""
        controller = api_bp.config_controller
        return controller.delete_theme(theme_name)

    # 제외 키워드 관리

    @api_bp.route("/config/exclusions", methods=["GET"])
    def get_exclusions():
        """모든 제외 키워드 조회"""
        controller = api_bp.config_controller
        return controller.get_exclusions()

    @api_bp.route("/config/exclusions", methods=["POST"])
    def add_exclusion():
        """
        제외 키워드 추가

        Request Body:
            {
                "keyword": "제외할키워드"
            }
        """
        controller = api_bp.config_controller
        return controller.add_exclusion()

    @api_bp.route("/config/exclusions", methods=["PUT"])
    def set_exclusions():
        """
        제외 키워드 일괄 설정 (기존 데이터 삭제 후 추가)

        Request Body:
            {
                "exclusions": ["키워드1", "키워드2", ...]
            }
        """
        controller = api_bp.config_controller
        return controller.set_exclusions()

    @api_bp.route("/config/exclusions/<keyword>", methods=["DELETE"])
    def delete_exclusion(keyword):
        """제외 키워드 삭제"""
        controller = api_bp.config_controller
        return controller.delete_exclusion(keyword)

    # 일괄 작업

    @api_bp.route("/config/reset", methods=["POST"])
    def reset_to_defaults():
        """설정을 기본값으로 리셋"""
        controller = api_bp.config_controller
        return controller.reset_to_defaults()

    @api_bp.route("/config/status", methods=["GET"])
    def get_config_status():
        """설정 상태 조회"""
        controller = api_bp.config_controller
        return controller.get_config_status()
