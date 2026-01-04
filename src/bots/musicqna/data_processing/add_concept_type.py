import json
import os

# 현재 파일 위치 파악 (예: src/bots/musicqna/data_processing/add_concept_type.py)
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CUR_DIR, "../../../../.."))

JSON_PATH = os.path.join(ROOT_DIR, "data", "musicqna", "processed", "music_theory_curriculum.json")

# 1. 데이터 로드
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    nodes = json.load(f)

def get_concept_type(node):
    if node['parent_id'] is None:
        if any(x in node['concept.ko'] for x in ['기초', '초급', '중급', '고급']):
            return 'foundation_concept'
        return 'foundation_concept'
    if any(x in node['concept.ko'] for x in ['요소', '계열', '구조', '다이아토닉', '모드', '펑션']):
        return 'categorical_concept'
    if any(x in node['concept.ko'] for x in [
        '멜로디', '리듬', '화성', '음정', '코드', '스케일', '모드', '트라이어드', '세븐스', '다이아토닉', '펜타토닉'
    ]):
        return 'core_concept'
    if any(x in node['concept.ko'] for x in [
        '전위', '서브라벨', '서브스티튜션', '어프로치', '작곡', '편곡', '진행', '아르페지오'
    ]):
        return 'technique_concept'
    if any(x in node['concept.ko'] for x in [
        '음표', '쉼표', '임시표', '박자표', '조표', '음자리표', '기호', '표', 'BPM'
    ]):
        return 'symbol_concept'
    if node['parent_id'] is not None:
        par = next((n for n in nodes if n["node_id"] == node['parent_id']), None)
        if par and get_concept_type(par) in ['core_concept', 'categorical_concept']:
            return 'example_concept'
    return 'core_concept'

# 2. concept_type 할당
for node in nodes:
    node['concept_type'] = get_concept_type(node)

# 3. 같은 파일에 덮어쓰기
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)

print(f'자동 분류 결과가 {JSON_PATH}에 덮어써졌습니다.')