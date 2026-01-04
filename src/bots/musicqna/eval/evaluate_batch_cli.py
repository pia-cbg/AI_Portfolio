import os
import json
import random
import datetime
from src.bots.musicqna.cli.cli_main import initialize_system

# === 평가 규칙: 이 파일 안에! ===
def evaluate_musicqna(q, topk_sources, nodes):
    target_ids = q.get("target_node_ids") or [q.get("target_node_id")]
    source_ids = [x.get("node_id") for x in topk_sources]
    node_map = {n["node_id"]: n for n in nodes}
    for tid in target_ids:
        if tid in source_ids:
            return "success"
    for tid in target_ids:
        target_parent = node_map.get(tid, {}).get("parent_id")
        target_children = [n["node_id"] for n in nodes if n.get("parent_id") == tid]
        for sid in source_ids:
            if sid == target_parent or sid in target_children:
                return "partial"
    return "fail"

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

    with open("data/musicqna/processed/music_theory_curriculum.json", encoding="utf-8") as f:
        nodes = json.load(f)
    with open("data/musicqna/processed/auto_questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    try:
        N_SAMPLE = int(input(f"\n평가할 질문 개수를 입력하세요 (최대 {len(questions)}): "))
    except:
        N_SAMPLE = 100
        print(f"(입력 오류로 100개만 평가)")
    N_SAMPLE = min(N_SAMPLE, len(questions))

    # 🟡 시드 입력(없으면 현재 시각(분) 기반 시드)
    seed_input = input("샘플링 랜덤 시드값을 입력하세요 (엔터시 현재 시각 기준): ").strip()
    if seed_input:
        try:
            seed_value = int(seed_input)
            print(f"☑️ [고정 시드 사용] seed = {seed_value}")
        except Exception:
            print(f"입력 시드값이 잘못되었습니다. 현재 시각으로 seed 사용.")
            seed_value = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            print(f"☑️ [기본 시드 사용] seed = {seed_value}")
    else:
        seed_value = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
        print(f"☑️ [기본 시드 사용] seed = {seed_value}")

    random.seed(seed_value)

    questions = random.sample(questions, N_SAMPLE)

    results, successes, fails, partials = [], [], [], []

    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y%m%d_%H%M")
    version_dir = os.path.join(
        "data", "musicqna", "batch_logs",
        f"{now_str}_seed{seed_value}"
    )

    for idx, q in enumerate(questions):
        question_text = q["question"]
        target_node_id = q.get("target_node_id")
        print(f"\n[{idx+1}/{N_SAMPLE}] 질문: {question_text}")

        try:
            response = rag_model.get_conversation_response(question_text)
        except Exception as e:
            response = {"sources": [], "answer": f"시스템 오류: {str(e)}"}
        topk_sources = response.get("sources", [])
        label = evaluate_musicqna(q, topk_sources, nodes)
        eval_log = {
            "question": question_text,
            "target_node_id": target_node_id,
            "topk_node_ids": [x.get("node_id") for x in topk_sources],
            "answer": response.get('answer', ''),
            "label": label,
            "topk_sources_full": topk_sources
        }
        results.append(eval_log)
        if label == "success":
            successes.append(eval_log)
        elif label == "fail":
            fails.append(eval_log)
        elif label == "partial":
            partials.append(eval_log)

        print(f"   → 평가결과: {label}")

        if (idx+1) % 100 == 0 or (idx+1) == N_SAMPLE:
            append_results(version_dir, results, successes, fails, partials)
            results, successes, fails, partials = [], [], [], []

    print("\n🌱 전체 루프 완료!")
    print(f"→ 전체 결과: {version_dir}/.json 등 (누적 append)")

if __name__ == "__main__":
    main()