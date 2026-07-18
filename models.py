from init import db
from flask_login import UserMixin
from sqlalchemy import func, JSON


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(145), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    user_name = db.Column(db.String(150), nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_online = db.Column(db.Boolean, nullable=False, default=False)
    logs = db.relationship("Log", backref="user", cascade="all, delete-orphan")
    history = db.relationship("History", backref="user", cascade="all, delete-orphan")


class History(db.Model):
    __tablename__ = "history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    search = db.Column(JSON)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    login_time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    logout_time = db.Column(db.DateTime)
