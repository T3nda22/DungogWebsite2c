from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Item, Rental
from datetime import datetime

renter_bp = Blueprint('renter', __name__, url_prefix='/renter')


@renter_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'renter':
        flash('Access denied. Renter privileges required.', 'danger')
        return redirect(url_for('dashboard'))

    active_rentals = Rental.query.filter_by(renter_id=current_user.id).filter(
        Rental.status.in_(['confirmed', 'pending'])
    ).count()
    completed_rentals = Rental.query.filter_by(renter_id=current_user.id, status='completed').count()
    recent_rentals = Rental.query.filter_by(renter_id=current_user.id).order_by(
        Rental.created_at.desc()
    ).limit(5).all()

    return render_template('renter/dashboard.html',
                           active_rentals=active_rentals,
                           completed_rentals=completed_rentals,
                           recent_rentals=recent_rentals)


@renter_bp.route('/browse')
@login_required
def browse():
    items = Item.query.filter_by(status='approved', is_available=True).all()
    return render_template('renter/browse.html', items=items)



@renter_bp.route('/rent/<int:item_id>', methods=['POST'])
@login_required
def rent_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.status != 'approved' or not item.is_available:
        flash('This item is not available for rent.', 'danger')
        return redirect(url_for('renter.browse'))

    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')

    if start_date >= end_date:
        flash('End date must be after start date.', 'danger')
        return redirect(url_for('renter.browse'))

    days = (end_date - start_date).days
    total_price = days * item.price_per_day

    rental = Rental(
        item_id=item.id,
        renter_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status='pending'
    )

    db.session.add(rental)
    db.session.commit()

    flash('Rental request submitted successfully!', 'success')
    return redirect(url_for('renter.dashboard'))


@renter_bp.route('/my-bookings')
@login_required
def my_bookings():
    # Sample data - replace with your actual database queries
    bookings = [
        {
            'id': 1,
            'property': {
                'title': 'Luxury Beach Villa',
                'location': 'Miami Beach, FL',
                'image_url': '/static/images/beach-villa.jpg'
            },
            'check_in_date': datetime(2025, 10, 20),
            'check_out_date': datetime(2025, 10, 25),
            'total_price': 1200.00,
            'status': 'confirmed',
            'guests_count': 2
        },
        {
            'id': 2,
            'property': {
                'title': 'Cozy Mountain Cabin',
                'location': 'Aspen, CO',
                'image_url': '/static/images/mountain-cabin.jpg'
            },
            'check_in_date': datetime(2025, 11, 15),
            'check_out_date': datetime(2025, 11, 20),
            'total_price': 800.00,
            'status': 'pending',
            'guests_count': 4
        }
    ]


    upcoming_count = len([b for b in bookings if b['status'] in ['confirmed', 'pending']])
    active_count = len([b for b in bookings if b['status'] == 'active'])
    completed_count = len([b for b in bookings if b['status'] == 'completed'])

    return render_template('renter/my_bookings.html',
                           bookings=bookings,
                           upcoming_count=upcoming_count,
                           active_count=active_count,
                           completed_count=completed_count)


@renter_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    # Add your cancellation logic here
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('renter.my_bookings'))


@renter_bp.route('/favorites')
@login_required
def favorites():
    # Sample data - replace with your actual database queries
    favorites = [
        {
            'id': 1,
            'property': {
                'id': 101,
                'title': 'Luxury Beach Villa',
                'location': 'Miami Beach, FL',
                'image_url': '/static/images/beach-villa.jpg',
                'price_per_night': 299,
                'original_price': 349,
                'discount': 15,
                'rating': 4.8,
                'guests': 6,
                'bedrooms': 3,
                'bathrooms': 2,
                'superhost': True,
                'available': True
            },
            'date_added': datetime(2025, 10, 15)
        },
        {
            'id': 2,
            'property': {
                'id': 102,
                'title': 'Cozy Mountain Cabin',
                'location': 'Aspen, CO',
                'image_url': '/static/images/mountain-cabin.jpg',
                'price_per_night': 189,
                'original_price': None,
                'discount': None,
                'rating': 4.6,
                'guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'superhost': False,
                'available': True
            },
            'date_added': datetime(2025, 10, 10)
        },
        {
            'id': 3,
            'property': {
                'id': 103,
                'title': 'Downtown Luxury Apartment',
                'location': 'New York, NY',
                'image_url': '/static/images/downtown-apartment.jpg',
                'price_per_night': 159,
                'original_price': 199,
                'discount': 20,
                'rating': 4.9,
                'guests': 2,
                'bedrooms': 1,
                'bathrooms': 1,
                'superhost': True,
                'available': False
            },
            'date_added': datetime(2025, 10, 5)
        }
    ]

    # Calculate counts for stats
    available_count = len([f for f in favorites if f['property']['available']])
    discount_count = len([f for f in favorites if f['property']['discount']])
    superhost_count = len([f for f in favorites if f['property']['superhost']])

    return render_template('renter/favorites.html',
                           favorites=favorites,
                           available_count=available_count,
                           discount_count=discount_count,
                           superhost_count=superhost_count)


@renter_bp.route('/profile')
@login_required
def profile():
    return render_template('renter/profile.html')