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

DATABASE_NAME = "calc.db"
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

    db_path = os.path.join(BASE_DIR, "instance", DATABASE_NAME)
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    database_url = _normalize_database_url(os.environ.get("DATABASE_URL"))
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{db_path}" 
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
    app.config["IS_POSTGRES"] = app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql")

    if app.config["IS_POSTGRES"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
        }

    db.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
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
    if app.config["IS_POSTGRES"]:
        db.create_all()
        return

    instance_dir = os.path.join(BASE_DIR, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    db_file = os.path.join(instance_dir, DATABASE_NAME)
    if not os.path.exists(db_file):
        db.create_all()
        print(f"Created new database at {db_file}")
