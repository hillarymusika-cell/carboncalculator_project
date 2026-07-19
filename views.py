from flask import render_template, Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from calculator import (
    Electricity,
    Fuel,
    Transport,
    EnhancedFuel,
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
        
        # Transport - frequency or expense (in km per week)
        if "frequency" in data and data.get("frequency"):
            frequency = data.get("frequency")
            if frequency == "multiple" and "frequency_custom" in data:
                frequency = float(data.get("frequency_custom", 0))
            elif frequency != "multiple":
                frequency = float(frequency)
            else:
                frequency = 0
            
            if frequency > 0:
                # Assume average ~50km per use
                km_per_week = frequency * 50
                transport_type = data.get("transport", "car")
                footprint.add(Transport(km_per_week, transport_type=transport_type))
        
        # Alternative: Transport expense in currency (fallback)
        elif "transport_expense" in data and data.get("transport_expense"):
            # Assume £1 = 0.5kg CO2e average
            expense = float(data.get("transport_expense", 0))
            footprint.add(Transport(expense * 0.5, transport_type="car"))
        
        # Fuel/Energy - handle based on fuel type
        if "fuel" in data and data.get("fuel"):
            fuel_type = data.get("fuel")
            if "energy_expense" in data and data.get("energy_expense"):
                energy_amount = float(data.get("energy_expense", 0))
                if fuel_type == "electricity":
                    footprint.add(Electricity(energy_amount))
                else:
                    footprint.add(EnhancedFuel(energy_amount, fuel_type=fuel_type))
        
        # Housing and lifestyle
        if "livestock" in data and data.get("livestock"):
            footprint.add(Diet(data.get("livestock")))
        if "pets" in data and data.get("pets"):
            footprint.add(Diet(data.get("pets")))
        if "adults" in data and data.get("adults"):
            footprint.add(Diet(data.get("adults")))
        if "trees" in data and data.get("trees"):
            footprint.add(Trees(data.get("trees")))
        if "house_no" in data and data.get("house_no"):
            footprint.add(Buildings(data.get("house_no")))                                               
    except (InvalidUnitsError, ValueError) as e:
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
    try:
        history= History.query.filter_by(user_id=current_user.id).order_by(History.time.desc()).first()
    except SQLAlchemyError:
        return jsonify({"message": "Something went wrong. Please try again."}), 500
    return jsonify({"message":"Success","history":history}),200
@views.route("/history",methods=["GET"])
@login_required
def history():
    try:
        history= History.query.filter_by(user_id=current_user.id).order_by(History.time.desc()).all()
    except SQLAlchemyError:
        return jsonify({"message": "Something went wrong. Please try again."}), 500
    return jsonify({"message":"Tracking history","history":history}),200