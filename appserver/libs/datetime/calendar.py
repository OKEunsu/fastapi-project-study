from datetime import date, timedelta

def get_start_weekday_of_month(year:int, month:int) -> int:
    """
    특정 연도와 월의 1일이 무슨 요일인지 계산합니다.

    Args:
        year (int): 계산하려는 연도 (예: 2024)
        month (int): 계산하려는 월 (1~12)

    Returns:
        int: 요일을 나타내는 정수 (0: 월요일, 1: 화요일, ..., 6: 일요일)
    
    >>> get_start_weekday_of_month(2024, 12)
    6
    >>> get_start_weekday_of_month(2025, 2)
    5
    """
    result = date(year, month, 1)
    return result.weekday()

def get_last_day_of_month(year: int, month: int) -> int:
    """특정 연도와 월의 마지막 날짜(일)를 반환합니다.

    Args:
        year (int): 조회하고자 하는 연도.
        month (int): 조회하고자 하는 월 (1~12).

    Returns:
        int: 해당 월의 마지막 날짜 (28, 29, 30, 또는 31).
    
    # 2. Docstring 테스트 케이스 수정
    >>> get_last_day_of_month(2024, 2)  # 윤년
    29
    >>> get_last_day_of_month(2025, 2)  # 평년
    28
    """
    # [로직 설명] 다음 달의 1일을 구한 뒤 하루를 빼면 이번 달의 마지막 날이 됩니다.
    if month == 12:
        # 12월인 경우 다음 해 1월 1일을 기준점으로 잡음
        next_month = date(year + 1, 1, 1)
    else:
        # 그 외에는 다음 달 1일을 기준점으로 잡음
        next_month = date(year, month + 1, 1)
    
    # [핵심] timedelta(days=1)을 빼서 이번 달의 마지막 날 객체를 생성
    result = next_month - timedelta(days=1)
    
    return result.day

def get_range_days_of_month(year:int, month:int):
    """특정 월의 달력 표시를 위한 날짜 리스트를 생성합니다.

    1일이 시작되기 전의 빈칸은 0으로 채워지며, 
    일요일(0)부터 시작하는 달력 한 달 치 데이터의 기반이 됩니다.

    Args:
        year (int): 조회할 연도.
        month (int): 조회할 월 (1~12).

    Returns:
        list[int]: 0(빈칸)과 실제 날짜(1~마지막날)가 섞인 정수 리스트.
    >>> result = get_range_days_of_month(2024, 3)
    >>> result[:5]
    [0, 0, 0, 0, 0]
    >>> result[5]
    1
    >>> len(result)
    36
    >>> result = get_range_days_of_month(2024, 2) # 윤년
    >>> result[:4]
    [0, 0, 0, 0]
    >>> result[4]
    1
    >>> len(result)
    33
    """
    # 월의 시작 요일을 가져옴(월요일=0~일요일=6)
    start_weekday = get_start_weekday_of_month(year, month)
    
    # 월의 마지막 날짜를 가져옴
    last_day = get_last_day_of_month(year, month)
    
    # 월요일 = 0을 월요일=1로 변환(일요일=0으로 만들기 위해)
    start_weekday = (start_weekday + 1) % 7
    
    # 결과 리스트 생성
    result = [0] * start_weekday # 시작 요일 전까지 0으로 채움
    
    # 1일부터 마지막 날까지 추가
    # for day in range(1, last_day + 1):
    #     result.append(day)
        
    return result + list(range(1, last_day + 1))