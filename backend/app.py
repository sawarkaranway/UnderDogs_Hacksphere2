from flask import Flask, request, jsonify
import json
import os
from utils import load_json, save_json, upload_to_ipfs


app = Flask(__name__)

# File paths
USERS_FILE = "data/users.json"
REPORTS_FILE = "data/reports.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

@app.route("/register", methods=["POST"])
def register_user():
    """Registers a new user with their MetaMask address."""
    data = request.json
    metamask_address = data.get("metamask_address")

    if not metamask_address:
        return jsonify({"error": "MetaMask address is required"}), 400

    users = load_json(USERS_FILE)

    if metamask_address in users:
        return jsonify({"message": "User already registered"}), 200

    users[metamask_address] = {"reported_issues": []}
    save_json(USERS_FILE, users)

    return jsonify({"message": "User registered successfully"}), 201