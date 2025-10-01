"""
Config Controller (개선됨)
✅ 데코레이터로 중복 코드 제거
"""

from domain.repositories.config_repository import ConfigRepository
from flask import jsonify, request

from presentation.api.decorators import handle_controller_errors, log_api_call


class ConfigController:
    """
    설정 컨트롤러

    ✅ 개선사항:
    - 데코레이터로 에러 처리 자동화
    """

    def __init__(self, config_repository: ConfigRepository):
        self.config_repo = config_repository

    # 테마 관리

    @log_api_call
    @handle_controller_errors("테마 목록을 가져오는 데 실패했습니다.")
    def get_themes(self):
        """모든 테마를 조회합니다."""
        themes = self.config_repo.get_all_themes()
        return jsonify({"themes": themes, "count": len(themes)}), 200

    @log_api_call
    @handle_controller_errors("테마 추가 중 오류가 발생했습니다.")
    def add_theme(self):
        """테마를 추가합니다."""
        data = request.get_json()

        if not data or "name" not in data:
            return jsonify(
                {"status": "error", "message": "테마 이름이 필요합니다."}
            ), 400

        theme_name = data["name"].strip()

        if not theme_name:
            return jsonify(
                {"status": "error", "message": "테마 이름은 비어있을 수 없습니다."}
            ), 400

        if self.config_repo.theme_exists(theme_name):
            return jsonify(
                {
                    "status": "error",
                    "message": f"이미 존재하는 테마입니다: {theme_name}",
                }
            ), 409

        self.config_repo.add_theme(theme_name)
        return jsonify(
            {"status": "success", "message": f"테마가 추가되었습니다: {theme_name}"}
        ), 201

    @log_api_call
    @handle_controller_errors("테마 삭제 중 오류가 발생했습니다.")
    def delete_theme(self, theme_name: str):
        """테마를 삭제합니다."""
        if not self.config_repo.theme_exists(theme_name):
            return jsonify(
                {"status": "error", "message": f"테마를 찾을 수 없습니다: {theme_name}"}
            ), 404

        self.config_repo.remove_theme(theme_name)
        return jsonify(
            {"status": "success", "message": f"테마가 삭제되었습니다: {theme_name}"}
        ), 200

    # 제외 키워드 관리

    @log_api_call
    @handle_controller_errors("제외 키워드 목록을 가져오는 데 실패했습니다.")
    def get_exclusions(self):
        """모든 제외 키워드를 조회합니다."""
        exclusions = self.config_repo.get_all_exclusions()
        return jsonify({"exclusions": exclusions, "count": len(exclusions)}), 200

    @log_api_call
    @handle_controller_errors("제외 키워드 추가 중 오류가 발생했습니다.")
    def add_exclusion(self):
        """제외 키워드를 추가합니다."""
        data = request.get_json()

        if not data or "keyword" not in data:
            return jsonify(
                {"status": "error", "message": "제외 키워드가 필요합니다."}
            ), 400

        keyword = data["keyword"].strip()

        if not keyword:
            return jsonify(
                {"status": "error", "message": "제외 키워드는 비어있을 수 없습니다."}
            ), 400

        if self.config_repo.exclusion_exists(keyword):
            return jsonify(
                {
                    "status": "error",
                    "message": f"이미 존재하는 제외 키워드입니다: {keyword}",
                }
            ), 409

        self.config_repo.add_exclusion(keyword)
        return jsonify(
            {"status": "success", "message": f"제외 키워드가 추가되었습니다: {keyword}"}
        ), 201

    @log_api_call
    @handle_controller_errors("제외 키워드 삭제 중 오류가 발생했습니다.")
    def delete_exclusion(self, keyword: str):
        """제외 키워드를 삭제합니다."""
        if not self.config_repo.exclusion_exists(keyword):
            return jsonify(
                {
                    "status": "error",
                    "message": f"제외 키워드를 찾을 수 없습니다: {keyword}",
                }
            ), 404

        self.config_repo.remove_exclusion(keyword)
        return jsonify(
            {"status": "success", "message": f"제외 키워드가 삭제되었습니다: {keyword}"}
        ), 200

    # 일괄 작업

    @log_api_call
    @handle_controller_errors("테마 일괄 설정 중 오류가 발생했습니다.")
    def set_themes(self):
        """테마를 일괄 설정합니다."""
        data = request.get_json()

        if not data or "themes" not in data:
            return jsonify(
                {"status": "error", "message": "테마 목록이 필요합니다."}
            ), 400

        themes = [t.strip() for t in data["themes"] if t and t.strip()]
        self.config_repo.set_themes(themes)

        return jsonify(
            {
                "status": "success",
                "message": f"{len(themes)}개의 테마가 설정되었습니다.",
            }
        ), 200

    @log_api_call
    @handle_controller_errors("제외 키워드 일괄 설정 중 오류가 발생했습니다.")
    def set_exclusions(self):
        """제외 키워드를 일괄 설정합니다."""
        data = request.get_json()

        if not data or "exclusions" not in data:
            return jsonify(
                {"status": "error", "message": "제외 키워드 목록이 필요합니다."}
            ), 400

        exclusions = [e.strip() for e in data["exclusions"] if e and e.strip()]
        self.config_repo.set_exclusions(exclusions)

        return jsonify(
            {
                "status": "success",
                "message": f"{len(exclusions)}개의 제외 키워드가 설정되었습니다.",
            }
        ), 200

    @log_api_call
    @handle_controller_errors("설정 리셋 중 오류가 발생했습니다.")
    def reset_to_defaults(self):
        """설정을 기본값으로 리셋합니다."""
        self.config_repo.reset_to_defaults()
        return jsonify(
            {"status": "success", "message": "설정이 기본값으로 리셋되었습니다."}
        ), 200

    @log_api_call
    @handle_controller_errors("설정 상태 조회 중 오류가 발생했습니다.")
    def get_config_status(self):
        """설정 상태를 조회합니다."""
        theme_count = self.config_repo.count_themes()
        exclusion_count = self.config_repo.count_exclusions()
        is_empty = self.config_repo.is_empty()
        has_default = self.config_repo.has_default_config()

        return jsonify(
            {
                "theme_count": theme_count,
                "exclusion_count": exclusion_count,
                "is_empty": is_empty,
                "has_default_config": has_default,
            }
        ), 200
