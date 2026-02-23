"""
Toolkit Access Request API — Cloud Run Service
Receives form submissions from the onboarding site and emails Jake via Domo Code Engine.
"""

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "https://jakeheaps-coder.github.io",
    "http://localhost:*",
    "http://127.0.0.1:*"
])

DOMO_INSTANCE = "domo"
DOMO_ACCESS_TOKEN = os.environ.get("DOMO_ACCESS_TOKEN", "")
CE_EMAIL_PACKAGE_ID = os.environ.get("CE_EMAIL_PACKAGE_ID", "02b77ae9-fc21-40c7-8a62-d9d735e2db9c")
CE_EMAIL_VERSION = os.environ.get("CE_EMAIL_VERSION", "3.3.1")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "jake.heaps@domo.com")


def send_email_via_domo(to_email: str, subject: str, body: str) -> dict:
    """Send an email using Domo Code Engine."""
    url = f"https://{DOMO_INSTANCE}.domo.com/api/codeengine/v2/packages/{CE_EMAIL_PACKAGE_ID}/versions/{CE_EMAIL_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "X-DOMO-Developer-Token": DOMO_ACCESS_TOKEN,
    }
    payload = {
        "to": to_email,
        "subject": subject,
        "body": body,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


@app.route("/api/request-access", methods=["POST"])
def request_access():
    """Handle toolkit access request form submission."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()
    username = data.get("username", "").strip()
    role = data.get("role", "Unknown").strip()

    if not name or not username:
        return jsonify({"error": "Name and GitHub username are required"}), 400

    subject = f"Toolkit Access Request - {role}: {name}"
    body = f"""New toolkit access request:

Name: {name}
GitHub Username: {username}
Role: {role}
Page: {data.get('page', 'Unknown')}

Action needed:
1. Add {username} as a collaborator on GitHub: https://github.com/jakeheaps-coder/creative-director-toolkit/settings/access
2. Add to users.json with role: {role.lower()}
"""

    try:
        send_email_via_domo(NOTIFY_EMAIL, subject, body)
        return jsonify({"success": True, "message": "Request sent to Jake"})
    except Exception as e:
        # Fallback: log the request even if email fails
        print(f"Email failed: {e}")
        print(f"ACCESS REQUEST: name={name}, username={username}, role={role}")
        return jsonify({
            "success": True,
            "message": "Request logged. Jake will be notified.",
            "fallback": True
        })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "toolkit-access-api"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
