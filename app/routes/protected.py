from flask import Blueprint, jsonify
from flask_login import login_required, current_user

protected_bp = Blueprint('protected_bp', __name__)

@protected_bp.route('/protected', methods=['GET'])
@login_required
def protected():
    return jsonify(message=f'You are logged in as user {current_user.id}'), 200
