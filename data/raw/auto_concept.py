import json

# 1. 데이터 로드
with open('/Users/cbg/github/AI_Portfolio/data/raw/music_theory_curriculum copy.json', 'r', encoding='utf-8') as f:
    nodes = json.load(f)

def get_concept_type(node):
    # 최상위 기초 - parent_id==null
    if node['parent_id'] is None:
        if '기초' in node['concept.ko'] or '초급' in node['concept.ko'] or '중급' in node['concept.ko'] or '고급' in node['concept.ko']:
            return 'foundation_concept'
        # 예외적으로 '코드' 등은 core로 의도될 수 있으나 일단 기초로 부여
        return 'foundation_concept'
    
    # 카테고리 체계: "요소", "계열", "구조", "다이아토닉", "세븐스 코드" 등
    if any(x in node['concept.ko'] for x in ['요소', '계열', '구조', '다이아토닉', '모드', '펑션']):
        return 'categorical_concept'
    
    # 코어개념: '멜로디', '리듬', '화성', '코드', '음정', '스케일', '테크닉', '트라이어드', 쇠붙이류
    if any(x in node['concept.ko'] for x in [
        '멜로디', '리듬', '화성', '음정', '코드', '스케일', '모드', '트라이어드', '세븐스', '다이아토닉', '펜타토닉'
    ]):
        return 'core_concept'
    
    # 기법/진행/특수개념
    if any(x in node['concept.ko'] for x in [
        '전위', '서브라벨', '서브스티튜션', '어프로치', '작곡', '편곡', '진행', '아르페지오'
    ]):
        return 'technique_concept'
        
    # 표기/기호/음표/쉼표/표
    if any(x in node['concept.ko'] for x in [
        '음표', '쉼표', '임시표', '박자표', '조표', '음자리표', '기호', '표', 'BPM'
    ]):
        return 'symbol_concept'
    
    # 실제 구체적 코드/스케일/예시류, parent가 core/concept/categorical이면 예시로 가정
    if node['parent_id'] is not None:
        par = next((n for n in nodes if n["node_id"]==node['parent_id']), None)
        if par and get_concept_type(par) in ['core_concept', 'categorical_concept']:
            return 'example_concept'
    
    # 기본값 (애매할 땐 core로)
    return 'core_concept'

# 2. 자동 concept_type 할당
for node in nodes:
    node['concept_type'] = get_concept_type(node)

# 3. 결과 저장
with open('music_nodes_with_type.json', 'w', encoding='utf-8') as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)

print('자동 분류 결과가 music_nodes_with_type.json에 저장되었습니다.')