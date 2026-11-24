from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)  # Allow your Netlify site to call this

# === CONFIG (set these as Environment Variables on Render) ===
MEDALLION_BASE_URL = os.getenv("MEDALLION_BASE_URL", "http://localhost:5000")
MEDALLION_API_KEY = os.getenv("MEDALLION_API_KEY", "test-key-123")

ALLOWED_USERS = {
    "warehouse@austinelectric.com": "warehouse123",
    "admin@austinelectric.com": "admin123",
}

@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if email in ALLOWED_USERS and ALLOWED_USERS[email] == password:
        return jsonify({"success": True, "email": email})
    return jsonify({"success": False, "error": "Invalid email or password"}), 401

@app.route("/api/charge", methods=["POST"])
def charge():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON"}), 400

    job_number = data.get("job_number")
    part_number = data.get("part_number")
    quantity = data.get("quantity")
    description = data.get("description", "")
    notes = data.get("notes", "")

    if not job_number or not part_number or quantity is None:
        return jsonify({"error": "job_number, part_number, and quantity are required"}), 400

    url = f"{MEDALLION_BASE_URL}/api/v1/jobs/{job_number}/materials"
    headers = {
        "x-api-key": MEDALLION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "part_number": part_number,
        "quantity": quantity,
        "description": description,
        "notes": notes
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return jsonify({
        "status": "Warehouse proxy running",
        "message": "API key is kept on the server",
        "medallion_url_set": bool(MEDALLION_BASE_URL)
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print(f"Proxy running on port {port}")
    print(f"Using Medallion URL: {MEDALLION_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)