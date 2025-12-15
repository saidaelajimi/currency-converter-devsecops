import os
from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

app = Flask(__name__)

# Get environment variables with safe defaults
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", os.urandom(24).hex())
app.config['WTF_CSRF_ENABLED'] = os.environ.get("WTF_CSRF_ENABLED", "False").lower() == "true"

# Initialize CSRF but it will be disabled for API routes
csrf = CSRFProtect(app)

# Get allowed origins from environment variable
# In Render: https://currency-converter-web.onrender.com,http://localhost:5173
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
else:
    allowed_origins = []

# Enable CORS for all routes (simpler for API)
CORS(app, resources={
    r"/*": {
        "origins": allowed_origins + [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:5000"
        ],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Type"]
    }
})

# Health check endpoint (REQUIRED for Render)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "currency-converter-api",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# Root endpoint
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Currency Converter API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "rates": "/rates",
            "health": "/health"
        },
        "documentation": "Use /rates to get currency conversion rates"
    }), 200

# Main API endpoint
@app.route('/rates', methods=['GET'])
def get_rates():
    """Fetch currency conversion rates from external API"""
    # Get API key from environment (should be set in Render dashboard)
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY", "97f9dc6126138480ee6da5fb")
    base_currency = request.args.get('base', 'USD')
    
    # Validate base currency
    if len(base_currency) != 3:
        return jsonify({
            "status": "error",
            "message": "Invalid base currency. Must be 3 characters (e.g., USD, EUR)"
        }), 400
    
    try:
        # Fetch from external API with timeout
        response = requests.get(
            f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Format response to match your frontend expectations
        if data.get("result") == "success":
            return jsonify({
                "status": "success",
                "base": data.get("base_code", "USD"),
                "conversion_rates": data.get("conversion_rates", {}),
                "last_update": data.get("time_last_update_utc", "")
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "External API returned an error",
                "error_type": data.get("error-type", "unknown")
            }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Exchange rate API timeout. Please try again."
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Failed to fetch conversion rates from external service",
            "error": str(e)
        }), 502
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": str(e)
        }), 500

# Add CSRF exemption for all routes (since it's a public API)
@csrf.exempt
@app.route('/rates', methods=['OPTIONS'])
def handle_options():
    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)