from flask import Blueprint, render_template, request, redirect, flash, url_for
from app.models import Notification, db
from app.forms import NotificationForm
from app.utils.email import send_email_async
from flask_login import login_required, current_user

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def manage_notifications():
    form = NotificationForm()
    if form.validate_on_submit():
        notif = Notification(
            title=form.title.data,
            message=form.message.data,
            send_email=form.send_email.data
        )
        db.session.add(notif)
        db.session.commit()

        if notif.send_email:
            from app.models import User
            for user in User.query.all():
                send_email_async(user.email, notif.title, notif.message)

        flash('Notification sent successfully!', 'success')
        return redirect(url_for('notifications.manage_notifications'))

    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', form=form, notifications=notifications)


@notifications_bp.route('/admin/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        flash('Notification not found.', 'error')
        return redirect(url_for('notifications.manage_notifications'))

    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted successfully!', 'success')
    return redirect(url_for('notifications.manage_notifications'))