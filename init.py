import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()
oauth = OAuth()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_database_url(url):
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production."
            )
        secret_key = os.urandom(24).hex()
    app.config["SECRET_KEY"] = secret_key

    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    database_url = _normalize_database_url(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable must be set to a postgresql:// URI."
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    db.init_app(app)
    csrf.init_app(app)

    # --- Google OAuth setup ---
    # Registered here (once) on the shared `oauth` instance so that every
    # module that does `from init import oauth` gets the same, fully
    # configured client. Previously auth.py created a second, separate
    # OAuth() instance and registered "google" on that one instead — the
    # instance actually wired into the Flask app via init_app() never had
    # a google client at all.
    oauth.init_app(app)

    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not google_client_id or not google_client_secret:
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment "
                "variables must be set in production."
            )
        print(
            "WARNING: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not set. "
            "Google sign-in will fail with 'invalid_client' until these "
            "are configured."
        )

    oauth.register(
        name="google",
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from auth import auth
    from views import views

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(views, url_prefix="/")

    with app.app_context():
        create_db(app)

    return app


def create_db(app):
    db.create_all()
    print("Database tables ensured on Postgres.")
