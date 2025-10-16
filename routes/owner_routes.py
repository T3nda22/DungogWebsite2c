from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Item, Rental
import os
from datetime import datetime

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


@owner_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'owner':
        flash('Access denied. Owner privileges required.', 'danger')
        return redirect(url_for('dashboard'))

    total_items = Item.query.filter_by(owner_id=current_user.id).count()
    approved_items = Item.query.filter_by(owner_id=current_user.id, status='approved').count()
    pending_items = Item.query.filter_by(owner_id=current_user.id, status='pending').count()
    active_rentals = Rental.query.join(Item).filter(
        Item.owner_id == current_user.id,
        Rental.status.in_(['confirmed', 'pending'])
    ).count()

    return render_template('owner/dashboard.html',
                           total_items=total_items,
                           approved_items=approved_items,
                           pending_items=pending_items,
                           active_rentals=active_rentals)

@owner_bp.route('/rentals')
@login_required
def view_rentals():
    if current_user.role != 'owner':
        flash('Access denied. Owner privileges required.', 'danger')
        return redirect(url_for('dashboard'))

    rentals = Rental.query.join(Item).filter(Item.owner_id == current_user.id).all()
    return render_template('owner/view_rentals.html', rentals=rentals)



@owner_bp.route('/items')
@login_required
def manage_items():
    items = Item.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/manage_items.html', items=items)


@owner_bp.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price_per_day = float(request.form.get('price_per_day'))
        location = request.form.get('location')

        item = Item(
            name=name,
            description=description,
            category=category,
            price_per_day=price_per_day,
            location=location,
            owner_id=current_user.id
        )

        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
                image_path = os.path.join('static/uploads/items', filename)
                image.save(image_path)
                item.image_path = image_path

        # Handle proof upload
        if 'proof' in request.files:
            proof = request.files['proof']
            if proof and allowed_file(proof.filename):
                filename = secure_filename(f"proof_{datetime.now().timestamp()}_{proof.filename}")
                proof_path = os.path.join('static/uploads/proofs', filename)
                proof.save(proof_path)
                item.proof_path = proof_path

        db.session.add(item)
        db.session.commit()

        flash('Item added successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('owner.manage_items'))

    return render_template('owner/add_item.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}