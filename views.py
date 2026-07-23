from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from init import db
from models import History
from calculator import (
    Transport,
    EnhancedFuel,
    Buildings,
    Trees,
    Adults,
    Livestock,
    Pets,
    CarbonFootprint,
    InvalidUnitsError,
)

views = Blueprint("views", __name__)


def _to_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@views.route("/healthz")
def healthz():
    backend = "postgres" if current_app.config.get("IS_POSTGRES") else "sqlite"
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": backend}), 200
    except SQLAlchemyError as e:
        current_app.logger.error(f"Health check DB failure ({backend}): {e}")
        return jsonify({"status": "error", "database": backend}), 503


@views.route("/")
@views.route("/home")
def home():
    return render_template("home.html", user=current_user)


@views.route("/about")
def about():
    return render_template("about.html", user=current_user)


@views.route("/submit", methods=["POST"])
@login_required
def submit():
    form = request.form

    transport_type = form.get("transport") or "other"
    frequency_raw = form.get("frequency")
    frequency = (
        _to_number(form.get("frequency_custom"), default=1)
        if frequency_raw == "multiple"
        else _to_number(frequency_raw, default=1)
    )

    fuel_type = form.get("fuel") or "electricity"
    energy_expense = _to_number(form.get("energy_expense"), default=0)

    house_no = _to_number(form.get("house_no"), default=0)
    trees = _to_number(form.get("trees"), default=0)
    adults = _to_number(form.get("adults"), default=0)
    livestock = _to_number(form.get("livestock"), default=0)
    pets = _to_number(form.get("pets"), default=0)

    calc = CarbonFootprint()
    try:
        calc.add(Transport(frequency, transport_type=transport_type))
        if energy_expense > 0:
            calc.add(EnhancedFuel(energy_expense, fuel_type=fuel_type))
        if house_no > 0:
            calc.add(Buildings(house_no))
        if trees > 0:
            calc.add(Trees(trees))
        if adults > 0:
            calc.add(Adults(adults))
        if livestock > 0:
            calc.add(Livestock(livestock))
        if pets > 0:
            calc.add(Pets(pets))
    except InvalidUnitsError as e:
        return jsonify({"message": str(e)}), 400

    result = {
        "total_kg_co2e": calc.total(),
        "breakdown": calc.breakdown(),
        "inputs": {
            "transport": transport_type,
            "frequency": frequency,
            "fuel": fuel_type,
            "energy_expense": energy_expense,
            "house_no": house_no,
            "trees": trees,
            "adults": adults,
            "livestock": livestock,
            "pets": pets,
        },
    }

    entry = History(user_id=current_user.id)
    entry.search = result

    try:
        db.session.add(entry)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Could not save your results. Please try again."}), 500

    return jsonify(result), 200


@views.route("/dashboard")
@login_required
def dashboard():
    latest = (
        History.query.filter_by(user_id=current_user.id)
        .order_by(History.time.desc())
        .first()
    )
    return render_template("dashboard.html", user=current_user, latest_data=latest, now=datetime.utcnow())


@views.route("/history")
@login_required
def history():
    entries = (
        History.query.filter_by(user_id=current_user.id)
        .order_by(History.time.desc())
        .limit(20)
        .all()
    )
    return jsonify(
        {
            "history": [
                {"time": e.time.isoformat() if e.time else None, "search": e.search}
                for e in entries
            ]
        }
    )
