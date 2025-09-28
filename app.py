import logging
import os
from datetime import datetime

from database.database_manager import DatabaseManager
from domain.repositories import ConfigRepository, EtfRepository, StockRepository
from domain.services import EtfDataService
from flask import Flask, jsonify, render_template, request, send_file

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 애플리케이션 설정
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 데이터베이스 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "etf_monitor.db")

# 서비스 및 리포지토리 초기화 (의존성 주입)
db_manager = DatabaseManager(DB_PATH)
etf_repo = EtfRepository(db_manager)
stock_repo = StockRepository(db_manager)
config_repo = ConfigRepository(db_manager)
etf_service = EtfDataService(etf_repo, stock_repo, config_repo)

# --- HTML 렌더링 라우트 ---


@app.route("/")
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template("index.html")


@app.route("/settings")
def settings():
    """설정 페이지를 렌더링합니다."""
    return render_template("settings.html")


# --- API 라우트 ---


@app.route("/api/initialize", methods=["POST"])
def initialize_data():
    """
    애플리케이션 초기화 함수. DB가 비어있을 경우 6개월치 데이터를 수집합니다.
    """
    try:
        is_initial_setup_done = etf_service.run_initial_setup()
        if is_initial_setup_done:
            return jsonify(
                {
                    "status": "success",
                    "message": "초기 데이터 수집 및 설정이 완료되었습니다.",
                }
            )
        else:
            return jsonify(
                {
                    "status": "success",
                    "message": "이미 데이터베이스가 존재합니다. 최신 데이터로 업데이트를 진행합니다.",
                }
            )
    except Exception as e:
        logging.error(f"초기화 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": f"초기화 중 오류가 발생했습니다: {str(e)}"}
        ), 500


@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """최신 데이터를 가져와 데이터베이스를 업데이트합니다."""
    try:
        updated_count = etf_service.update_latest_data()
        return jsonify(
            {
                "status": "success",
                "message": f"{updated_count}개의 ETF에 대한 최신 정보가 업데이트되었습니다.",
            }
        )
    except Exception as e:
        logging.error(f"데이터 새로고침 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": f"데이터 새로고침 중 오류가 발생했습니다: {str(e)}",
            }
        ), 500


@app.route("/api/etfs", methods=["GET"])
def get_etfs():
    """필터링된 모든 액티브 ETF 목록을 반환합니다."""
    try:
        etfs = etf_repo.get_all_etfs()
        return jsonify([etf.to_dict() for etf in etfs])
    except Exception as e:
        logging.error(f"ETF 목록 조회 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "ETF 목록을 가져오는 데 실패했습니다."}
        ), 500


@app.route("/api/etf/<ticker>", methods=["GET"])
def get_etf_holdings_comparison(ticker):
    """
    특정 ETF의 구성 종목 정보를 '현재'와 '이전' 날짜를 기준으로 비교하여 반환합니다.
    신규, 제외, 비중 변경 종목을 포함합니다.
    """
    try:
        holdings_comparison = etf_service.get_holdings_comparison(ticker)
        return jsonify(holdings_comparison)
    except Exception as e:
        logging.error(f"ETF 구성 종목 비교 정보 조회 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": "ETF 구성 종목 정보를 가져오는 데 실패했습니다.",
            }
        ), 500


@app.route("/api/etf/<etf_ticker>/stock/<stock_ticker>", methods=["GET"])
def get_stock_weight_history(etf_ticker, stock_ticker):
    """특정 ETF 내 특정 주식의 6개월간 비중 추이를 반환합니다."""
    try:
        history = etf_repo.get_stock_weight_history(etf_ticker, stock_ticker)
        return jsonify(history)
    except Exception as e:
        logging.error(f"주식 비중 추이 조회 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "주식 비중 추이를 가져오는 데 실패했습니다."}
        ), 500


@app.route("/api/export/csv/<ticker>", methods=["GET"])
def export_csv(ticker):
    """선택된 ETF의 현재 구성 종목 정보를 CSV 파일로 내보냅니다."""
    try:
        comparison_data = etf_service.get_holdings_comparison(ticker)
        file_path = etf_service.export_to_csv(ticker, comparison_data)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{ticker}_holdings_{datetime.now().strftime('%Y%m%d')}.csv",
        )
    except Exception as e:
        logging.error(f"CSV 내보내기 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "CSV 파일 생성에 실패했습니다."}
        ), 500


# --- 설정 관리 API 라우트 ---


@app.route("/api/config/themes", methods=["GET", "POST"])
def manage_themes():
    """테마 목록을 조회하거나 새 테마를 추가합니다."""
    try:
        if request.method == "GET":
            themes = config_repo.get_themes()
            return jsonify(themes)
        elif request.method == "POST":
            data = request.json
            if "name" not in data:
                return jsonify(
                    {"status": "error", "message": "테마 이름이 필요합니다."}
                ), 400
            config_repo.add_theme(data["name"])
            return jsonify(
                {
                    "status": "success",
                    "message": f"'{data['name']}' 테마가 추가되었습니다.",
                }
            )
    except Exception as e:
        logging.error(f"테마 관리 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "테마 관리 중 오류가 발생했습니다."}
        ), 500


@app.route("/api/config/themes/<int:theme_id>", methods=["DELETE"])
def delete_theme(theme_id):
    """특정 테마를 삭제합니다."""
    try:
        config_repo.delete_theme(theme_id)
        return jsonify({"status": "success", "message": "테마가 삭제되었습니다."})
    except Exception as e:
        logging.error(f"테마 삭제 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "테마 삭제 중 오류가 발생했습니다."}
        ), 500


@app.route("/api/config/exclusions", methods=["GET", "POST"])
def manage_exclusions():
    """제외 키워드 목록을 조회하거나 새 키워드를 추가합니다."""
    try:
        if request.method == "GET":
            exclusions = config_repo.get_exclusions()
            return jsonify(exclusions)
        elif request.method == "POST":
            data = request.json
            if "keyword" not in data:
                return jsonify(
                    {"status": "error", "message": "키워드가 필요합니다."}
                ), 400
            config_repo.add_exclusion(data["keyword"])
            return jsonify(
                {
                    "status": "success",
                    "message": f"'{data['keyword']}' 키워드가 추가되었습니다.",
                }
            )
    except Exception as e:
        logging.error(f"제외 키워드 관리 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "제외 키워드 관리 중 오류가 발생했습니다."}
        ), 500


@app.route("/api/config/exclusions/<int:exclusion_id>", methods=["DELETE"])
def delete_exclusion(exclusion_id):
    """특정 제외 키워드를 삭제합니다."""
    try:
        config_repo.delete_exclusion(exclusion_id)
        return jsonify(
            {"status": "success", "message": "제외 키워드가 삭제되었습니다."}
        )
    except Exception as e:
        logging.error(f"제외 키워드 삭제 중 오류 발생: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "제외 키워드 삭제 중 오류가 발생했습니다."}
        ), 500


if __name__ == "__main__":
    # 애플리케이션 시작 시 데이터베이스 테이블 생성 확인
    db_manager.create_tables()
    app.run(debug=True, port=5001)
