import os
from flask import Flask, jsonify, request, abort
import requests
from flask_cors import CORS  

app = Flask(__name__) 

# 🔒 Limitation du CORS uniquement à la route /rates et aux origines connues
CORS(app, resources={
    r"/rates": {
        "origins": [
            "https://react-frontend-unique123.eastus.azurecontainer.io",
            "http://react-frontend-unique123.eastus.azurecontainer.io",
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "methods": ["GET"],
        "allow_headers": ["Content-Type"]
    }
})

# 🔐 Protection CSRF pour les routes POST (si ajoutées dans le futur)
CSRF_TOKEN = os.environ.get("CSRF_TOKEN", "default_csrf_token")  # définir dans GitHub secrets pour prod

@app.before_request
def protect_csrf():
    if request.method == "POST":
        token = request.headers.get("X-CSRF-Token")
        if token != CSRF_TOKEN:
            abort(403, description="CSRF token missing or invalid")

# 🚀 Route GET pour les taux de conversion
@app.route('/rates', methods=['GET'])
def getRates():
    try:
        response = requests.get(
            "https://v6.exchangerate-api.com/v6/97f9dc6126138480ee6da5fb/latest/USD"
        )
        response.raise_for_status()
        data = response.json()

        # 🔥 Format attendu par les tests
        return jsonify({
            "status": "success",
            "conversion_rates": data.get("conversion_rates", {})
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Failed to fetch conversion rates",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
