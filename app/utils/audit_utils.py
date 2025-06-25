from app.models import AuditLog, db
from flask_login import current_user

def log_action(action, target_type=None, target_id=None, details=None):
    if not current_user.is_authenticated:
        return

    log = AuditLog(
        user_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()
