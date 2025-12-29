import json

# 평가규칙(룰): 계층 depth와 랭크 패널티, 스코어 등
evaluation_rules = {
    "core_concept": {"max_parent_depth": 1, "score_partial": 0.7},
    "categorical_concept": {"max_parent_depth": 1, "score_partial": 0.7},
    "example_concept": {"max_parent_depth": 2, "score_partial": 0.7},
    "symbol_concept": {"max_parent_depth": 1, "score_partial": 0.7},
    "technique_concept": {"max_parent_depth": 1, "score_partial": 0.7}
}

def get_parent_map(nodes):
    return {n["node_id"]: n.get("parent_id") for n in nodes}

def get_child_map(nodes):
    child_map = {}
    for n in nodes:
        pid = n.get("parent_id")
        if pid is not None:
            child_map.setdefault(pid, []).append(n["node_id"])
    return child_map

def get_node_map(nodes):
    return {n["node_id"]: n for n in nodes}

def evaluate(question_obj, topk_sources, nodes):
    """
    Success  : target_node_id(s) 중 하나라도 Top-K에 있으면
    Partial  : 없지만 parent/child(관련 개념) 중 하나라도 있으면
    Fail     : 그 외
    """
    # 1. target_ids를 항상 리스트로 만들기
    target_ids = question_obj.get("target_node_ids")
    if target_ids is None:
        # 단일 질문이면 기존과 동일하게 리스트로 변환
        target_id = question_obj["target_node_id"]
        target_ids = [target_id]
    # (s가 붙어있으면 리스트, 아니면 단일값을 리스트로 자동 변환)

    source_ids = [x.get("node_id") for x in topk_sources]
    node_map = {n["node_id"]: n for n in nodes}

    # (1) success: target_ids 중 하나라도 Top-K에 있으면 성공
    for tid in target_ids:
        if tid in source_ids:
            return {"outcome_status": "success", "match_node": tid}

    # (2) partial: parent/child 포함이면 partial
    for tid in target_ids:
        target_parent = node_map.get(tid, {}).get("parent_id")
        target_children = [n["node_id"] for n in nodes if n.get("parent_id") == tid]
        for sid in source_ids:
            if sid in target_children or sid == target_parent:
                return {"outcome_status": "partial", "match_node": sid}

    # (3) 그 외는 fail
    return {
        "outcome_status": "fail",
        "match_node": None,
    }


if __name__ == "__main__":
    with open("data/raw/music_theory_curriculum.json", encoding="utf-8") as f:
        nodes = json.load(f)
    with open("data/raw/auto_questions.json", encoding="utf-8") as f:
        questions = json.load(f)
    # dummy 실행 예시
    dummy_sources = [
        {"node_id": 116, "concept_type": "core_concept", "score": 0.88},
        {"node_id": 99, "concept_type": "foundation_concept", "score": 0.82},
    ]
    for q in questions[:10]:
        result = evaluate(q, dummy_sources, nodes)
        print(f"Q: {q['question']}\n → 평가: {result['outcome_status']} [score={result['top1_score']:.2f}]\n{'-'*25}")