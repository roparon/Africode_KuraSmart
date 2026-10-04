from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, logout_user
from datetime import datetime
from zoneinfo import ZoneInfo



main_bp = Blueprint('main', __name__)

@main_bp.route('/api/cron/reminders', methods=['GET'])
def cron_reminders():
    cron_secret = current_app.config.get('CRON_SECRET')

    if not cron_secret:
        return jsonify({"error": "Cron secret is not configured"}), 500

    if request.headers.get('Authorization') != f'Bearer {cron_secret}':
        return jsonify({"error": "Unauthorized"}), 401

    from app.tasks.reminders import send_reminders

    send_reminders()

    return jsonify({"ok": True, "message": "Reminders processed"}), 200


@main_bp.route('/')
def index():
    now_nairobi = datetime.now(ZoneInfo("Africa/Nairobi"))
    if current_user.is_authenticated:
        name = current_user.full_name
        logout_user()
        flash(f'{name}, you have been logged out automatically.', 'info')
        return redirect(url_for('main.index'))
    return render_template('index.html', now=now_nairobi)


