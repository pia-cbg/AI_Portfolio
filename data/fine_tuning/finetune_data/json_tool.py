import json
import tiktoken

FILEPATH = "/Users/cbg/github/AI_Portfolio/data/fine_tuning/finetune_data/finetune_messages_20250717_014759.jsonl"

# 모델 별로 encoding 선택: gpt-3.5-turbo, gpt-4 등
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

bad_lines = []
long_lines = []
max_total_tokens = 16384  # context window (gpt-3.5-turbo 기준), 예: 16k

with open(FILEPATH, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        try:
            data = json.loads(line)
        except Exception as e:
            print(f"{i}번째 줄: JSON 파싱 에러 : {e}")
            continue

        messages = data.get("messages", [])
        roles = [m.get('role', '') for m in messages]
        assistant_msgs = [m['content'] for m in messages if m.get('role', '') == "assistant"]

        # 1) assistant role 유무 체크
        if not assistant_msgs:
            print(f"{i}번째 줄: assistant role이 없음 (roles={roles})")
            bad_lines.append(i)

        # 2) 토큰 수 체크
        total_content = ''.join([m.get('content', '') for m in messages])
        total_tokens = len(enc.encode(total_content))
        if total_tokens > max_total_tokens:
            print(f"{i}번째 줄: 전체 토큰 {total_tokens} (16k 초과, context window 밖일 수 있음)")
            long_lines.append((i, total_tokens))

        for am in assistant_msgs:
            t = len(enc.encode(am))
            if t > max_total_tokens:
                print(f"{i}번째 줄: assistant 메시지 토큰 {t} (16k 초과!)")
                long_lines.append((i, f"assistant:{t}"))

print("\n======= 요약 =======")
print(f"assistant role 없는 샘플: {bad_lines}")
print(f"토큰 초과 샘플 (줄번호, 토큰수): {long_lines}")