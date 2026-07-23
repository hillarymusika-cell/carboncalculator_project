
from flask import render_template, Blueprint, request, jsonify, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from authlib.integrations.flask_client import OAuth
import logging
import time
import secrets
import hashlib
from datetime import datetime, timedelta
import os

from validate_password import v_password
from models import User
from init import db

auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

oauth = OAuth(current_app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

rate_limit_store = {}

def rate_limit(key: str, limit: int = 5, window: int = 300) -> bool:
    now = time.time()
    record = rate_limit_store.get(key)
    if record is None:
        rate_limit_store[key] = [now]
        return False
    record = [t for t in record if now - t < window]
    if len(record) >= limit:
        return True
    record.append(now)
    rate_limit_store[key] = record
    return False

@auth.route("/login/google")
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route("/callback/google")
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token)
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return jsonify({"message": "Authentication with Google failed.", "redirect": "/auth/login"}), 400

    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name', email.split('@')[0])

    if not google_id or not email:
        return jsonify({"message": "Missing required user information from Google.", "redirect": "/auth/login"}), 400

    try:
        user = User.get_or_create_from_google(google_id, email, name)
        user.is_online = True
        db.session.commit()
        login_user(user, remember=True)
        logger.info(f"Google OAuth login: {email}")
        return redirect(url_for('views.home'))  
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during Google OAuth: {e}")
        return jsonify({"message": "Could not sign in. Please try again.", "redirect": "/auth/login"}), 500


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=current_user)

    email = (request.form.get("login-email") or "").strip().lower()
    password = request.form.get("login-password") or ""
    remember = request.form.get("remember") == "on"

    if not email or not password:
        return jsonify({"message": "Email and password are required.", "redirect": "/auth/login"}), 400

    client_ip = request.remote_addr
    if rate_limit(f"login_{client_ip}"):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        return jsonify({"message": "Too many login attempts. Please try again later.", "redirect": "/auth/login"}), 429

    try:
        user = User.query.filter_by(email=email).first()
    except OperationalError:
        logger.error("Database unavailable during login lookup", exc_info=True)
        return jsonify({"message": "Service temporarily unavailable. Please try again in a moment.", "redirect": "/auth/login"}), 503
    except SQLAlchemyError:
        logger.error("Database error during login lookup", exc_info=True)
        return jsonify({"message": "Something went wrong. Please try again.", "redirect": "/auth/login"}), 500

    if not user or not user.password or not check_password_hash(user.password, password):
        if user and user.password: 
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                logger.warning(f"Account {user.email} locked due to too many failed logins")
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
        time.sleep(1)
        return jsonify({"message": "Invalid email or password.", "redirect": "/auth/login"}), 401

    if user.is_locked:
        return jsonify({"message": "Account is locked due to multiple failed attempts. Please reset your password.", "redirect": "/auth/login"}), 403

    user.failed_login_attempts = 0
    user.is_locked = False
    user.is_online = True
    login_user(user, remember=remember)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.error("Failed to commit user online status", exc_info=True)
        return jsonify({"message": "Login failed. Please try again.", "redirect": "/auth/login"}), 500

    logger.info(f"User {user.email} logged in from {client_ip}")
    return jsonify({"message": "Login successful", "redirect": "/home"})


@auth.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    current_user.is_online = False
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
    logout_user()
    return jsonify({"message": "Logged out", "redirect": "/auth/login"})


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("sign_up.html", user=current_user)

    client_ip = request.remote_addr
    if rate_limit(f"signup_{client_ip}"):
        logger.warning(f"Rate limit exceeded for signup from {client_ip}")
        return jsonify({"message": "Too many signup attempts. Please try again later.", "redirect": "/auth/signup"}), 429

    email = (request.form.get("login-email") or "").strip()
    password = request.form.get("login-password") or ""
    confirm_password = request.form.get("confirm-password") or ""

    if not email:
        return jsonify({"message": "Email is required", "redirect": "/auth/signup"}), 400
    if not password:
        return jsonify({"message": "Password is required", "redirect": "/auth/signup"}), 400
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match!", "redirect": "/auth/signup"}), 400

    try:
        valid = validate_email(email, check_deliverability=False)
        email = valid.normalized
    except EmailNotValidError as e:
        return jsonify({"message": str(e), "redirect": "/auth/signup"}), 400

    password_ok, password_message = v_password(password)
    if not password_ok:
        return jsonify({"message": password_message, "redirect": "/auth/signup"}), 400

    try:
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "An account with that email already exists.", "redirect": "/auth/signup"}), 409

        new_user = User(
            email=email,
            user_name=email,
            password=generate_password_hash(password),
            is_online=True,
            failed_login_attempts=0,
            is_locked=False,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        logger.info(f"New user registered: {email} from {client_ip}")
        return jsonify({"message": "Account created successfully!", "redirect": "/"}), 200
    except OperationalError:
        db.session.rollback()
        logger.error("Database unavailable during signup", exc_info=True)
        return jsonify({"message": "Service temporarily unavailable. Please try again in a moment.", "redirect": "/auth/signup"}), 503
    except SQLAlchemyError:
        db.session.rollback()
        logger.error("Signup database error", exc_info=True)
        return jsonify({"message": "Could not create account. Please try again.", "redirect": "/auth/signup"}), 500


@auth.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "GET":
        return render_template("recovery.html")

    email = (request.form.get("email") or "").strip().lower()
    if not email:
        return jsonify({"message": "Email is required."}), 400

    client_ip = request.remote_addr
    if rate_limit(f"reset_{client_ip}", limit=3, window=3600):
        return jsonify({"message": "Too many reset requests. Please try again later."}), 429

    try:
        user = User.query.filter_by(email=email).first()
    except SQLAlchemyError:
        logger.error("Database error during password reset lookup", exc_info=True)
        return jsonify({"message": "Something went wrong. Please try again."}), 500

    if not user:
        time.sleep(1)
        return jsonify({"message": "If that email exists, we have sent a reset link."}), 200

    if user.oauth_provider:
        return jsonify({"message": "This account uses Google Sign-In. Please log in with Google."}), 400

    token = secrets.token_urlsafe(32)
    user.reset_token = hashlib.sha256(token.encode()).hexdigest()
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Could not process reset. Please try again."}), 500

    logger.info(f"Password reset token generated for {email}")
    return jsonify({"message": "If that email exists, we have sent a reset link."}), 200