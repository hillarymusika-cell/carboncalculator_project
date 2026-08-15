from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from init import db
from models import History
from calculator import (
    calculate_from_inputs,
    calculate_single,
    list_factors,
    InvalidUnitsError,
)

views = Blueprint("views", __name__)


def _payload_from_request():
    """Prefer JSON body; fall back to form fields."""
    if request.is_json:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    return request.form.to_dict() if request.form else {}


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


# ---------------------------------------------------------------------------
# Real-time calculation APIs (no persistence)
# ---------------------------------------------------------------------------

@views.route("/api/factors", methods=["GET"])
def api_factors():
    """Return emission factor tables for UI tooltips / docs."""
    return jsonify(list_factors()), 200


@views.route("/api/calculate", methods=["POST"])
def api_calculate():
    """
    Real-time full footprint calculation.

    Body: JSON or form fields (same shape as /submit).
    Does NOT require login and does NOT write to the database.
    """
    payload = _payload_from_request()
    try:
        result = calculate_from_inputs(payload)
    except InvalidUnitsError as e:
        return jsonify({"ok": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("calculate failed")
        return jsonify({"ok": False, "message": "Calculation failed."}), 500

    return jsonify({"ok": True, **result}), 200


@views.route("/api/calculate/single", methods=["POST"])
def api_calculate_single():
    """
    Real-time single-source calculation.

    JSON body example:
      { "source": "transport", "units": 5, "transport_type": "car" }
      { "source": "fuel", "units": 100, "fuel_type": "electricity" }
      { "source": "trees", "units": 10 }
    """
    payload = _payload_from_request()
    source = payload.get("source") or payload.get("type") or ""
    units = payload.get("units", payload.get("value", 0))
    try:
        result = calculate_single(
            source,
            units,
            transport_type=payload.get("transport_type") or payload.get("transport") or "car",
            fuel_type=payload.get("fuel_type") or payload.get("fuel") or "gas",
        )
    except InvalidUnitsError as e:
        return jsonify({"ok": False, "message": str(e)}), 400
    except Exception:
        current_app.logger.exception("calculate_single failed")
        return jsonify({"ok": False, "message": "Calculation failed."}), 500

    return jsonify({"ok": True, **result}), 200


# ---------------------------------------------------------------------------
# Persist assessment (login required)
# ---------------------------------------------------------------------------

@views.route("/submit", methods=["POST"])
@login_required
def submit():
    payload = _payload_from_request()
    try:
        result = calculate_from_inputs(payload)
    except InvalidUnitsError as e:
        return jsonify({"message": str(e)}), 400

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
    return render_template(
        "dashboard.html",
        user=current_user,
        latest_data=latest,
        now=datetime.utcnow(),
    )


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
