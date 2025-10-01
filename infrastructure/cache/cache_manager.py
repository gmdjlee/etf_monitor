"""
Cache Manager
메모리 기반 캐싱 레이어를 제공합니다.
✅ Medium Priority: 성능 최적화
"""

import time
from datetime import datetime
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional

from config.logging_config import LoggerMixin
from config.settings import settings


class CacheManager(LoggerMixin):
    """
    메모리 기반 캐시 매니저

    TTL(Time To Live) 기반으로 캐시를 관리하며,
    자주 조회되는 데이터의 성능을 향상시킵니다.

    Thread-safe 구현으로 멀티스레드 환경에서 안전합니다.
    """

    def __init__(self, default_ttl: int = None):
        """
        Args:
            default_ttl: 기본 TTL (초), None이면 설정값 사용
        """
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl or settings.CACHE_TTL_SECONDS
        self.enabled = settings.CACHE_ENABLED

        self.logger.info(
            f"CacheManager initialized: enabled={self.enabled}, ttl={self.default_ttl}s"
        )

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값을 조회합니다.

        Args:
            key: 캐시 키

        Returns:
            캐시된 값, 없거나 만료되었으면 None
        """
        if not self.enabled:
            return None

        with self._lock:
            if key not in self._cache:
                return None

            # TTL 확인
            if self._is_expired(key):
                self._delete_internal(key)
                return None

            value = self._cache[key]
            self.logger.debug(f"Cache HIT: {key}")
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        캐시에 값을 저장합니다.

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초), None이면 기본값 사용
        """
        if not self.enabled:
            return

        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = datetime.now()

            self.logger.debug(f"Cache SET: {key} (ttl={ttl or self.default_ttl}s)")

    def delete(self, key: str) -> None:
        """캐시에서 특정 키를 삭제합니다."""
        if not self.enabled:
            return

        with self._lock:
            self._delete_internal(key)

    def _delete_internal(self, key: str) -> None:
        """내부용 삭제 메서드 (락 없음)"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            self.logger.debug(f"Cache DELETE: {key}")

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        if not self.enabled:
            return

        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            self.logger.info(f"Cache CLEAR: {count} items removed")

    def clear_pattern(self, pattern: str) -> int:
        """
        패턴과 일치하는 캐시를 삭제합니다.

        Args:
            pattern: 키 패턴 (예: "etf:*", "*:2024-01-01")

        Returns:
            삭제된 항목 수
        """
        if not self.enabled:
            return 0

        with self._lock:
            # 와일드카드 패턴 처리
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            elif pattern.startswith("*"):
                suffix = pattern[1:]
                keys_to_delete = [k for k in self._cache.keys() if k.endswith(suffix)]
            else:
                keys_to_delete = [k for k in self._cache.keys() if pattern in k]

            for key in keys_to_delete:
                self._delete_internal(key)

            self.logger.info(
                f"Cache CLEAR PATTERN '{pattern}': {len(keys_to_delete)} items"
            )
            return len(keys_to_delete)

    def _is_expired(self, key: str) -> bool:
        """캐시 항목이 만료되었는지 확인합니다."""
        if key not in self._timestamps:
            return True

        age = datetime.now() - self._timestamps[key]
        return age.total_seconds() > self.default_ttl

    def cleanup_expired(self) -> int:
        """
        만료된 캐시 항목을 정리합니다.

        Returns:
            삭제된 항목 수
        """
        if not self.enabled:
            return 0

        with self._lock:
            expired_keys = [key for key in self._cache.keys() if self._is_expired(key)]

            for key in expired_keys:
                self._delete_internal(key)

            if expired_keys:
                self.logger.info(
                    f"Cache CLEANUP: {len(expired_keys)} expired items removed"
                )

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계를 반환합니다."""
        with self._lock:
            return {
                "enabled": self.enabled,
                "total_items": len(self._cache),
                "default_ttl": self.default_ttl,
                "memory_usage_estimate": self._estimate_memory_usage(),
            }

    def _estimate_memory_usage(self) -> str:
        """메모리 사용량 추정 (간단한 근사치)"""
        try:
            import sys

            total_size = sum(
                sys.getsizeof(k) + sys.getsizeof(v) for k, v in self._cache.items()
            )

            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.2f} KB"
            else:
                return f"{total_size / (1024 * 1024):.2f} MB"
        except:
            return "Unknown"


# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        ttl: TTL (초)
        key_prefix: 캐시 키 접두사

    Examples:
        >>> @cached(ttl=300, key_prefix="etf")
        >>> def get_etf_list():
        ...     return expensive_query()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return func(*args, **kwargs)

            # 캐시 키 생성
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            # 캐시 조회
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 캐시 미스 - 함수 실행
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            # 결과 캐싱
            cache_manager.set(cache_key, result, ttl)

            cache_manager.logger.debug(
                f"Cache MISS: {cache_key} (computed in {elapsed:.3f}s)"
            )

            return result

        return wrapper

    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str) -> str:
    """캐시 키를 생성합니다."""
    # 함수명
    func_name = f"{func.__module__}.{func.__name__}"

    # 인자를 문자열로 변환
    args_str = "_".join(str(arg) for arg in args)
    kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

    # 키 조합
    parts = [prefix, func_name, args_str, kwargs_str]
    key = ":".join(part for part in parts if part)

    # 너무 긴 키는 해시로 변환
    if len(key) > 200:
        import hashlib

        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"

    return key


def invalidate_cache(pattern: str) -> int:
    """
    패턴과 일치하는 캐시를 무효화합니다.

    Args:
        pattern: 키 패턴

    Returns:
        삭제된 항목 수
    """
    return cache_manager.clear_pattern(pattern)
