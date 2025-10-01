"""
Statistics Controller (개선됨)
✅ 데코레이터로 중복 코드 제거
✅ 공통 유틸리티 사용
"""

from application.use_cases.get_statistics import GetStatisticsUseCase
from flask import jsonify
from shared.utils.request_utils import get_int_param, parse_date_from_request

from presentation.api.decorators import handle_controller_errors, log_api_call


class StatisticsController:
    """
    통계 컨트롤러

    ✅ 개선사항:
    - 데코레이터로 에러 처리 자동화
    - 공통 유틸리티로 중복 코드 제거
    """

    def __init__(self, get_statistics_use_case: GetStatisticsUseCase):
        self.get_statistics_uc = get_statistics_use_case

    @log_api_call
    @handle_controller_errors("중복 종목 통계를 가져오는 데 실패했습니다.")
    def get_duplicate_stocks(self):
        """중복 종목 통계를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")
        min_count = get_int_param("min_count", 2)
        limit = get_int_param("limit", 100)

        result = self.get_statistics_uc.get_duplicate_stocks(
            date=date, min_count=min_count, limit=limit
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value.to_dict()), 200

    @log_api_call
    @handle_controller_errors("평가금액 순위를 가져오는 데 실패했습니다.")
    def get_amount_ranking(self):
        """평가금액 순위를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")
        top_n = get_int_param("top_n", 100)

        result = self.get_statistics_uc.get_amount_ranking(date=date, top_n=top_n)

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value.to_dict()), 200

    @log_api_call
    @handle_controller_errors("테마 통계를 가져오는 데 실패했습니다.")
    def get_theme_statistics(self, theme: str):
        """특정 테마의 통계를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")
        limit = get_int_param("limit", 100)

        result = self.get_statistics_uc.get_theme_statistics(
            theme=theme, date=date, limit=limit
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value.to_dict()), 200

    @log_api_call
    @handle_controller_errors("통계 요약을 가져오는 데 실패했습니다.")
    def get_statistics_summary(self):
        """전체 통계 요약을 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")

        result = self.get_statistics_uc.get_statistics_summary(date=date)

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value), 200

    @log_api_call
    @handle_controller_errors("비중 분포를 가져오는 데 실패했습니다.")
    def get_weight_distribution(self):
        """비중 분포를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")

        result = self.get_statistics_uc.get_weight_distribution(date=date)

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value), 200
