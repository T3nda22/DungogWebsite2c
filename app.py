from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from models import db, User
from config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.static_folder, 'uploads', 'items'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'proofs'), exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.owner_routes import owner_bp
    from routes.renter_routes import renter_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(renter_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'owner':
            return redirect(url_for('owner.dashboard'))
        elif current_user.role == 'renter':
            return redirect(url_for('renter.dashboard'))
        else:
            flash('Unknown user role.', 'danger')
            return redirect(url_for('auth.logout'))

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
