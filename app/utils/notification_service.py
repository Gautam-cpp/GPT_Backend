
import firebase_admin
from firebase_admin import messaging

def send_push_notification(target_uid: int, title: str, body: str, data: dict):
    """Send FCM push (topic-based: `user-{id}`)"""
    try:
        topic = f"user-{target_uid}"
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in data.items()},
            topic=topic,
        )
        messaging.send(message)
    except Exception as exc:
        # Log but never fail the request
        print(f"FCM error: {exc}")
