
from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
from utils import load_json, save_json, upload_to_ipfs
from blockchain import send_report_to_blockchain, contract

app = Flask(__name__)

# File paths
USERS_FILE = "data/users.json"
REPORTS_FILE = "data/reports.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

@app.route("/")
def index():
    """Home page with links to actions."""
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register_user():
    """Registers a new user with their MetaMask address."""
    if request.method == "POST":
        metamask_address = request.form.get("metamask_address")
        if not metamask_address:
            return render_template("register.html", error="MetaMask address is required")
        
        users = load_json(USERS_FILE)
        if metamask_address in users:
            message = "User already registered"
        else:
            users[metamask_address] = {"reported_issues": []}
            save_json(USERS_FILE, users)
            message = "User registered successfully"
        return render_template("register.html", message=message)
    return render_template("register.html")

@app.route("/report", methods=["GET", "POST"])
def report_issue():
    """Displays a form and handles submission of a whistleblower report."""
    if request.method == "POST":
        metamask_address = request.form.get("metamask_address")
        organization = request.form.get("organization")
        description = request.form.get("description")

        if not all([metamask_address, organization, description]):
            return render_template("report_form.html", error="All fields are required")

        # Handle file upload (if any)
        file = request.files.get("document")
        ipfs_document_url = None
        if file:
            ipfs_document_url = upload_to_ipfs(file.read(), is_file=True, filename=file.filename)  

        # Prepare report data to store locally
        report = {
            "metamask_address": metamask_address,
            "organization": organization,
            "description": description,
            "document_url": ipfs_document_url,
            "status": "Pending"
        }

        # Save to local JSON storage
        reports = load_json(REPORTS_FILE)
        # Ensure reports is a list if file is empty or not created yet
        if not isinstance(reports, list):
            reports = []
        reports.append(report)
        save_json(REPORTS_FILE, reports)

        # Convert to JSON and upload to IPFS
        ipfs_hash = upload_to_ipfs(json.dumps(report))

        # Send the IPFS hash to blockchain.
        # This returns the unsigned transaction object for now.
        tx_object = send_report_to_blockchain(ipfs_hash, metamask_address)

        return render_template("report_form.html", message="Report submitted successfully", 
                               tx_object=tx_object, ipfs_hash=ipfs_hash, document_url=ipfs_document_url)
    return render_template("report_form.html")

@app.route("/my_reports/<string:metamask_address>")
def get_my_reports(metamask_address):
    """Fetch and display reports for a specific user."""
    reports = load_json(REPORTS_FILE)
    user_reports = [r for r in reports if r["metamask_address"] == metamask_address]
    return render_template("my_reports.html", reports=user_reports, metamask_address=metamask_address)

@app.route("/report/<int:report_id>", methods=["GET"])
def get_report(report_id):
    """Retrieve a specific report from the blockchain by its ID."""
    try:
        # Call the smart contract function getReport(report_id)
        ipfs_hash, reporter, resolved = contract.functions.getReport(report_id).call()
        return jsonify({
            "id": report_id,
            "ipfs_hash": ipfs_hash,
            "reporter": reporter,
            "resolved": resolved
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# @app.route("/my_reports/<string:metamask_address>", methods=["GET"])
# def get_my_reports(metamask_address):
#     """Fetch reports for a specific user."""
#     reports = load_json(REPORTS_FILE)
#     user_reports = [r for r in reports if r["metamask_address"] == metamask_address]
#     return jsonify(user_reports)


@app.route("/my_reports/<string:metamask_address>", methods=["GET"])
def my_reports_page(metamask_address):
    """Display reports for a specific user in an HTML page."""
    reports = load_json(REPORTS_FILE)
    user_reports = [r for r in reports if r["metamask_address"] == metamask_address]
    return render_template("my_reports.html", reports=user_reports, metamask_address=metamask_address)

if __name__ == "__main__":
    app.run(debug=True)


# from flask import Flask, request, jsonify
# import json
# import os
# from utils import load_json, save_json, upload_to_ipfs
# from blockchain import send_report_to_blockchain

# app = Flask(__name__)

# # File paths
# USERS_FILE = "data/users.json"
# REPORTS_FILE = "data/reports.json"

# # Ensure data directory exists
# os.makedirs("data", exist_ok=True)

# @app.route("/register", methods=["POST"])
# def register_user():
#     """Registers a new user with their MetaMask address."""
#     data = request.json
#     metamask_address = data.get("metamask_address")

#     if not metamask_address:
#         return jsonify({"error": "MetaMask address is required"}), 400

#     users = load_json(USERS_FILE)

#     if metamask_address in users:
#         return jsonify({"message": "User already registered"}), 200

#     users[metamask_address] = {"reported_issues": []}
#     save_json(USERS_FILE, users)

#     return jsonify({"message": "User registered successfully"}), 201

# @app.route("/report", methods=["POST"])
# def report_issue():
#     """Handles a whistleblower report with an optional document upload."""
#     metamask_address = request.form.get("metamask_address")
#     organization = request.form.get("organization")
#     description = request.form.get("description")

#     if not all([metamask_address, organization, description]):
#         return jsonify({"error": "Missing required fields"}), 400

#     # Handle file upload (if any)
#     file = request.files.get("document")
#     ipfs_document_url = None
#     if file:
#         ipfs_document_url = upload_to_ipfs(file.read(), is_file=True, filename=file.filename)  

#     # Prepare report data
#     report = {
#         "metamask_address": metamask_address,
#         "organization": organization,
#         "description": description,
#         "document_url": ipfs_document_url,
#         "status": "Pending"
#     }

#     # Save to local JSON storage
#     reports = load_json(REPORTS_FILE)
#     reports.append(report)
#     save_json(REPORTS_FILE, reports)

#     # Convert to JSON and upload to IPFS
#     ipfs_hash = upload_to_ipfs(json.dumps(report))

#     # Send the IPFS hash to blockchain using private key (from .env)
#     tx_hash = send_report_to_blockchain(ipfs_hash, metamask_address)

#     return jsonify({
#         "message": "Report submitted successfully",
#         "tx_hash": tx_hash,
#         "ipfs_hash": ipfs_hash,
#         "document_url": ipfs_document_url
#     }), 201

# @app.route("/my_reports/<string:metamask_address>", methods=["GET"])
# def get_my_reports(metamask_address):
#     """Fetch reports for a specific user."""
#     reports = load_json(REPORTS_FILE)
#     user_reports = [r for r in reports if r["metamask_address"] == metamask_address]
#     return jsonify(user_reports)

# if __name__ == "__main__":
#     app.run(debug=True)

