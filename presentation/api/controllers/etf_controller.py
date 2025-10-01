"""
ETF Controller
ETF 관련 API 요청을 처리하는 컨트롤러입니다.
"""

from datetime import datetime
from typing import Optional

from application.queries.weight_history_query import WeightHistoryQuery
from application.use_cases.export_data import ExportDataUseCase
from application.use_cases.get_holdings_comparison import GetHoldingsComparisonUseCase
from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from flask import jsonify, request
from shared.utils.date_utils import parse_flexible_date


class ETFController(LoggerMixin):
    """
    ETF 컨트롤러

    ETF 조회, 보유 종목 비교, 데이터 내보내기 등의 API를 처리합니다.

    Args:
        etf_repository: ETF 리포지토리
        get_holdings_comparison_use_case: 보유 종목 비교 유스케이스
        export_data_use_case: 데이터 내보내기 유스케이스
        weight_history_query: 비중 추이 쿼리
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        get_holdings_comparison_use_case: GetHoldingsComparisonUseCase,
        export_data_use_case: ExportDataUseCase,
        weight_history_query: WeightHistoryQuery,
    ):
        self.etf_repo = etf_repository
        self.get_holdings_comparison_uc = get_holdings_comparison_use_case
        self.export_data_uc = export_data_use_case
        self.weight_history_query = weight_history_query

    def get_all_etfs(self):
        """모든 ETF 목록을 조회합니다."""
        try:
            self.logger.info("GET /api/etfs")

            etfs = self.etf_repo.find_all()

            return jsonify([etf.to_dict() for etf in etfs]), 200

        except Exception as e:
            self.logger.error(f"Failed to get ETFs: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "ETF 목록을 가져오는 데 실패했습니다."}
            ), 500

    def get_etf_detail(self, ticker: str):
        """특정 ETF의 상세 정보를 조회합니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}")

            etf = self.etf_repo.find_by_ticker(ticker)

            if not etf:
                return jsonify(
                    {"status": "error", "message": f"ETF를 찾을 수 없습니다: {ticker}"}
                ), 404

            # 사용 가능한 날짜 조회
            available_dates = self.etf_repo.get_available_dates(ticker)

            result = {
                "ticker": etf.ticker,
                "name": etf.name,
                "is_active": etf.is_active(),
                "available_dates": [d.strftime("%Y-%m-%d") for d in available_dates],
                "latest_date": available_dates[0].strftime("%Y-%m-%d")
                if available_dates
                else None,
            }

            return jsonify(result), 200

        except Exception as e:
            self.logger.error(f"Failed to get ETF detail: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "ETF 상세 정보를 가져오는 데 실패했습니다.",
                }
            ), 500

    def get_holdings_comparison(self, ticker: str):
        """ETF의 보유 종목 비교 정보를 조회합니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}/comparison")

            # 쿼리 파라미터에서 날짜 추출
            current_date = self._parse_date_param("current_date")
            previous_date = self._parse_date_param("previous_date")

            # 유스케이스 실행
            result = self.get_holdings_comparison_uc.execute(
                etf_ticker=ticker,
                current_date=current_date,
                previous_date=previous_date,
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value.to_dict()), 200

        except Exception as e:
            self.logger.error(f"Failed to get holdings comparison: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "보유 종목 비교 정보를 가져오는 데 실패했습니다.",
                }
            ), 500

    def get_stock_weight_history(self, etf_ticker: str, stock_ticker: str):
        """특정 종목의 비중 추이를 조회합니다."""
        try:
            self.logger.info(f"GET /api/etf/{etf_ticker}/stock/{stock_ticker}/history")

            # 쿼리 실행
            result_dto = self.weight_history_query.execute(etf_ticker, stock_ticker)

            return jsonify(result_dto.to_dict()), 200

        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 404

        except Exception as e:
            self.logger.error(f"Failed to get weight history: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "비중 추이를 가져오는 데 실패했습니다."}
            ), 500

    def get_top_holdings(self, ticker: str):
        """상위 보유 종목을 조회합니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}/top-holdings")

            # 쿼리 파라미터
            date = self._parse_date_param("date")
            top_n = request.args.get("top_n", 10, type=int)

            # 유스케이스 실행
            result = self.get_holdings_comparison_uc.get_top_holdings(
                etf_ticker=ticker, date=date, top_n=top_n
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value), 200

        except Exception as e:
            self.logger.error(f"Failed to get top holdings: {e}", exc_info=True)
            return jsonify(
                {
                    "status": "error",
                    "message": "상위 보유 종목을 가져오는 데 실패했습니다.",
                }
            ), 500

    def get_holdings_summary(self, ticker: str):
        """보유 종목 요약 정보를 조회합니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}/summary")

            # 쿼리 파라미터
            date = self._parse_date_param("date")

            # 유스케이스 실행
            result = self.get_holdings_comparison_uc.get_holdings_summary(
                etf_ticker=ticker, date=date
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            return jsonify(result.value), 200

        except Exception as e:
            self.logger.error(f"Failed to get holdings summary: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "요약 정보를 가져오는 데 실패했습니다."}
            ), 500

    def export_csv(self, ticker: str):
        """보유 종목을 CSV로 내보냅니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}/export")

            # 쿼리 파라미터
            date = self._parse_date_param("date")

            # 유스케이스 실행
            result = self.export_data_uc.export_holdings_to_csv(
                etf_ticker=ticker, date=date
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            from flask import send_file

            return send_file(
                result.value, as_attachment=True, download_name=f"{ticker}_holdings.csv"
            )

        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "CSV 내보내기에 실패했습니다."}
            ), 500

    def export_comparison_csv(self, ticker: str):
        """보유 종목 비교 결과를 CSV로 내보냅니다."""
        try:
            self.logger.info(f"GET /api/etf/{ticker}/export-comparison")

            # 쿼리 파라미터
            current_date = self._parse_date_param("current_date")
            previous_date = self._parse_date_param("previous_date")

            # 유스케이스 실행
            result = self.export_data_uc.export_comparison_to_csv(
                etf_ticker=ticker,
                current_date=current_date,
                previous_date=previous_date,
            )

            if result.is_failure():
                return jsonify({"status": "error", "message": result.error}), 400

            from flask import send_file

            return send_file(
                result.value,
                as_attachment=True,
                download_name=f"{ticker}_comparison.csv",
            )

        except Exception as e:
            self.logger.error(f"Failed to export comparison CSV: {e}", exc_info=True)
            return jsonify(
                {"status": "error", "message": "비교 CSV 내보내기에 실패했습니다."}
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
