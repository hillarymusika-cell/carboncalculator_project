from flask import render_template, Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from calculator import (
    Electricity,
    Fuel,
    Diet,
    Trees,
    Buildings,
    CarbonFootprint,
    InvalidUnitsError,
)
from models import History
from init import db

views = Blueprint("views", __name__)


@views.route("/", methods=["GET"])
@login_required
def home():
    return render_template("home.html",user=current_user)


@views.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@views.route("/submit", methods=["POST"])
@login_required
def submit():
    data = request.get_json(silent=True) or request.form

    try:
        footprint = CarbonFootprint()
        if "electricity" in data:
            footprint.add(Electricity(data.get("electricity")))
        if "fuel" in data:
            footprint.add(Fuel(data.get("fuel")))
        if "transport" in data:
            footprint.add(Fuel(data.get("transport")))
        if "other-transport" in data:
            footprint.add(Fuel(data.get("other-transport")))
        if "livestock" in data:
            footprint.add(Diet(data.get("livestock")))
        if "pets" in data:
            footprint.add(Diet(data.get("pets")))
        if "adults" in data:
            footprint.add(Diet(data.get("adults")))
        if "trees" in data:
            footprint.add(Trees(data.get("trees")))
        if "house_no" in data:
            footprint.add(Buildings(data.get("house_no")))                                               
    except InvalidUnitsError as e:
        return jsonify({"message": str(e)}), 400

    if not footprint.sources:
        return jsonify({"message": "No recognised inputs were submitted."}), 400

    result = {"total_kg_co2e": footprint.total(), "breakdown": footprint.breakdown()}

    try:
        db.session.add(History(user_id=current_user.id, search=result))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

    return jsonify(result)
    
@views.route("/dashboard",methods=["GET","POST"])
@login_required
def dashboard():
    if request.method == "GET":
        return render_template("dashboard.html",now=datetime.utcnow(),user=current_user)