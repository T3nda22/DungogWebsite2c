from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Item, User
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    pending_items = Item.query.filter_by(status='pending').count()
    total_items = Item.query.count()
    total_users = User.query.count()
    recent_items = Item.query.order_by(Item.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           pending_items=pending_items,
                           total_items=total_items,
                           total_users=total_users,
                           recent_items=recent_items)


@admin_bp.route('/items/pending')
@login_required
@admin_required
def pending_items():
    items = Item.query.filter_by(status='pending').all()
    return render_template('admin/pending_items.html', items=items)


@admin_bp.route('/items/<int:item_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_item(item_id):
    item = Item.query.get_or_404(item_id)
    item.status = 'approved'
    db.session.commit()
    flash('Item approved successfully!', 'success')
    return redirect(url_for('admin.pending_items'))


@admin_bp.route('/items/<int:item_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_item(item_id):
    item = Item.query.get_or_404(item_id)
    item.status = 'rejected'
    db.session.commit()
    flash('Item rejected.', 'info')
    return redirect(url_for('admin.pending_items'))