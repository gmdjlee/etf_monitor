"""
Statistics Controller
통계 관련 API 요청을 처리하는 컨트롤러입니다.
"""

from datetime import datetime
from typing import Optional

from application.use_cases.get_statistics import GetStatisticsUseCase
from config.logging_config import LoggerMixin
from flask import jsonify, request
from shared.utils.date_utils import parse_flexible_date


class StatisticsController(LoggerMixin):
    """
    통계 컨트롤러

    중복 종목, 평가금액 순위, 테마별 통계 등의 API를 처리합니다.

    Args:
        get_statistics_use_case: 통계 조회 유스케이스
    """

    def __init__(self, get_statistics_use_case: GetStatisticsUseCase):
        self.get_statistics_uc = get_statistics_use_case

    def get_duplicate_stocks(self):
        """중복 종목 통계를 조회합니다."""
        try:
            self.logger.info("GET /api/stats/duplicate-stocks")

            # 쿼리 파라미터
            date = self._parse_date_param("date")
            min_count = request.args.get("min_count", 2, type=int)
            limit = request.args.get("limit", 100, type=int)

            # 유스케이스 실행
            result = self.get_statistics_uc.get_duplicate_stocks(
                date=date, min_count=min_count, limit=limit
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value.to_dict()), 200

        except Exception as e:
            self.logger.error(f"Failed to get duplicate stocks: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "중복 종목 통계를 가져오는 데 실패했습니다.",
                }
            ), 500

    def get_amount_ranking(self):
        """평가금액 순위를 조회합니다."""
        try:
            self.logger.info("GET /api/stats/amount-ranking")

            # 쿼리 파라미터
            date = self._parse_date_param("date")
            top_n = request.args.get("top_n", 100, type=int)

            # 유스케이스 실행
            result = self.get_statistics_uc.get_amount_ranking(date=date, top_n=top_n)

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value.to_dict()), 200

        except Exception as e:
            self.logger.error(f"Failed to get amount ranking: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "평가금액 순위를 가져오는 데 실패했습니다.",
                }
            ), 500

    def get_theme_statistics(self, theme: str):
        """특정 테마의 통계를 조회합니다."""
        try:
            self.logger.info(f"GET /api/stats/theme/{theme}")

            # 쿼리 파라미터
            date = self._parse_date_param("date")
            limit = request.args.get("limit", 100, type=int)

            # 유스케이스 실행
            result = self.get_statistics_uc.get_theme_statistics(
                theme=theme, date=date, limit=limit
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value.to_dict()), 200

        except Exception as e:
            self.logger.error(f"Failed to get theme statistics: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "테마 통계를 가져오는 데 실패했습니다."}
            ), 500

    def get_statistics_summary(self):
        """전체 통계 요약을 조회합니다."""
        try:
            self.logger.info("GET /api/stats/summary")

            # 쿼리 파라미터
            date = self._parse_date_param("date")

            # 유스케이스 실행
            result = self.get_statistics_uc.get_statistics_summary(date=date)

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value), 200

        except Exception as e:
            self.logger.error(f"Failed to get statistics summary: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "통계 요약을 가져오는 데 실패했습니다."}
            ), 500

    def get_weight_distribution(self):
        """비중 분포를 조회합니다."""
        try:
            self.logger.info("GET /api/stats/weight-distribution")

            # 쿼리 파라미터
            date = self._parse_date_param("date")

            # 유스케이스 실행
            result = self.get_statistics_uc.get_weight_distribution(date=date)

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value), 200

        except Exception as e:
            self.logger.error(f"Failed to get weight distribution: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "비중 분포를 가져오는 데 실패했습니다."}
            ), 500

    def _parse_date_param(self, param_name: str) -> Optional[datetime]:
        """쿼리 파라미터에서 날짜를 파싱합니다."""
        date_str = request.args.get(param_name)

        if not date_str:
            return None

        date = parse_flexible_date(date_str)
        if not date:
            raise ValueError(f"Invalid date format: {date_str}")

        return date
