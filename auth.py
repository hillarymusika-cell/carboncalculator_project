import os
from flask import render_template, Blueprint, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from authlib.integrations.flask_client import OAuth

from validate_password import v_password
from models import User
from init import db

auth = Blueprint("auth", __name__)

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=current_user)

    email = (request.form.get("login-email") or "").strip().lower()
    password = request.form.get("login-password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required.", "redirect": "/auth/login"}), 400

    try:
        existing_user = User.query.filter_by(email=email).first()
    except SQLAlchemyError:
        return jsonify({"message": "Something went wrong. Please try again.", "redirect": "/auth/login"}), 500

    if not existing_user:
        return jsonify({"message": f"No account found for {email}.", "redirect": "/auth/login"}), 404

    if not existing_user.password or not check_password_hash(existing_user.password, password):
        return jsonify({"message": "Incorrect password.", "redirect": "/auth/login"}), 401

    existing_user.is_online = True
    login_user(existing_user, remember=True)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

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

    email = (request.form.get("login-email") or "").strip()
    password = request.form.get("login-password") or ""
    confirm_password = request.form.get("confirm-password")

    if not email:
        return jsonify({"message": "Email is required", "redirect": "/auth/signup"}), 400
    if not password:
        return jsonify({"message": "Password is required", "redirect": "/auth/signup"}), 400
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match! ", "redirect": "/auth/signup"}), 400

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
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        return jsonify({"message": "Account created successfully!", "redirect": "/"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Could not create account. Please try again.", "redirect": "/auth/signup"}), 500


@auth.route("/forgot", methods=["GET", "POST"])
def forgot():
    return render_template("recovery.html")


@auth.route("/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route("/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")
    except Exception:
        return jsonify({"message": "Google login failed. Please try again.", "redirect": "/auth/login"}), 400

    if not user_info or not user_info.get("email"):
        return jsonify({"message": "Could not retrieve account info from Google.", "redirect": "/auth/login"}), 400

    email = user_info["email"].strip().lower()

    try:
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            existing_user.is_online = True
            login_user(existing_user, remember=True)
        else:
            new_user = User(
                email=email,
                user_name=user_info.get("name", email),
                password=None,
                is_online=True,
            )
            db.session.add(new_user)
            login_user(new_user, remember=True)

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Something went wrong creating your account.", "redirect": "/auth/login"}), 500

    return redirect("/home")
