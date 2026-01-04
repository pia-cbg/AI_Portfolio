import os
from google_auth_oauthlib.flow import Flow

# 항상 루트 기준으로 동작!
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
TOKEN_DIR = os.path.join(ROOT_DIR, "tokens")
CREDENTIALS = os.path.join(ROOT_DIR, "credentials.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = "http://localhost:8000/"

if not os.path.exists(TOKEN_DIR):
    os.makedirs(TOKEN_DIR)

def token_path(user_id):
    return os.path.join(TOKEN_DIR, f"{user_id}.pickle")

def has_token(user_id):
    return os.path.isfile(token_path(user_id))

def generate_auth_url(user_id):
    flow = Flow.from_client_secrets_file(
        CREDENTIALS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(user_id)
    )
    return auth_url