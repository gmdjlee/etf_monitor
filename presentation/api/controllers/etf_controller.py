"""
ETF Controller (개선됨)
✅ 데코레이터로 중복 코드 제거
✅ 공통 유틸리티 사용
"""

from application.queries.weight_history_query import WeightHistoryQuery
from application.use_cases.export_data import ExportDataUseCase
from application.use_cases.get_holdings_comparison import GetHoldingsComparisonUseCase
from domain.repositories.etf_repository import ETFRepository
from flask import jsonify
from shared.utils.request_utils import get_int_param, parse_date_from_request

from presentation.api.decorators import handle_controller_errors, log_api_call


class ETFController:
    """
    ETF 컨트롤러

    ✅ 개선사항:
    - 데코레이터로 에러 처리 자동화
    - 공통 유틸리티로 중복 코드 제거
    - 로깅 자동화
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

    @log_api_call
    @handle_controller_errors("ETF 목록을 가져오는 데 실패했습니다.")
    def get_all_etfs(self):
        """모든 ETF 목록을 조회합니다."""
        etfs = self.etf_repo.find_all()
        return jsonify([etf.to_dict() for etf in etfs]), 200

    @log_api_call
    @handle_controller_errors("ETF 상세 정보를 가져오는 데 실패했습니다.")
    def get_etf_detail(self, ticker: str):
        """특정 ETF의 상세 정보를 조회합니다."""
        etf = self.etf_repo.find_by_ticker(ticker)
        if not etf:
            return jsonify(
                {"status": "error", "message": f"ETF를 찾을 수 없습니다: {ticker}"}
            ), 404

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

    @log_api_call
    @handle_controller_errors("보유 종목 비교 정보를 가져오는 데 실패했습니다.")
    def get_holdings_comparison(self, ticker: str):
        """ETF의 보유 종목 비교 정보를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        current_date = parse_date_from_request("current_date")
        previous_date = parse_date_from_request("previous_date")

        result = self.get_holdings_comparison_uc.execute(
            etf_ticker=ticker,
            current_date=current_date,
            previous_date=previous_date,
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value.to_dict()), 200

    @log_api_call
    @handle_controller_errors("비중 추이를 가져오는 데 실패했습니다.")
    def get_stock_weight_history(self, etf_ticker: str, stock_ticker: str):
        """특정 종목의 비중 추이를 조회합니다."""
        result_dto = self.weight_history_query.execute(etf_ticker, stock_ticker)
        return jsonify(result_dto.to_dict()), 200

    @log_api_call
    @handle_controller_errors("상위 보유 종목을 가져오는 데 실패했습니다.")
    def get_top_holdings(self, ticker: str):
        """상위 보유 종목을 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")
        top_n = get_int_param("top_n", 10)

        result = self.get_holdings_comparison_uc.get_top_holdings(
            etf_ticker=ticker, date=date, top_n=top_n
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value), 200

    @log_api_call
    @handle_controller_errors("요약 정보를 가져오는 데 실패했습니다.")
    def get_holdings_summary(self, ticker: str):
        """보유 종목 요약 정보를 조회합니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")

        result = self.get_holdings_comparison_uc.get_holdings_summary(
            etf_ticker=ticker, date=date
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        return jsonify(result.value), 200

    @log_api_call
    @handle_controller_errors("CSV 내보내기에 실패했습니다.")
    def export_csv(self, ticker: str):
        """보유 종목을 CSV로 내보냅니다."""
        # ✅ 개선: 공통 유틸리티 사용
        date = parse_date_from_request("date")

        result = self.export_data_uc.export_holdings_to_csv(
            etf_ticker=ticker, date=date
        )

        if result.is_failure():
            return jsonify({"status": "error", "message": result.error}), 400

        from flask import send_file

        return send_file(
            result.value, as_attachment=True, download_name=f"{ticker}_holdings.csv"
        )

    @log_api_call
    @handle_controller_errors("비교 CSV 내보내기에 실패했습니다.")
    def export_comparison_csv(self, ticker: str):
        """보유 종목 비교 결과를 CSV로 내보냅니다."""
        # ✅ 개선: 공통 유틸리티 사용
        current_date = parse_date_from_request("current_date")
        previous_date = parse_date_from_request("previous_date")

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
