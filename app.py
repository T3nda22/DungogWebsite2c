from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cebu-rental-hub-secret-key-2023'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentalhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    """Save uploaded image and create thumbnail"""
    if file and allowed_file(file.filename):
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Add timestamp to make filename unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            image = Image.open(file)

            max_size = (1200, 1200)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            image.save(filepath, 'JPEG', quality=85)

            thumbnail_size = (300, 300)
            thumbnail = image.copy()
            thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

            thumb_filename = f"thumb_{filename}"
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
            thumbnail.save(thumb_path, 'JPEG', quality=80)

            return filename
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
    return None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RentalItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_filename = db.Column(db.String(300))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)

    owner = db.relationship('User', backref=db.backref('items', lazy=True))

    @property
    def image_url(self):
        if self.image_filename:
            return url_for('uploaded_file', filename=self.image_filename)
        return url_for('static', filename='images/default-item.jpg')

    @property
    def thumbnail_url(self):
        if self.image_filename:
            return url_for('uploaded_file', filename=f"thumb_{self.image_filename}")
        return url_for('static', filename='images/default-item.jpg')


class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('rental_item.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('RentalItem', backref=db.backref('rentals', lazy=True))
    renter = db.relationship('User', backref=db.backref('rentals', lazy=True))


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rental = db.relationship('Rental', backref=db.backref('payment', uselist=False))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
    featured_items = RentalItem.query.filter_by(is_available=True).order_by(db.func.random()).limit(6).all()
    return render_template('index.html', featured_items=featured_items)


@app.route('/items')
def items():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    location = request.args.get('location', '')

    query = RentalItem.query.filter_by(is_available=True)

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(RentalItem.title.ilike(f'%{search}%'))
    if location:
        query = query.filter(RentalItem.location.ilike(f'%{location}%'))

    items = query.all()
    categories = db.session.query(RentalItem.category).distinct().all()
    categories = [cat[0] for cat in categories]

    return render_template('items.html', items=items, search=search, category=category, location=location,
                           categories=categories)


@app.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        location = request.form['location']
        category = request.form['category']

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_filename = save_image(file)
                if not image_filename:
                    flash('Invalid image file. Please upload PNG, JPG, or GIF.', 'error')
                    return render_template('add_item.html')

        new_item = RentalItem(
            title=title,
            description=description,
            price=price,
            location=location,
            category=category,
            image_filename=image_filename,
            owner_id=current_user.id
        )

        db.session.add(new_item)
        db.session.commit()

        flash('Item listed successfully!', 'success')
        return redirect(url_for('items'))

    return render_template('add_item.html')


@app.route('/delete-item/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    item = RentalItem.query.get_or_404(item_id)

    if item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    if item.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], f"thumb_{item.image_filename}")

        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as e:
            print(f"Error deleting image files: {e}")

    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Item deleted successfully'})


@app.route('/dashboard')
@login_required
def dashboard():
    total_rentals = Rental.query.filter_by(renter_id=current_user.id).count()
    active_bookings = Rental.query.filter(
        Rental.renter_id == current_user.id,
        Rental.status.in_(['approved', 'rented'])
    ).count()

    completed_payments = Payment.query.join(Rental).filter(
        Rental.renter_id == current_user.id,
        Payment.status == 'completed'
    ).count()

    my_items = RentalItem.query.filter_by(owner_id=current_user.id).count()
    recent_rentals = Rental.query.filter_by(renter_id=current_user.id).order_by(Rental.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_rentals=total_rentals,
                           active_bookings=active_bookings,
                           completed_payments=completed_payments,
                           my_items=my_items,
                           recent_rentals=recent_rentals)


@app.route('/rent/<int:item_id>', methods=['GET', 'POST'])
@login_required
def rent_item(item_id):
    item = RentalItem.query.get_or_404(item_id)

    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')

        days = (end_date - start_date).days
        if days < 1:
            flash('Rental period must be at least 1 day', 'error')
            return redirect(url_for('rent_item', item_id=item_id))

        total_price = item.price * days

        new_rental = Rental(
            item_id=item_id,
            renter_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )

        db.session.add(new_rental)
        db.session.commit()

        flash('Rental request submitted successfully! Please proceed to payment.', 'success')
        return redirect(url_for('payment', rental_id=new_rental.id))

    return render_template('rent_item.html', item=item)


@app.route('/my-rentals')
@login_required
def my_rentals():
    rentals = Rental.query.filter_by(renter_id=current_user.id).order_by(Rental.created_at.desc()).all()
    return render_template('my_rentals.html', rentals=rentals)


@app.route('/my-listings')
@login_required
def my_listings():
    items = RentalItem.query.filter_by(owner_id=current_user.id).order_by(RentalItem.created_at.desc()).all()
    return render_template('my_listings.html', items=items)


@app.route('/payment/<int:rental_id>', methods=['GET', 'POST'])
@login_required
def payment(rental_id):
    rental = Rental.query.get_or_404(rental_id)

    if rental.renter_id != current_user.id:
        flash('You are not authorized to view this payment.', 'error')
        return redirect(url_for('my_rentals'))

    if request.method == 'POST':
        method = request.form['payment_method']

        new_payment = Payment(
            rental_id=rental_id,
            amount=rental.total_price,
            method=method,
            status='completed',
            transaction_id=f'TXN-{rental_id}-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
        )

        rental.status = 'approved'

        db.session.add(new_payment)
        db.session.commit()

        flash('Payment completed successfully! Your rental has been approved.', 'success')
        return redirect(url_for('my_rentals'))

    return render_template('payment.html', rental=rental)


@app.route('/update-rental-status/<int:rental_id>/<status>')
@login_required
def update_rental_status(rental_id, status):
    rental = Rental.query.get_or_404(rental_id)

    if rental.item.owner_id != current_user.id:
        flash('You are not authorized to update this rental.', 'error')
        return redirect(url_for('dashboard'))

    rental.status = status
    db.session.commit()

    flash(f'Rental status updated to {status}.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form.get('phone', '')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            phone=phone
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)