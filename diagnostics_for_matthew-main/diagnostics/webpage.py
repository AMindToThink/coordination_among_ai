import html
import json

# Initialize simulator with a default patient file
import pandas as pd
from data_loaders import (
    randomly_sample_patient_file,
    save_completed_case,
    save_diagnosis_result,
)
from evaluate_llm_grading import grade_diagnosis
from llm_diagnosis import get_possible_diagnoses, get_possible_diagnoses_baseline
from markupsafe import escape
from quart import Quart, jsonify, redirect, render_template, request, session, url_for
from quart_auth import (
    AuthUser,
    QuartAuth,
    Unauthorized,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from simulate import Simulator
from werkzeug.security import check_password_hash, generate_password_hash

# ... existing imports ...


app = Quart(__name__)
app.secret_key = "hello_there"
app.config["QUART_AUTH_COOKIE_SECURE"] = False  # Allow cookies on HTTP
app.config["SESSION_COOKIE_SECURE"] = False  # Allow session cookies on HTTP
auth_manager = QuartAuth(app)


# Simple user class
class User(AuthUser):
    def __init__(self, auth_id):
        super().__init__(auth_id)


# In-memory user database - Replace with a proper database for production
# Simple plain-text username/password pairs
users = {"dennis": "yale", "bradly": "nu", "mauro": "europe", "test": "test"}


@app.errorhandler(Unauthorized)
async def unauthorized(e):
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "GET":
        return await render_template("login.html")

    form = await request.form
    username = form.get("username")
    password = form.get("password")

    print(f"Login attempt: {username}")  # Debug print

    if username in users and users[username] == password:
        print(f"Login successful for {username}")  # Debug print
        login_user(User(username))
        session["mode"] = "simulator_calibrate"
        print(f"LOGIN: Setting mode to: {session.get('mode')}")  # Debug print
        return redirect(url_for("index"))

    print(f"Login failed for {username}")  # Debug print
    return await render_template("login.html", error="Invalid credentials")


@app.route("/logout")
async def logout():
    logout_user()
    return redirect(url_for("login"))


# Modify your existing routes to require login
@app.route("/")
@login_required
async def index():
    current_mode = session.get("mode", "no_help")
    
    # Check completion status first
    if current_mode != 'demo':
        try:
            # Try to sample a patient file to check if any are available
            randomly_sample_patient_file(mode=current_mode, username=current_user.auth_id)
        except ValueError as e:
            # User has completed all cases
            return await render_template(
                "index.html",
                medical_history="<p><strong>Congratulations!</strong> You have completed all available cases for this mode.</p>",
                disease_list="",
                show_sidebar=False,
                current_mode=current_mode,
                username=current_user.auth_id,
                completed=True
            )
    
    # If not completed, proceed with normal flow
    try:
        if not hasattr(app, "simulator"):
            simulator = get_simulator()
        else:
            simulator = app.simulator
        medical_history = format_medical_history(simulator)
        return await render_template(
            "index.html",
            medical_history=medical_history,
            disease_list="No diseases identified yet.",
            show_sidebar=(current_mode != "simulator_calibrate"),
            current_mode=current_mode,
            username=current_user.auth_id,
            last_submission_type="action",
            completed=False
        )
    except ValueError as e:
        # Handle any other errors
        return await render_template(
            "index.html",
            medical_history="<p><strong>Congratulations!</strong> You have completed all available cases for this mode.</p>",
            disease_list="",
            show_sidebar=False,
            current_mode=current_mode,
            username=current_user.auth_id,
            completed=True
        )


@app.route("/change_mode", methods=["POST"])
@login_required
async def change_mode():
    data = await request.get_json()
    mode = data.get("mode")
    if mode in [
        "demo",
        "no_help",
        "generic_chatgpt_help",
        "lamp_help",
        "simulator_calibrate",
    ]:
        session["mode"] = mode
        return {"success": True}
    return {"success": False, "error": "Invalid mode"}


def get_simulator(force_new=False):
    print(f"SIMULATOR: Current mode: {session.get('mode')}")  # Debug print
    if force_new or not hasattr(app, "simulator"):
        current_mode = session.get("mode", "no_help")
        print(f"SIMULATOR: Using mode: {current_mode}")  # Debug print
        patient_file = randomly_sample_patient_file(
            mode=current_mode,
            username=current_user.auth_id
        )
        app.simulator = Simulator(
            patient_file["context"], patient_file["true_diagnosis"]
        )
        app.patient_file = patient_file
    return app.simulator


def format_medical_history(simulator):
    formatted_history = ""
    for entry in simulator.history:
        formatted_history += (
            f"<p><strong>Action:</strong> {html.escape(entry['action'])}</p>"
        )
        formatted_history += (
            f"<p><strong>Results:</strong> {html.escape(entry['result'])}</p>"
        )
        formatted_history += "<hr>"
    return formatted_history or "No actions taken yet."


def format_disease_list(possible_diagnoses):
    if not possible_diagnoses:
        return "No diseases identified yet."

    try:
        # Handle both dict and JSON string inputs
        diagnoses = (
            possible_diagnoses
            if isinstance(possible_diagnoses, dict)
            else json.loads(possible_diagnoses)
        )

        formatted_html = "<h3>Most Likely Diseases:</h3>"

        # Format most likely diseases
        for disease in diagnoses["most_likely_diseases"]:
            formatted_html += f"""
                <p><strong>{html.escape(disease['disease'])}</strong><br>
                <span class="rationale">{html.escape(disease['rationale'])}</span></p>
            """

        formatted_html += "<h3>Rare Possibilities:</h3>"

        # Format rare possibilities
        for disease in diagnoses["rare_possibilities"]:
            formatted_html += f"""
                <p><strong>{html.escape(disease['disease'])}</strong><br>
                <span class="rationale">{html.escape(disease['rationale'])}</span></p>
            """

        return formatted_html
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"Error formatting disease list: {e}")
        return "Error parsing disease list."


@app.route("/submit_action", methods=["POST"])
async def submit_action():
    form = await request.form
    action = form.get("action", "")
    current_mode = session.get("mode", "no_help")

    simulator = get_simulator()
    simulation_result = simulator.simulate(action)

    medical_history = format_medical_history(simulator)

    # Simplified logic for disease list display
    formatted_diseases = "No diseases identified yet."
    if current_mode not in ["simulator_calibrate", "no_help"]:
        if current_mode == "generic_chatgpt_help":
            raw_diseases = get_possible_diagnoses_baseline(simulator.get_history())
            formatted_diseases = f"""
                <h3>Possible Diagnoses:</h3>
                <p>{html.escape(raw_diseases)}</p>
            """
        else:
            raw_diseases = get_possible_diagnoses(simulator.get_history())
            formatted_diseases = format_disease_list(raw_diseases)

    return await render_template(
        "index.html",
        medical_history=medical_history,
        disease_list=formatted_diseases,
        current_mode=current_mode,
        show_sidebar=(current_mode != "simulator_calibrate"),
        username=current_user.auth_id,
        last_submission_type="action",
    )


@app.route("/submit_diagnosis", methods=["POST"])
@login_required
async def submit_diagnosis():
    form = await request.form
    diagnosis = form.get("action", "")
    current_mode = session.get("mode", "no_help")  # Changed from 'demo'

    simulator = get_simulator()
    grade, thought = grade_diagnosis(diagnosis, app.patient_file["true_diagnosis"])

    simulator.diagnosis_result = {
        "final_diagnosis": diagnosis,
        "grade": grade,
        "thought": thought,
        "feedback": "",
        "feedback_comment": "",
    }

    # Save the completed case with mode information
    case_data = {
        "final_diagnosis": diagnosis,
        "grade": grade,
        "thought": thought,
        "true_diagnosis": app.patient_file["true_diagnosis"],
        "history": simulator.get_history_json(),
        "case_id": app.patient_file["case_id"],
        "common_uncommon": app.patient_file["common_uncommon"],
    }
    save_completed_case(
        current_user.auth_id, case_data, app.patient_file["index"], mode=current_mode
    )

    # Add the diagnosis attempt to the history
    if grade == 1.0:
        result_message = f"Diagnosis attempt: {diagnosis}\n Result: Judged as Correct with rationale:\n\n{thought}"
    else:
        result_message = f"Diagnosis attempt: {diagnosis}\n Result: Judged as Incorrect with rationale:\n\n{thought}"

    # simulator.history.append(
    #     {
    #         "action": "diagnosis",
    #         "result": result_message,
    #         "feedback": "",
    #         "feedback_comment": "",
    #     }
    # )

    simulator.diagnosis_result = {
        "case_id": app.patient_file["case_id"],
        "final_diagnosis": diagnosis,
        "grade": grade,
        "thought": thought,
        "feedback": "",
        "feedback_comment": "",
    }

    medical_history = format_medical_history(simulator)
    medical_history += f"<p><strong>Action:</strong> diagnosis</p>"
    medical_history += f"<p><strong>Results:</strong> {result_message}</p>"
    formatted_diseases = "Diagnosis has been graded."

    return await render_template(
        "index.html",
        medical_history=medical_history,
        disease_list=formatted_diseases,
        current_mode=current_mode,
        username=current_user.auth_id,
        last_submission_type="diagnosis",
    )


@app.route("/new_patient")
@login_required
async def new_patient():
    current_mode = session.get("mode", "no_help")
    try:
        simulator = get_simulator(force_new=True)
        medical_history = format_medical_history(simulator)
        return await render_template(
            "index.html",
            medical_history=medical_history,
            disease_list="No diseases identified yet.",
            show_sidebar=(current_mode != "simulator_calibrate"),
            current_mode=current_mode,
            username=current_user.auth_id,
            last_submission_type="action",
            completed=False
        )
    except ValueError as e:
        # Handle the case where user has completed all available cases
        return await render_template(
            "index.html",
            medical_history="<p><strong>Congratulations!</strong> You have completed all available cases for this mode.</p>",
            disease_list="",
            show_sidebar=False,
            current_mode=current_mode,
            username=current_user.auth_id,
            completed=True
        )


@app.route("/submit_feedback", methods=["POST"])
async def submit_feedback():
    data = await request.get_json()
    feedback_type = data.get("feedback_type")
    feedback_comment = data.get("feedback_comment", "")

    simulator = get_simulator()

    if simulator.diagnosis_result != None:
        print("Test simulator")
        simulator.diagnosis_result["feedback"] = feedback_type
        simulator.diagnosis_result["feedback_comment"] = feedback_comment

        current_mode = session.get("mode", "no_help")

        save_diagnosis_result(
            current_user.auth_id,
            simulator.diagnosis_result,
            app.patient_file["index"],
            current_mode,
        )

        return jsonify({"success": True})

    if simulator:
        simulator.add_feedback(feedback_type, feedback_comment)
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "No active simulation found"})


if __name__ == "__main__":
    app.run(debug=True)
