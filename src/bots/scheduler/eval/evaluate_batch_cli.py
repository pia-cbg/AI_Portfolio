import os
import json
import random
import datetime
import re
from src.bots.scheduler.models.schedule_llm import extract_schedule
from src.bots.scheduler.utils.date_utils import resolve_relative_date_kor

def is_iso_datetime(dt_str):
    return bool(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", dt_str))

def try_to_iso(natural_str, base_date):
    try:
        dt, _ = resolve_relative_date_kor(natural_str, base_date)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    except Exception:
        return None

def evaluate_event(event, input_text):
    if not event:
        return "fail"

    start = event.get('start', {}).get('dateTime', '')
    end = event.get('end', {}).get('dateTime', '')
    summary = (event.get('summary', '') or '').strip()
    description = (event.get('description', '') or '').strip()
    now = datetime.datetime.now()

    # 1. 자연어 → ISO 변환 시도
    start_iso = try_to_iso(start, now)
    end_iso = try_to_iso(end, now)

    if start_iso and end_iso and is_iso_datetime(start_iso) and is_iso_datetime(end_iso):
        event['start']['dateTime'] = start_iso
        event['end']['dateTime'] = end_iso

        # 2. success/partial/fail 분기
        if summary and description:
            return "success"
        elif summary or description:
            return "partial"
        else:
            return "fail"
    else:
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
        curdata_keys = {d.get('input','') for d in curdata}
        adddata = [d for d in newdata if d.get('input', '') not in curdata_keys]
        curdata += adddata
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(curdata, f, ensure_ascii=False, indent=2)
    print(f"\n🌱 Results appended: {version_dir}/ (success/fail/partial_fail/all.json)")

def main():
    input_path = os.path.join("data", "scheduler", "processed", "auto_schedule_questions.json")
    with open(input_path, encoding="utf-8") as f:
        questions = json.load(f)

    try:
        N_SAMPLE = int(input(f"\n평가할 질문 개수를 입력하세요 (최대 {len(questions)}): "))
    except:
        N_SAMPLE = 100
        print(f"(입력 오류로 100개만 평가)")
    N_SAMPLE = min(N_SAMPLE, len(questions))

    # 🟡 시드 입력: 없으면 현재 날짜(분까지)를 int로 변환
    seed_input = input("샘플링 랜덤 시드값을 입력하세요 (엔터시 현재 시각 기반): ").strip()
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
        "data", "scheduler", "batch_logs",
        f"{now_str}_seed{seed_value}"
    )

    for idx, question_text in enumerate(questions):
        print(f"\n[{idx+1}/{N_SAMPLE}] 질문: {question_text}")
        try:
            result = extract_schedule(question_text)
            event = result.get('event')
        except Exception as e:
            result = {"event": None, "response": str(e)}
            event = None

        label = evaluate_event(event, question_text)
        eval_log = {
            "input": question_text,
            "event": event,
            "llm_response": result.get("response"),
            "label": label,
            "missing": result.get("missing"),
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