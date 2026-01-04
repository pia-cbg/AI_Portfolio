import json
import random
import os

# 현재 파일 위치에서 루트 디렉토리 추적
CUR_DIR = os.path.dirname(os.path.abspath(__file__))  # src/bots/musicqna/data_processing
ROOT_DIR = os.path.abspath(os.path.join(CUR_DIR, "../../../../.."))  # project-root

IN_PATH = os.path.join(ROOT_DIR, "data", "musicqna", "processed", "music_theory_curriculum.json")
OUT_PATH = os.path.join(ROOT_DIR, "data", "musicqna", "processed", "auto_questions.json")

with open(IN_PATH, encoding="utf-8") as f:
    nodes = json.load(f)

questions = []
used_pairs = set()  # 비교형에서 중복 방지

# === 1. 기존 단일 노드 기반 질문 (그대로) ===
for node in nodes:
    concept_ko = node.get("concept.ko", "")
    ctype = node.get("concept_type", "")
    node_id = node.get("node_id")

    questions.append({
        "question": f"{concept_ko}란?",
        "target_node_id": node_id,
        "concept_type": ctype
    })
    questions.append({
        "question": f"{concept_ko}의 정의는?",
        "target_node_id": node_id,
        "concept_type": ctype
    })
    questions.append({
        "question": f"{concept_ko}의 역할은?",
        "target_node_id": node_id,
        "concept_type": ctype
    })

    if node.get("logic"):
        questions.append({
            "question": f"{concept_ko}의 원리(원칙)는?",
            "target_node_id": node_id,
            "concept_type": ctype
        })

    if node.get("tips"):
        questions.append({
            "question": f"{concept_ko} 학습/활용 팁이 있다면?",
            "target_node_id": node_id,
            "concept_type": ctype
        })

    if node.get("examples.name") or node.get("examples.description"):
        questions.append({
            "question": f"{concept_ko}의 예시를 알려줘",
            "target_node_id": node_id,
            "concept_type": ctype
        })

    if node.get("prerequisites.ko") or node.get("prerequisites.en"):
        questions.append({
            "question": f"{concept_ko}를 배우기 전에 알아두면 좋은 선수 지식(개념)은?",
            "target_node_id": node_id,
            "concept_type": ctype
        })

# === 2. 추가: 임의 두 노드(중복X) 비교형 질문 생성 ===
random.seed(42)
num_compare = min(100, len(nodes)*2)
node_indices = list(range(len(nodes)))

for _ in range(num_compare):
    n1, n2 = random.sample(node_indices, 2)
    node1, node2 = nodes[n1], nodes[n2]
    # 중복/순서 상관없는 쌍 방지
    pair_key = tuple(sorted([node1["node_id"], node2["node_id"]]))
    if pair_key in used_pairs or node1["node_id"] == node2["node_id"]:
        continue
    used_pairs.add(pair_key)

    q_sentence = f"{node1.get('concept.ko','')}와 {node2.get('concept.ko','')}의 차이점은?"
    questions.append({
        "question": q_sentence,
        "target_node_ids": [node1["node_id"], node2["node_id"]],
        "concept_types": [node1.get("concept_type"), node2.get("concept_type")]
    })

# === 저장 ===
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"총 {len(questions)}개 질문 생성 완료! (기존+비교질문, {len(nodes)}개 노드 기준)")
print(f"저장 경로: {OUT_PATH}")