"""
애플리케이션 설정 (Medium Priority 확인)
상수, 기본값, 환경 변수 등을 관리합니다.
"""

import os
from typing import List


class Settings:
    """애플리케이션 전역 설정"""

    # 애플리케이션 정보
    APP_NAME = "ETF Monitoring System"
    APP_VERSION = "2.1.0"  # ✅ 버전 업데이트

    # 데이터베이스 설정
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    DATABASE_NAME = "etf_monitor.db"
    DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

    # Flask 설정
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")

    # 데이터 수집 설정
    DEFAULT_COLLECT_DAYS = 10
    MAX_COLLECT_DAYS = 360
    API_DELAY_SECONDS = 0.1
    RETRY_MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 1

    # ETF 필터링 설정
    REQUIRE_ACTIVE_KEYWORD = True
    ACTIVE_KEYWORD = "액티브"

    # 기본 테마 키워드
    DEFAULT_THEMES: List[str] = [
        "반도체",
        "바이오",
        "혁신기술",
        "배당성장",
        "신재생",
        "2차전지",
        "AI",
        "코스피",
        "조선",
        "테크",
        "수출",
        "로봇",
        "컬처",
        "밸류업",
        "친환경",
        "소비",
        "이노베이션",
        "메모리",
        "비메모리",
        "인공지능",
        "전기차",
        "배터리",
        "ESG",
        "탄소중립",
        "메타버스",
        "블록체인",
        "헬스케어",
        "IT",
        "성장",
    ]

    # 기본 제외 키워드
    DEFAULT_EXCLUSIONS: List[str] = [
        "인버스",
        "레버리지",
        "곱버스",
        "2X",
        "3X",
        "글로벌",
        "차이나",
        "채권",
        "달러",
        "China",
        "아시아",
        "미국",
        "일본",
        "코스피",
        "코스닥",
    ]

    # 통계 설정
    DEFAULT_STATS_LIMIT = 100
    MIN_DUPLICATE_COUNT = 2

    # CSV 내보내기 설정
    EXPORT_DIR = os.path.join(BASE_DIR, "temp_exports")
    CSV_ENCODING = "utf-8-sig"

    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # ✅ 캐싱 설정 (Medium Priority)
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5분

    # 캐시 TTL 세부 설정
    CACHE_TTL_ETF_LIST = 300  # ETF 목록: 5분
    CACHE_TTL_ETF_DETAIL = 600  # ETF 상세: 10분
    CACHE_TTL_HOLDINGS = 180  # 보유 종목: 3분
    CACHE_TTL_STATISTICS = 300  # 통계: 5분

    # 페이징 설정
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # 날짜 형식
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    KRX_DATE_FORMAT = "%Y%m%d"

    # API 응답 설정
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False

    # 비즈니스 규칙
    MIN_WEIGHT_THRESHOLD = 0.01
    WEIGHT_CHANGE_SIGNIFICANT = 0.5

    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리가 없으면 생성"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        os.makedirs(cls.EXPORT_DIR, exist_ok=True)

    @classmethod
    def get_database_url(cls) -> str:
        """데이터베이스 URL 반환"""
        return f"sqlite:///{cls.DATABASE_PATH}"

    @classmethod
    def is_development(cls) -> bool:
        """개발 환경인지 확인"""
        return cls.FLASK_DEBUG

    @classmethod
    def is_production(cls) -> bool:
        """운영 환경인지 확인"""
        return not cls.FLASK_DEBUG


class MarketSettings:
    """시장 관련 설정"""

    # 시장 코드
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    MARKETS = [KOSPI, KOSDAQ]

    # 영업일 설정
    BUSINESS_DAYS = [0, 1, 2, 3, 4]  # 월~금

    # 시장 개장 시간
    MARKET_OPEN_HOUR = 9
    MARKET_CLOSE_HOUR = 15
    MARKET_CLOSE_MINUTE = 30

    # 대표 종목
    REFERENCE_TICKER = "005930"  # 삼성전자


class FilterSettings:
    """필터링 관련 설정"""

    FILTER_TYPE_THEME = "theme"
    FILTER_TYPE_EXCLUSION = "exclusion"
    FILTER_TYPE_ACTIVE = "active"

    OPERATOR_AND = "AND"
    OPERATOR_OR = "OR"

    DEFAULT_FILTER_OPERATOR = OPERATOR_AND


class StatisticsSettings:
    """통계 관련 설정"""

    STATS_TYPE_DUPLICATE = "duplicate"
    STATS_TYPE_AMOUNT = "amount"
    STATS_TYPE_WEIGHT = "weight"

    SORT_BY_COUNT = "count"
    SORT_BY_AMOUNT = "amount"
    SORT_BY_WEIGHT = "weight"
    SORT_BY_NAME = "name"

    DEFAULT_SORT_BY = SORT_BY_COUNT
    DEFAULT_SORT_ORDER = "desc"


# 싱글톤 인스턴스
settings = Settings()
market_settings = MarketSettings()
filter_settings = FilterSettings()
statistics_settings = StatisticsSettings()

# 애플리케이션 시작 시 필요한 디렉토리 생성
settings.ensure_directories()
