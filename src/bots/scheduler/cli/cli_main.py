import sys
import json
from src.bots.scheduler.models.schedule_llm import extract_schedule 

def main():
    print("=== LLM 스케줄러 CLI ===")
    print("자연어 일정 문장을 입력하세요. (종료: 엔터 없이 Enter, 또는 q 입력)")

    while True:
        try:
            text = input("\n일정 입력> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break
        if not text or text.lower() == "q":
            print("종료합니다.")
            break

        state = {}
        result = extract_schedule(text, state)
        # print(result)
        event = result.get('event')
        missing = result.get('missing', [])
        # debug = result.get('debug', [])
        response = result.get('response', "처리 결과가 없습니다.")

        print("\n[AI 응답]")
        print(response)

        if event:
            try:
                print("\n[구글 캘린더 event JSON]")
                print(json.dumps(event, ensure_ascii=False, indent=2))
            except Exception:
                print("\n[event dict]")
                print(event)

        if missing:
            print("\n[필요 추가 정보]")
            print(missing)
        # if debug:
        #     print("\n[DEBUG]")
        #     for msg in debug:
        #         print(msg)
        # print("\n" + ("=" * 40))

if __name__ == "__main__":
    main()