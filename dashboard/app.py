"""
InsightOps – Flask Web Application
Replaces Streamlit. Serves pre-computed JSON data through a fast,
always-on web dashboard deployable to Render.
"""

import json
from pathlib import Path
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder="templates", static_folder="static")

DATA_FILE = Path(__file__).parent / "static" / "data" / "dashboard_data.json"


def load_data():
    """Load pre-computed dashboard data from JSON."""
    if not DATA_FILE.exists():
        return None
    with open(DATA_FILE) as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    data = load_data()
    if data is None:
        return jsonify({"error": "Dashboard data not found. Run export_data.py first."}), 503
    return jsonify(data)


@app.route("/health")
def health():
    """Render health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
