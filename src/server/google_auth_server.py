from flask import Flask, request
import os, pickle
from google_auth_oauthlib.flow import Flow

app = Flask(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS = "credentials.json"
TOKEN_DIR = "./tokens"   # 필수: 루트 기준

@app.route('/')
def oauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")  # ← 디스코드 user_id (안쓰면 생략)

    if not code:
        return "code(인가코드) 없음"

    flow = Flow.from_client_secrets_file(
        CREDENTIALS,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/",   # 반드시 콘솔/인증URL와 일치!
        state=state
    )

    flow.fetch_token(code=code)

    # 토큰 저장
    os.makedirs(TOKEN_DIR, exist_ok=True)
    if state:
        token_path = os.path.join(TOKEN_DIR, f"{state}.pickle")
    else:
        token_path = os.path.join(TOKEN_DIR, "token.pickle")
    with open(token_path, "wb") as tokenfile:
        pickle.dump(flow.credentials, tokenfile)

    return "구글 인증 및 토큰 저장 완료! 디스코드로 돌아가세요."

if __name__ == "__main__":
    app.run(port=8000)