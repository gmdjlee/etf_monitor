"""
ETF Routes
ETF 관련 API 라우트를 정의합니다.
"""

from flask import Blueprint


def register_etf_routes(api_bp: Blueprint):
    """
    ETF 관련 라우트를 등록합니다.

    Args:
        api_bp: API Blueprint
    """

    # 의존성 주입 (나중에 app.py에서 설정)
    # 여기서는 라우트만 정의

    @api_bp.route("/etfs", methods=["GET"])
    def get_all_etfs():
        """모든 ETF 목록 조회"""
        controller = api_bp.etf_controller
        return controller.get_all_etfs()

    @api_bp.route("/etf/<ticker>", methods=["GET"])
    def get_etf_detail(ticker):
        """특정 ETF 상세 정보 조회"""
        controller = api_bp.etf_controller
        return controller.get_etf_detail(ticker)

    @api_bp.route("/etf/<ticker>/comparison", methods=["GET"])
    def get_holdings_comparison(ticker):
        """
        ETF 보유 종목 비교 조회

        Query Parameters:
            - current_date: 현재 날짜 (선택, 기본값: 최신)
            - previous_date: 이전 날짜 (선택, 기본값: current_date의 이전)
        """
        controller = api_bp.etf_controller
        return controller.get_holdings_comparison(ticker)

    @api_bp.route("/etf/<etf_ticker>/stock/<stock_ticker>/history", methods=["GET"])
    def get_stock_weight_history(etf_ticker, stock_ticker):
        """특정 종목의 비중 추이 조회"""
        controller = api_bp.etf_controller
        return controller.get_stock_weight_history(etf_ticker, stock_ticker)

    @api_bp.route("/etf/<ticker>/top-holdings", methods=["GET"])
    def get_top_holdings(ticker):
        """
        상위 보유 종목 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
            - top_n: 상위 N개 (선택, 기본값: 10)
        """
        controller = api_bp.etf_controller
        return controller.get_top_holdings(ticker)

    @api_bp.route("/etf/<ticker>/summary", methods=["GET"])
    def get_holdings_summary(ticker):
        """
        보유 종목 요약 정보 조회

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
        """
        controller = api_bp.etf_controller
        return controller.get_holdings_summary(ticker)

    @api_bp.route("/etf/<ticker>/export", methods=["GET"])
    def export_csv(ticker):
        """
        보유 종목 CSV 내보내기

        Query Parameters:
            - date: 기준일 (선택, 기본값: 최신)
        """
        controller = api_bp.etf_controller
        return controller.export_csv(ticker)

    @api_bp.route("/etf/<ticker>/export-comparison", methods=["GET"])
    def export_comparison_csv(ticker):
        """
        보유 종목 비교 CSV 내보내기

        Query Parameters:
            - current_date: 현재 날짜 (선택)
            - previous_date: 이전 날짜 (선택)
        """
        controller = api_bp.etf_controller
        return controller.export_comparison_csv(ticker)
