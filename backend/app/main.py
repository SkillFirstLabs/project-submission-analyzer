import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS
from app.api.routes.analyze import analyze_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(analyze_bp)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "project analyzer api is running"})

@app.errorhandler(Exception)
def handle_exception(e):
    response = jsonify({"detail": f"Internal Server Error: {str(e)}"})
    return response, 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
