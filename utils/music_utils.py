"""음악 이론 관련 유틸리티 함수"""
import re
from typing import Dict, List, Any

def format_chord_name(chord_name: str) -> str:
    """코드 이름을 깔끔하게 포맷팅합니다."""
    # 예: 'Cmaj7' -> 'Cmaj7', 'G 7' -> 'G7', 'F#m7b5' -> 'F#m7♭5'
    chord_name = chord_name.strip().replace(' ', '')
    chord_name = chord_name.replace('b5', '♭5').replace('b9', '♭9')
    chord_name = chord_name.replace('#5', '♯5').replace('#9', '♯9')
    return chord_name

def parse_roman_numeral(numeral: str) -> Dict[str, Any]:
    """로마 숫자 코드 표기를 파싱합니다."""
    # 예: 'V7' -> {'degree': 5, 'quality': 'dominant', 'extension': '7'}
    
    # 기본 품질 (대문자 = 메이저, 소문자 = 마이너)
    quality = 'major' if numeral[0].isupper() else 'minor'
    
    # 로마 숫자 변환
    roman_map = {'i': 1, 'v': 5, 'x': 10}
    degree = 0
    for char in numeral.lower():
        if char in roman_map:
            degree += roman_map[char]
    
    # 확장 추출
    extension = re.search(r'[0-9]+', numeral)
    extension = extension.group(0) if extension else ''
    
    # 변형 기호 처리
    if 'o' in numeral or 'dim' in numeral:
        quality = 'diminished'
    elif '+' in numeral or 'aug' in numeral:
        quality = 'augmented'
    
    return {
        'degree': degree,
        'quality': quality,
        'extension': extension
    }

def generate_key_description(key: str) -> str:
    """키(조성)에 대한 설명을 생성합니다."""
    key_info = {
        'C': {'sharps_flats': '없음', 'relative_minor_key': 'A minor', 'character': '가장 기본적인 조성으로, 흰 건반만 사용합니다.'},
        'G': {'sharps_flats': '# 1개 (F#)', 'relative_minor_key': 'E minor', 'character': '밝고 활기찬 느낌의 조성입니다.'},
        'D': {'sharps_flats': '# 2개 (F#, C#)', 'relative_minor_key': 'B minor', 'character': '강하고 결연한 느낌의 조성입니다.'},
        'A': {'sharps_flats': '# 3개 (F#, C#, G#)', 'relative_minor_key': 'F# minor', 'character': '화려하고 생동감 있는 조성입니다.'},
        'F': {'sharps_flats': '♭ 1개 (B♭)', 'relative_minor_key': 'D minor', 'character': '따뜻하고 부드러운 느낌의 조성입니다.'},
        'B♭': {'sharps_flats': '♭ 2개 (B♭, E♭)', 'relative_minor_key': 'G minor', 'character': '풍부하고 둥근 느낌의 조성입니다.'},
        'E♭': {'sharps_flats': '♭ 3개 (B♭, E♭, A♭)', 'relative_minor_key': 'C minor', 'character': '어둡고 묵직한 느낌의 조성입니다.'}
    }
    
    if key in key_info:
        info = key_info[key]
        return f"{key} Major: 조표 {info['sharps_flats']}, 관계단조 {info['relative_minor_key']}, {info['character']}"
    else:
        return f"{key} Major"

def get_example_songs(chord_progression: List[str]) -> List[str]:
    """특정 코드 진행을 사용하는 예시 곡들을 반환합니다."""
    progression_str = ' - '.join(chord_progression)
    
    examples = {
        'C - G - Am - F': ['Let It Be (Beatles)', '노래방에서 (장범준)', '무한도전 (무한도전)'],
        'G - D - Em - C': ['Country Roads (John Denver)', '청춘 (볼빨간사춘기)'],
        'Am - F - C - G': ['Zombie (The Cranberries)', '그대를 사랑하는 10가지 이유 (이석훈)'],
        'Dm - G - C': ['Fly Me to the Moon (Frank Sinatra)', '어떻게 지내 (오반)'],
        'ii - V - I': ['Autumn Leaves', 'All The Things You Are', '대부분의 재즈 스탠다드'],
        'I - vi - IV - V': ['Stand By Me', 'Beautiful Girls', '수많은 Pop 곡들']
    }
    
    # 정확히 일치하는 코드 진행이 없으면 비슷한 것 찾기
    if progression_str in examples:
        return examples[progression_str]
    
    # 일반적인 진행 패턴 (ii-V-I 등)과 매칭 시도
    for pattern, songs in examples.items():
        if pattern in progression_str:
            return songs
    
    return ['예시 곡을 찾을 수 없습니다.']

def extract_musical_terms(text: str) -> List[str]:
    """텍스트에서 음악 용어를 추출합니다."""
    musical_terms = [
        'Major', 'minor', 'Dominant', 'Tonic', 'Subdominant',
        'chord', 'scale', 'key', 'triad', 'seventh', 'progression',
        'cadence', 'resolution', 'voice leading', 'harmony',
        'diatonic', 'non-diatonic', 'secondary dominant', 'tritone substitution'
    ]
    
    found_terms = []
    for term in musical_terms:
        if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
            found_terms.append(term)
    
    return found_terms


if __name__ == "__main__":
    # 유틸리티 함수 테스트
    print(format_chord_name("G 7"))  # -> G7
    print(parse_roman_numeral("V7"))  # -> {'degree': 5, 'quality': 'major', 'extension': '7'}
    print(generate_key_description("C"))
    print(get_example_songs(["C", "G", "Am", "F"]))
    print(extract_musical_terms("This is a progression using secondary dominant chords"))