import re
from datetime import datetime
import dateparser

def resolve_relative_date_kor(natural_kor_str, base_date):
    """
    한국/상대표현 자연어 일정문장 → datetime 변환.
    - 날짜/시간 slot(월일/년월일 + 시) 모두 명확해야 함
    - 모호한 시간 표기는 예외
    - ISO 형식, '내일', '모레' 등도 지원
    - 파싱 실패시 반드시 ValueError 발생(빈/애매/불완전 등)
    """
    orig = natural_kor_str.strip()
    if not orig:
        raise ValueError("빈 입력")

    # (1) 완전 ISO 포맷일 때
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", orig):
        dt = dateparser.parse(orig)
        if dt:
            return dt, []
        else:
            raise ValueError(f"ISO8601 파싱 실패: '{orig}'")

    # (2) 애매/추측 불가 시간 표현은 강제 예외
    ambiguous_time = ["저녁", "아침", "심야", "밤", "점심", "새벽"]
    if any(word in orig for word in ambiguous_time):
        raise ValueError(f"모호한 시간표현(추정·자동변환X): '{orig}'")

    # (3) 날짜/시간 필수 slot 체크
    year = re.search(r'(\d{4})년', orig)
    month = re.search(r'(\d{1,2})월', orig)
    day = re.search(r'(\d{1,2})일', orig)
    hour = re.search(r'(\d{1,2})시', orig) or re.search(r'(\d{1,2}):(\d{2})', orig)
    am_pm = re.search(r'(오전|오후)\s*(\d{1,2})시', orig)
    is_relative = any(x in orig for x in ["내일", "모레", "오늘", "주말", "이번주", "다음주", "다다음주"])

    has_full_date = (year and month and day) or (month and day)
    has_time = (hour or am_pm)

    # 날짜/시간 정보 부족
    if not ((has_full_date and has_time) or is_relative):
        raise ValueError(f"날짜/시간 slot 불충분: '{orig}'")

    # (4) dateparser 우선 해석 (internal, 상대표현 등)
    dt = dateparser.parse(orig, languages=["ko"], settings={'RELATIVE_BASE': base_date})

    # (5) Fallback 정형식 처리

    # 5-1. 'YYYY년 MM월 DD일 HH시(분)'
    m_full = re.match(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*([0-2]?\d)시(?:\s*(\d{1,2})분)?', orig)
    if not dt and m_full:
        year, month, day, hour = map(int, m_full.groups()[:4])
        minute = int(m_full.group(5)) if m_full.group(5) else 0
        dt = datetime(year, month, day, hour, minute, 0)
        return dt, []

    # 5-2. 'MM월 DD일 오전/오후 HH시(분)'
    m_ampm = re.match(r'(\d{1,2})월\s*(\d{1,2})일\s*(오전|오후)\s*([0-2]?\d)시(?:\s*(\d{1,2})분)?', orig)
    if not dt and m_ampm:
        month, day, ampm, hour, minute = m_ampm.groups()
        month, day, hour = map(int, [month, day, hour])
        minute = int(minute) if minute else 0
        year = base_date.year
        if (month < base_date.month) or (month == base_date.month and day < base_date.day):
            year += 1
        if ampm == '오후' and hour != 12:
            hour += 12
        elif ampm == '오전' and hour == 12:
            hour = 0
        dt = datetime(year, month, day, hour, minute, 0)
        return dt, []

    # 5-3. 'MM월 DD일 HH시(분)'
    m_md_hm = re.match(r'(\d{1,2})월\s*(\d{1,2})일\s*([0-2]?\d)시(?:\s*(\d{1,2})분)?', orig)
    if not dt and m_md_hm:
        month, day, hour = map(int, m_md_hm.groups()[:3])
        minute = int(m_md_hm.group(4)) if m_md_hm.group(4) else 0
        year = base_date.year
        if (month < base_date.month) or (month == base_date.month and day < base_date.day):
            year += 1
        dt = datetime(year, month, day, hour, minute, 0)
        return dt, []

    # 5-4. '오전/오후 HH시(분)' (날짜: base_date)
    m_ampm_hm = re.match(r'(오전|오후)\s*([0-2]?\d)시(?:\s*(\d{1,2})분)?', orig)
    if not dt and m_ampm_hm:
        ampm, hour, minute = m_ampm_hm.groups()
        hour = int(hour)
        minute = int(minute) if minute else 0
        if ampm == '오후' and hour != 12: hour += 12
        elif ampm == '오전' and hour == 12: hour = 0
        dt = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return dt, []

    if dt:
        return dt, []

    raise ValueError(f"명확한 날짜/시간 파싱 실패: '{orig}'")