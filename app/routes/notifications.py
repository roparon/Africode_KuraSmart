from flask import Blueprint, render_template, request, redirect, flash, url_for, abort
from app.models import Notification, User, db
from app.forms import NotificationForm
from app.utils.email import send_email_async
from flask_login import login_required, current_user

notifications_bp = Blueprint('notifications', __name__, template_folder='templates')

@notifications_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def manage_notifications():
    if not current_user.is_superadmin:
        abort(403)

    form = NotificationForm()

    try:
        if form.validate_on_submit():
            notif = Notification(
                subject=form.title.data,
                message=form.message.data,
                send_email=form.send_email.data
            )
            db.session.add(notif)
            db.session.commit()

            if notif.send_email:
                users = User.query.all()
                for user in users:
                    try:
                        send_email_async(user.email, notif.subject, notif.message)
                    except Exception as email_err:
                        flash(f"Failed to send email to {user.email}: {email_err}", "warning")

            flash('✅ Notification sent successfully!', 'success')
            return redirect(url_for('notifications.manage_notifications'))

        notifs = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('admin/notifications.html', form=form, notifications=notifs)

    except Exception as e:
        db.session.rollback()
        flash(f"Error sending notification: {e}", "danger")
        return redirect(url_for('notifications.manage_notifications'))
