import os
import json
from datetime import datetime
import argparse

# 학습에 사용할 feedback 태그 (수정 가능)
TRAINING_TAGS = {"0", "1", "4"}

GROUNDING_SYSTEM_PROMPT = (
    "You are a music theory expert. For each question, use the retrieved passages only as evidence "
    "if their context—such as key, chord function, or topic—matches the question. "
    "Before using any passage, always check whether it properly applies to the question based on context (e.g. same key, correct chord function, relevant topic). "
    "If a passage is about a different key or context than the question, explicitly state that it does not apply and do not use it as justification for your answer. "
    "Always answer in your own words with clear reasoning, grounding your response only in contextually correct references, and explicitly list your sources if you use them. "
    "If no retrieved passage fully matches the question’s context, answer using your own expertise and state that the evidence did not cover this case. "
    "If additional user feedback is present (correction/comment), use it as guidance to improve your answer. "
    "Do not copy text verbatim."
)

def get_project_root():
    # 현재 파일에서 4단계 위가 프로젝트 루트
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def convert_trainer_session_to_jsonl(session_json_path):
    project_root = get_project_root()
    session_path = os.path.join(project_root, session_json_path)
    finetune_dir = os.path.join(project_root, "data", "fine_tuning", "finetune_data")
    os.makedirs(finetune_dir, exist_ok=True)

    # 세션 파일명에서 타임스탬프 추출 (없으면 그냥 현재시각)
    base = os.path.splitext(os.path.basename(session_json_path))[0]
    ts_parts = base.split('_')
    if len(ts_parts) >= 4:
        timestamp = ts_parts[-2] + "_" + ts_parts[-1]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(finetune_dir, f"finetune_messages_{timestamp}.jsonl")

    with open(session_path, encoding='utf-8') as f:
        session = json.load(f)
    results = session.get("results", [])
    finetune_records = []
    stat = {"total": 0, "excluded": 0, "train_samples": 0, "by_tag": {}}

    for entry in results:
        tag = entry.get("feedback_tag", "0")
        tag_name = entry.get("feedback_label", "")
        stat["by_tag"][tag_name] = stat["by_tag"].get(tag_name, 0) + 1
        stat["total"] += 1
        if tag not in TRAINING_TAGS:
            stat["excluded"] += 1
            continue

        user_content = entry.get("question", "").strip()
        passages = entry.get("retrieved_passages", [])
        if passages:
            user_content += "\n\n참고자료:\n" + "\n---\n".join([p.strip() for p in passages if p.strip()])

        messages = [
            {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        if tag != "0":
            feedback = entry.get("feedback_detail", "").strip()
            if feedback:
                messages.append({"role": "user", "content": f"운영자 피드백({tag_name}): {feedback}"})

        answer = entry.get("model_answer", "").strip()
        messages.append({"role": "assistant", "content": answer})
        finetune_records.append({"messages": messages})
        stat["train_samples"] += 1

    if not finetune_records:
        print("⚠️ 추출된 파인튜닝 샘플이 없습니다.")
        return

    with open(save_path, "w", encoding='utf-8') as f:
        for record in finetune_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"✅ 변환 완료: {os.path.relpath(save_path, project_root)}")
    print(json.dumps(stat, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="trainer_session_*.json → fine-tune messages jsonl")
    parser.add_argument("session_json", help="data/fine_tuning/training_logs/trainer_session_xxxx.json (루트기준 상대경로)")
    args = parser.parse_args()
    convert_trainer_session_to_jsonl(args.session_json)