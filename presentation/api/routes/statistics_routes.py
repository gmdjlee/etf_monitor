"""
Statistics Routes
통계 관련 API 라우트를 정의합니다.
"""

from flask import Blueprint


def register_statistics_routes(api_bp: Blueprint):
    """
    통계 관련 라우트를 등록합니다.

    Args:
        api_bp: API Blueprint
    """

    @api_bp.route("/stats/duplicate-stocks", methods=["GET"])
    def get_duplicate_stocks():
        """
        중복 종목 통계 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
            - min_count: 최소 중복 횟수 (선택, 기본값: 2)
            - limit: 최대 반환 개수 (선택, 기본값: 100)
        """
        controller = api_bp.statistics_controller
        return controller.get_duplicate_stocks()

    @api_bp.route("/stats/amount-ranking", methods=["GET"])
    def get_amount_ranking():
        """
        평가금액 순위 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
            - top_n: 상위 N개 (선택, 기본값: 100)
        """
        controller = api_bp.statistics_controller
        return controller.get_amount_ranking()

    @api_bp.route("/stats/theme/<theme>", methods=["GET"])
    def get_theme_statistics(theme):
        """
        특정 테마 통계 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
            - limit: 최대 반환 개수 (선택, 기본값: 100)
        """
        controller = api_bp.statistics_controller
        return controller.get_theme_statistics(theme)

    @api_bp.route("/stats/summary", methods=["GET"])
    def get_statistics_summary():
        """
        전체 통계 요약 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
        """
        controller = api_bp.statistics_controller
        return controller.get_statistics_summary()

    @api_bp.route("/stats/weight-distribution", methods=["GET"])
    def get_weight_distribution():
        """
        비중 분포 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
        """
        controller = api_bp.statistics_controller
        return controller.get_weight_distribution()
