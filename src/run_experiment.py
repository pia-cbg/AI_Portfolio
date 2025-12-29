import os
import json
import random
import datetime
from main import initialize_system
from src.evaluator import evaluate

def append_results(version_dir, results, successes, fails, partials):
    os.makedirs(version_dir, exist_ok=True)
    for fname, newdata in {
        "all.json": results,
        "success.json": successes,
        "fail.json": fails,
        "partial_fail.json": partials
    }.items():
        fpath = os.path.join(version_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                curdata = json.load(f)
        else:
            curdata = []
        curdata_ids = {str(d.get('question', ''))+str(d.get('target_node_id', '')) for d in curdata}
        adddata = [d for d in newdata if str(d.get('question',''))+str(d.get('target_node_id','')) not in curdata_ids]
        curdata += adddata
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(curdata, f, ensure_ascii=False, indent=2)
    print(f"\n🌱 Results appended: {version_dir}/ (success/fail/partial_fail/all.json)")

def main():
    rag_model = initialize_system()
    with open("data/raw/music_theory_curriculum.json", encoding="utf-8") as f:
        nodes = json.load(f)
    with open("data/raw/auto_questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    # 평가할 질문 수 입력 받아서 랜덤 계산
    try:
        N_SAMPLE = int(input(f"\n평가할 질문 개수를 입력하세요 (최대 {len(questions)}): "))
    except:
        N_SAMPLE = 100
        print(f"(입력 오류로 100개만 평가)")

    if N_SAMPLE > len(questions):
        N_SAMPLE = len(questions)

    random.seed(42)
    questions = random.sample(questions, N_SAMPLE)

    results, successes, fails, partials = [], [], [], []

    now_tag = datetime.datetime.now().strftime("%m%d_%H%M")
    version_dir = os.path.join("data", "logs", now_tag)

    for idx, q in enumerate(questions):
        question_text = q["question"]
        target_node_id = q.get("target_node_id")
        concept_type = q.get("concept_type")
        print(f"\n[{idx+1}/{len(questions)}] 질문: {question_text}")

        try:
            response = rag_model.get_conversation_response(question_text)
        except Exception as e:
            response = {"sources": [], "answer": f"시스템 오류: {str(e)}"}

        topk_sources = response.get("sources", [])
        eval_result = evaluate(q, topk_sources, nodes)
        outcome = eval_result.get("outcome_status")

        resultcase = {
            "question": question_text,
            "target_node_id": target_node_id,
            "concept_type": concept_type,
            "topk_node_ids": [x.get("node_id") for x in topk_sources],
            "topk_concept_types": [x.get("concept_type") for x in topk_sources],
            "topk_scores": [x.get("score") for x in topk_sources if "score" in x],
            "answer": response.get("answer", ""),
            "eval_result": eval_result,
            "topk_sources_full": topk_sources
        }
        results.append(resultcase)
        if outcome == "success":
            successes.append(resultcase)
        elif outcome == "fail":
            fails.append(resultcase)
        elif outcome == "partial":
            partials.append(resultcase)

        print(f"   → 평가결과: {outcome}")
        if outcome != "success":
            print(f"     > TopK node_ids: {resultcase['topk_node_ids']}")
            print(f"     > target(id): {target_node_id} / 매칭: {eval_result.get('match_node')}")
            print(f"     > 답변: {resultcase['answer'][:60]}...")

        # 100개마다 자동 저장(중간질의/멈춤 없음)
        if (idx+1) % 100 == 0 or (idx+1) == len(questions):
            append_results(version_dir, results, successes, fails, partials)
            results, successes, fails, partials = [], [], [], []

    print("\n🌱 전체 루프 완료!")
    print(f"→ 전체 결과: {version_dir}/.json 등 (누적 append)")

if __name__ == "__main__":
    main()