"""
ETF Monitoring Application (Medium Priority 적용)
애플리케이션 진입점입니다.
✅ 캐싱, 인덱스, 전역 예외 핸들러 적용
"""

from application.queries.holdings_comparison_query import HoldingsComparisonQuery
from application.queries.stock_statistics_query import StockStatisticsQuery
from application.queries.weight_history_query import WeightHistoryQuery
from application.use_cases.export_data import ExportDataUseCase
from application.use_cases.get_holdings_comparison import GetHoldingsComparisonUseCase
from application.use_cases.get_statistics import GetStatisticsUseCase
from application.use_cases.initialize_system import InitializeSystemUseCase
from application.use_cases.update_etf_data import UpdateETFDataUseCase
from config.logging_config import initialize_logging
from config.settings import settings
from domain.services.etf_filter_service import ETFFilterService
from domain.services.holdings_analyzer import HoldingsAnalyzer
from domain.services.statistics_calculator import StatisticsCalculator
from flask import Flask, render_template
from infrastructure.adapters.pykrx_adapter import PyKRXAdapter
from infrastructure.database.connection import db_connection
from infrastructure.database.migrations import DatabaseMigrations
from infrastructure.database.repositories.sqlite_config_repository import (
    SQLiteConfigRepository,
)
from infrastructure.database.repositories.sqlite_etf_repository import (
    SQLiteETFRepository,
)
from infrastructure.database.repositories.sqlite_stock_repository import (
    SQLiteStockRepository,
)
from presentation.api.controllers.config_controller import ConfigController
from presentation.api.controllers.etf_controller import ETFController
from presentation.api.controllers.statistics_controller import StatisticsController
from presentation.api.controllers.system_controller import SystemController

# ✅ NEW: 전역 예외 핸들러 import
from presentation.api.error_handlers import ErrorHandlers
from presentation.api.routes import register_all_routes


def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    # 로깅 초기화
    initialize_logging()

    # Flask 앱 생성
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = settings.JSON_AS_ASCII

    # ✅ NEW: 전역 예외 핸들러 등록 (먼저 등록)
    ErrorHandlers.register_all_handlers(app)

    # 데이터베이스 초기화
    migrations = DatabaseMigrations(db_connection)
    migrations.run_all_migrations()  # ✅ 최적화 인덱스 포함

    # ==========================================
    # 의존성 주입 - Infrastructure Layer
    # ==========================================
    stock_repo = SQLiteStockRepository(db_connection)
    etf_repo = SQLiteETFRepository(db_connection)  # ✅ 캐싱 적용됨
    config_repo = SQLiteConfigRepository(db_connection)
    market_adapter = PyKRXAdapter()

    # ==========================================
    # 의존성 주입 - Domain Layer
    # ==========================================
    filter_service = ETFFilterService()
    holdings_analyzer = HoldingsAnalyzer()
    statistics_calculator = StatisticsCalculator()

    # ==========================================
    # 의존성 주입 - Application Layer (Queries)
    # ==========================================
    holdings_comparison_query = HoldingsComparisonQuery(
        etf_repo, stock_repo, holdings_analyzer
    )
    stock_statistics_query = StockStatisticsQuery(etf_repo, statistics_calculator)
    weight_history_query = WeightHistoryQuery(etf_repo)

    # ==========================================
    # 의존성 주입 - Application Layer (Use Cases)
    # ==========================================
    initialize_system_uc = InitializeSystemUseCase(
        etf_repo, stock_repo, config_repo, market_adapter, filter_service
    )
    update_etf_data_uc = UpdateETFDataUseCase(
        etf_repo, config_repo, market_adapter, filter_service
    )

    get_holdings_comparison_uc = GetHoldingsComparisonUseCase(
        etf_repo,
        holdings_comparison_query,
    )

    get_statistics_uc = GetStatisticsUseCase(
        etf_repo,
        statistics_calculator,
        stock_statistics_query,
    )

    export_data_uc = ExportDataUseCase(etf_repo, holdings_comparison_query)

    # ==========================================
    # 의존성 주입 - Presentation Layer (Controllers)
    # ==========================================
    etf_controller = ETFController(
        etf_repo, get_holdings_comparison_uc, export_data_uc, weight_history_query
    )
    statistics_controller = StatisticsController(get_statistics_uc)
    system_controller = SystemController(initialize_system_uc, update_etf_data_uc)
    config_controller = ConfigController(config_repo)

    # ==========================================
    # API 라우트 등록
    # ==========================================
    def setup_controllers(api_bp):
        """Blueprint에 컨트롤러 주입"""
        api_bp.etf_controller = etf_controller
        api_bp.statistics_controller = statistics_controller
        api_bp.system_controller = system_controller
        api_bp.config_controller = config_controller

    # 라우트 등록
    register_all_routes(app)

    # Blueprint에 컨트롤러 주입
    for blueprint in app.blueprints.values():
        if blueprint.name == "api":
            setup_controllers(blueprint)

    # ==========================================
    # HTML 라우트
    # ==========================================
    @app.route("/")
    def index():
        """메인 페이지"""
        return render_template("index.html")

    @app.route("/settings")
    def settings_page():
        """설정 페이지"""
        return render_template("settings.html")

    # ✅ NEW: 캐시 관리 엔드포인트 (디버그용)
    if settings.FLASK_DEBUG:
        from infrastructure.cache import cache_manager

        @app.route("/api/cache/stats")
        def cache_stats():
            """캐시 통계 조회"""
            return cache_manager.get_stats()

        @app.route("/api/cache/clear", methods=["POST"])
        def clear_cache():
            """캐시 전체 삭제"""
            cache_manager.clear()
            return {"status": "success", "message": "Cache cleared"}

    # ==========================================
    # 에러 핸들러 (기본 HTTP 에러들)
    # Note: 커스텀 예외는 ErrorHandlers에서 처리됨
    # ==========================================
    @app.errorhandler(404)
    def not_found(error):
        """404 에러 (ErrorHandlers에 의해 처리되지만 명시적 정의)"""
        return {"status": "error", "message": "Not Found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 에러 (ErrorHandlers에 의해 처리되지만 명시적 정의)"""
        return {"status": "error", "message": "Internal Server Error"}, 500

    return app


def main():
    """애플리케이션을 실행합니다."""
    app = create_app()

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database: {settings.DATABASE_PATH}")
    print(f"Cache: {'Enabled' if settings.CACHE_ENABLED else 'Disabled'}")
    print(f"Running on http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")

    app.run(
        host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=settings.FLASK_DEBUG
    )


if __name__ == "__main__":
    main()
