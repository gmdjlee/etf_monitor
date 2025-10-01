"""
API Routes
모든 API 라우트를 등록합니다.
"""

from flask import Blueprint

from presentation.api.routes.config_routes import register_config_routes
from presentation.api.routes.etf_routes import register_etf_routes
from presentation.api.routes.statistics_routes import register_statistics_routes
from presentation.api.routes.system_routes import register_system_routes


def register_all_routes(app):
    """
    모든 API 라우트를 Flask 앱에 등록합니다.

    Args:
        app: Flask 애플리케이션 인스턴스
    """
    # API Blueprint 생성
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    # 각 라우트 등록
    register_etf_routes(api_bp)
    register_statistics_routes(api_bp)
    register_system_routes(api_bp)
    register_config_routes(api_bp)

    # Flask 앱에 Blueprint 등록
    app.register_blueprint(api_bp)
