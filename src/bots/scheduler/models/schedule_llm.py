import openai
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from src.bots.scheduler.prompts.prompts import SCHEDULER_SYSTEM_PROMPT
# from src.bots.scheduler.utils.config import OPENAI_API_KEY

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def extract_schedule(text, state=None, base_date_str=None):
    """
    LLM에 자연어 명령을 입력받아 일정 정보(event/missing)를 추출만 한다.
    성공/실패 등 판정이나 메시지 안내엔 관여하지 않는다.
    """
    if base_date_str is None:
        base_date = datetime.now()
    else:
        base_date = datetime.strptime(base_date_str, '%Y-%m-%d')

    messages = [
        {"role": "system", "content": SCHEDULER_SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2
        )
        llm_reply = completion.choices[0].message.content
    except Exception as e:
        return {
            "event": None,
            "missing": [],
            "done": False,
            "state": state or {},
            "error": f"AI 처리 중 오류: {e}"
        }

    try:
        parsed = json.loads(llm_reply)
    except Exception:
        return {
            "event": None,
            "missing": [],
            "done": False,
            "state": state or {},
            "error": f"LLM 응답 파싱 오류: {llm_reply}"
        }

    event = parsed.get("event")
    missing = parsed.get("missing", [])
    done = event is not None and not missing

    next_state = {
        "event": event,
        "missing": missing
    }

    return {
        "event": event,
        "missing": missing,
        "done": done,
        "state": next_state
    }