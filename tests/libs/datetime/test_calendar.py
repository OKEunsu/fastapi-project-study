from appserver.libs.datetime.calendar import get_start_weekday_of_month, get_last_day_of_month, get_range_days_of_month
import pytest

def test_get_start_weekday_of_month():
    assert get_start_weekday_of_month(2024, 12) == 6
    assert get_start_weekday_of_month(2025, 2) == 5
    
def test_get_last_day_of_month():
    assert get_last_day_of_month(2024, 2) == 29
    assert get_last_day_of_month(2025, 2) == 28
    assert get_last_day_of_month(2024, 4) == 30
    assert get_last_day_of_month(2024, 12) == 31

# @pytest.mark.parametrize: 데이터 기반 테스트 장식자
# 테스트 함수 하나를 복사-붙여넣기를 해서 여러 개 만들 필요 없이,
# 데이터만 리스트로 관리하기 때문에 코드가 매우 깔끔
@pytest.mark.parametrize("year, month, expected", [
    (2024, 12, 6), # 케이스 1: 2024년 12월은 일요일(6) 시작
    (2025, 2, 5),  # 케이스 2: 2025년 2월은 토요일(5) 시작
])
def test_get_start_weekday_of_month(year, month, expected):
    """
    다양한 연도와 월에 대해 시작 요일 계산 로직을 검증합니다.

    Args:
        year (int): 테스트할 연도
        month (int): 테스트할 월
        expected (int): 기대되는 시작 요일 결과값 (0~6)
    """
    # [주석 공부 포인트]
    # parametrize에 적힌 데이터들이 순서대로 year, month, expected 변수에 들어옵니다.
    # 즉, 이 함수는 내부적으로 총 2번(리스트의 개수만큼) 실행됩니다.
    assert get_start_weekday_of_month(year, month) == expected
    
@pytest.mark.parametrize("year, month, expected", [
    (2024, 2, 29),
    (2025, 2, 28),
    (2024, 4, 30),
    (2024, 12, 31),
])
def test_get_last_day_of_month(year, month, expected):
    assert get_last_day_of_month(year, month) == expected
    
@pytest.mark.parametrize("year, month, expected_padding_count, expected_total_count", [
    (2024, 3, 5, 36),
    (2024, 2, 4, 33),
    (2025, 2, 6, 34),
    (2024, 4, 1, 31),
    (2024, 12, 0, 31),
])
def test_get_range_days_of_month(year, month, expected_padding_count, expected_total_count):
    days = get_range_days_of_month(year, month)
    padding_count = days[:expected_padding_count]
    
    assert sum(padding_count) == 0
    assert days[expected_padding_count] == 1
    assert len(days) == expected_total_count