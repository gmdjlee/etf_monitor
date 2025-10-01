"""
Cache Performance Test
캐시 성능을 측정하고 검증하는 테스트 스크립트
✅ Medium Priority: 캐싱 효과 측정
"""

import time

from infrastructure.cache import cache_manager, cached


def measure_execution_time(func, *args, **kwargs):
    """함수 실행 시간을 측정합니다."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


# 무거운 연산을 시뮬레이션하는 함수
def expensive_operation(n: int) -> int:
    """
    시간이 오래 걸리는 연산을 시뮬레이션합니다.
    """
    time.sleep(0.5)  # 0.5초 지연
    return sum(range(n))


# 캐싱이 적용된 버전
@cached(ttl=60, key_prefix="test")
def cached_expensive_operation(n: int) -> int:
    """캐싱이 적용된 무거운 연산"""
    time.sleep(0.5)
    return sum(range(n))


def test_cache_performance():
    """캐시 성능을 테스트합니다."""
    print("=" * 60)
    print("Cache Performance Test")
    print("=" * 60)

    # 캐시 활성화 확인
    print(f"\n캐시 상태: {'활성화' if cache_manager.enabled else '비활성화'}")
    print(f"기본 TTL: {cache_manager.default_ttl}초")

    # 테스트 1: 캐시 미적용 vs 적용
    print("\n" + "=" * 60)
    print("테스트 1: 캐시 미적용 vs 적용")
    print("=" * 60)

    n = 1000000

    # 캐시 미적용
    print("\n[캐시 미적용]")
    _, time1 = measure_execution_time(expensive_operation, n)
    print(f"  1차 실행: {time1:.3f}초")

    _, time2 = measure_execution_time(expensive_operation, n)
    print(f"  2차 실행: {time2:.3f}초")

    # 캐시 적용
    print("\n[캐시 적용]")
    cache_manager.clear()  # 캐시 초기화

    _, time3 = measure_execution_time(cached_expensive_operation, n)
    print(f"  1차 실행 (Cache MISS): {time3:.3f}초")

    _, time4 = measure_execution_time(cached_expensive_operation, n)
    print(f"  2차 실행 (Cache HIT): {time4:.3f}초")

    speedup = time3 / time4 if time4 > 0 else 0
    print(f"\n  ✅ 속도 향상: {speedup:.1f}배")

    # 테스트 2: 캐시 통계
    print("\n" + "=" * 60)
    print("테스트 2: 캐시 통계")
    print("=" * 60)

    stats = cache_manager.get_stats()
    print(f"\n  총 캐시 항목: {stats['total_items']}")
    print(f"  메모리 사용량: {stats['memory_usage_estimate']}")
    print(f"  기본 TTL: {stats['default_ttl']}초")

    # 테스트 3: 캐시 무효화
    print("\n" + "=" * 60)
    print("테스트 3: 캐시 무효화")
    print("=" * 60)

    # 여러 캐시 항목 생성
    for i in range(5):
        cached_expensive_operation(1000 * (i + 1))

    stats = cache_manager.get_stats()
    print(f"\n  캐시 항목 생성: {stats['total_items']}개")

    # 패턴으로 삭제
    deleted = cache_manager.clear_pattern("test:*")
    print(f"  패턴 삭제 (test:*): {deleted}개")

    stats = cache_manager.get_stats()
    print(f"  남은 캐시 항목: {stats['total_items']}개")

    # 테스트 4: TTL 만료 테스트
    print("\n" + "=" * 60)
    print("테스트 4: TTL 만료 테스트")
    print("=" * 60)

    # 짧은 TTL로 캐시 설정
    cache_manager.set("test_ttl", "value", ttl=2)

    value = cache_manager.get("test_ttl")
    print(f"\n  즉시 조회: {value}")

    print("  2초 대기 중...")
    time.sleep(2.1)

    value = cache_manager.get("test_ttl")
    print(f"  2초 후 조회: {value}")

    # 정리
    cache_manager.clear()

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


def test_real_world_scenario():
    """실제 사용 시나리오를 테스트합니다."""
    print("\n" + "=" * 60)
    print("실제 시나리오 테스트: ETF 목록 조회")
    print("=" * 60)

    # ETF 목록 조회를 시뮬레이션
    @cached(ttl=300, key_prefix="etf:list")
    def get_etf_list():
        """ETF 목록 조회 (DB 쿼리 시뮬레이션)"""
        time.sleep(0.3)  # DB 쿼리 시간
        return [
            {"ticker": "152100", "name": "TIGER 반도체"},
            {"ticker": "091160", "name": "KODEX 반도체"},
            {"ticker": "364960", "name": "TIGER 차이나전기차"},
        ]

    # 첫 번째 조회 (Cache MISS)
    result1, time1 = measure_execution_time(get_etf_list)
    print(f"\n  1차 조회 (Cache MISS): {time1:.3f}초")
    print(f"  결과: {len(result1)}개 ETF")

    # 두 번째 조회 (Cache HIT)
    result2, time2 = measure_execution_time(get_etf_list)
    print(f"  2차 조회 (Cache HIT): {time2:.3f}초")
    print(f"  결과: {len(result2)}개 ETF")

    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n  ✅ 속도 향상: {speedup:.1f}배")
    print(f"  절약된 시간: {(time1 - time2) * 1000:.1f}ms")


if __name__ == "__main__":
    # 캐시 활성화
    from config.settings import settings

    settings.CACHE_ENABLED = True

    # 테스트 실행
    test_cache_performance()
    test_real_world_scenario()

    print("\n✅ 모든 테스트 완료!")
