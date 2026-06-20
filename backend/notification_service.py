from sqlalchemy.orm import Session
from backend.models import NotificationLog

def send_notification(db: Session, user_id: int, notification_type: str, content: str) -> NotificationLog:
    """
    Simulates sending an Email, SMS, or WhatsApp notification.
    Logs the result to the database for testing and admin visibility.
    """
    # Print to console/system logs as standard logging, sanitizing emojis for Windows terminals
    safe_content = content.encode('ascii', errors='replace').decode('ascii')
    print(f"[NOTIFICATION - {notification_type.upper()}] Sent to User ID {user_id}: {safe_content}")
    
    # Save log entry - keep original content with emojis in the database
    log_entry = NotificationLog(
        user_id=user_id,
        notification_type=notification_type,
        content=content,
        status="sent"  # Mocking success since live integrations are skipped for now
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return log_entry
