import pickle
from googleapiclient.discovery import build

def get_gcal_creds(user_id):
    with open(f"tokens/{user_id}.pickle", "rb") as f:
        creds = pickle.load(f)
    return creds

def add_event(event_dict, user_id):
    creds = get_gcal_creds(user_id)
    service = build("calendar", "v3", credentials=creds)
    event = service.events().insert(calendarId='primary', body=event_dict).execute()
    return event.get("htmlLink")