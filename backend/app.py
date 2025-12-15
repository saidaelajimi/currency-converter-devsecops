import os
import secrets
from flask import Flask, jsonify, request, abort
import requests
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from functools import wraps
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# === CONFIGURATION CRITIQUE ===
# Les variables doivent être définies dans l'environnement
EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
CSRF_TOKEN = os.environ.get("CSRF_TOKEN")

# Validation stricte en production
if not EXCHANGE_RATE_API_KEY:
    logger.error("❌ EXCHANGE_RATE_API_KEY non configurée")
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError("EXCHANGE_RATE_API_KEY manquante")
    EXCHANGE_RATE_API_KEY = "demo_key_only_for_development"

if not SECRET_KEY or SECRET_KEY == "change_me_in_production":
    logger.warning("⚠️ SECRET_KEY faible détectée")
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError("SECRET_KEY trop faible pour la production")
    SECRET_KEY = secrets.token_hex(32)

app.config['SECRET_KEY'] = SECRET_KEY

# === SÉCURITÉ CORS ===
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

CORS(app, resources={
    r"/rates": {
        "origins": allowed_origins,
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Request-ID"],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        "supports_credentials": False,
        "max_age": 600
    }
})

# === PROTECTION CSRF ===
csrf = CSRFProtect(app)

def require_csrf(f):
    """Décorateur pour protéger les routes POST/PUT/DELETE"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            token = request.headers.get("X-CSRF-Token")
            if not token or token != CSRF_TOKEN:
                abort(403, description="Token CSRF invalide ou manquant")
        return f(*args, **kwargs)
    return decorated_function

# === RATE LIMITING SIMPLE ===
from datetime import datetime, timedelta

request_log = {}

def rate_limit(ip, limit=100, window=60):
    """Limite le nombre de requêtes par IP"""
    now = datetime.now()
    window_start = now - timedelta(seconds=window)
    
    # Nettoyer les vieilles entrées
    request_log[ip] = [t for t in request_log.get(ip, []) if t > window_start]
    
    # Vérifier la limite
    if len(request_log.get(ip, [])) >= limit:
        return False
    
    # Ajouter la requête
    request_log.setdefault(ip, []).append(now)
    return True

@app.before_request
def before_request():
    """Middleware de sécurité"""
    # Rate limiting
    ip = request.remote_addr
    if not rate_limit(ip):
        abort(429, description="Trop de requêtes. Réessayez plus tard.")
    
    # Headers de sécurité
    response_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Ces headers seront ajoutés à la réponse
    request.custom_headers = response_headers

# === ROUTES ===
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé (sans clé API)"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "currency-converter-api"
    })

@app.route('/rates', methods=['GET'])
def get_rates():
    """Endpoint principal pour les taux de change"""
    try:
        # Journalisation sécurisée (sans la clé)
        logger.info(f"Requête taux de change depuis {request.remote_addr}")
        
        # Construire l'URL de l'API externe
        api_url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"
        
        # Headers sécurisés pour la requête externe
        headers = {
            'User-Agent': 'CurrencyConverter/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Format de réponse sécurisé
        result = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "base_currency": "USD",
            "conversion_rates": data.get("conversion_rates", {})
        }
        
        # Retourner avec les headers de sécurité
        resp = jsonify(result)
        for key, value in request.custom_headers.items():
            resp.headers[key] = value
        
        return resp, 200

    except requests.exceptions.Timeout:
        logger.error("Timeout de l'API externe")
        return jsonify({
            "status": "error",
            "message": "Service temporairement indisponible"
        }), 504
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Impossible de récupérer les taux de change"
        }), 500
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Une erreur interne est survenue"
        }), 500

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint non trouvé"
    }), 404

@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({
        "status": "error",
        "message": "Limite de requêtes atteinte"
    }), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Erreur interne du serveur"
    }), 500

# === MAIN ===
if __name__ == '__main__':
    # Vérifications de sécurité au démarrage
    env = os.environ.get("FLASK_ENV", "development")
    debug_mode = env == "development"
    
    if debug_mode:
        logger.warning("⚠️ Mode développement activé - NON SÉCURISÉ POUR LA PRODUCTION")
    else:
        logger.info("✅ Mode production activé")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode,
        threaded=True
    )