from init import db
from flask_login import UserMixin
from sqlalchemy import func
import json


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(145), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=True)
    user_name = db.Column(db.String(150), nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_online = db.Column(db.Boolean, nullable=False, default=False)

    google_id = db.Column(db.String(255), unique=True, nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)

    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expiry = db.Column(db.DateTime(timezone=True), nullable=True)

    logs = db.relationship("Log", backref="user", cascade="all, delete-orphan")
    history = db.relationship("History", backref="user", cascade="all, delete-orphan")

    @classmethod
    def get_or_create_from_google(cls, google_id, email, name):
        user = cls.query.filter_by(google_id=google_id).first()
        if user:
            return user

        user = cls.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.oauth_provider = 'google'
            db.session.commit()
            return user

        new_user = cls(
            email=email,
            user_name=name or email.split('@')[0],
            google_id=google_id,
            oauth_provider='google',
            is_online=True,
            password=None
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user


class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    _search = db.Column("search", db.Text)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @property
    def search(self):
        if self._search is None:
            return None
        try:
            return json.loads(self._search)
        except (json.JSONDecodeError, TypeError):
            return None

    @search.setter
    def search(self, value):
        self._search = json.dumps(value) if value is not None else None


class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    login_time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    logout_time = db.Column(db.DateTime)
