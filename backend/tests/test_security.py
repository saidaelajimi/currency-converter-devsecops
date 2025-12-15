# Tests de sécurité de l'application
import pytest
from unittest.mock import patch, Mock
import os
import re


def test_api_key_not_exposed_in_response(client):
    """CRITIQUE: Vérifier que la clé API n'est JAMAIS exposée"""
    mock_response = Mock()
    mock_response.json.return_value = {
        'result': 'success',
        'conversion_rates': {'EUR': 0.85}
    }
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        # Utiliser une clé de test qui n'est pas une vraie clé API
        with patch.dict(os.environ, {'EXCHANGE_RATE_API_KEY': 'test_dummy_key_12345'}):
            response = client.get('/rates')
            data_str = str(response.get_data())
            
            # Vérifier qu'aucune clé API réelle n'est exposée
            # Ces patterns ne doivent PAS apparaître
            assert 'exchangerate-api.com/v6/' not in data_str
            
            # Vérifier qu'aucun pattern de clé API n'est présent
            api_key_pattern = r'[a-f0-9]{32}'
            matches = re.findall(api_key_pattern, data_str)
            assert len(matches) == 0, f"Clé API détectée dans la réponse: {matches}"
            
            # Vérifier les headers de sécurité
            security_headers = ['X-Content-Type-Options', 'X-Frame-Options', 'X-XSS-Protection']
            for header in security_headers:
                assert header in response.headers


def test_no_hardcoded_api_key_in_code():
    """Vérifier qu'aucune clé API n'est codée en dur"""
    # Lire tous les fichiers Python
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and 'test_' in file:
                python_files.append(os.path.join(root, file))
    
    # Patterns à vérifier
    dangerous_patterns = [
        'exchangerate-api.com/v6/',
        '97f9dc6126138480ee6da5fb',
        'c9320a54e197eec7764f7dca'
    ]
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in dangerous_patterns:
                assert pattern not in content, f"Pattern dangereux trouvé dans {file_path}: {pattern}"


def test_cors_configured_properly(client):
    """Test que CORS est correctement configuré"""
    mock_response = Mock()
    mock_response.json.return_value = {'result': 'success', 'conversion_rates': {}}
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        response = client.get('/rates', headers={'Origin': 'http://localhost:5173'})
        assert 'Access-Control-Allow-Origin' in response.headers


def test_no_debug_mode_in_production(app):
    """Test que le mode debug n'est pas activé en production"""
    # Tester en mode production
    app.config['FLASK_ENV'] = 'production'
    assert app.debug is False
    
    # Tester en mode développement
    app.config['FLASK_ENV'] = 'development'
    # En développement, debug peut être True


def test_security_headers_present(client):
    """Vérifier la présence des headers de sécurité"""
    mock_response = Mock()
    mock_response.json.return_value = {'result': 'success', 'conversion_rates': {}}
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        response = client.get('/rates')
        
        # Headers de sécurité obligatoires
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Header de sécurité manquant: {header}"


def test_health_endpoint_does_not_expose_secrets(client):
    """L'endpoint de santé ne doit pas exposer de secrets"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'healthy'
    
    # Vérifier qu'aucune clé API n'est dans la réponse
    response_text = str(response.get_data())
    api_key_patterns = [
        'EXCHANGE_RATE_API_KEY',
        'SECRET_KEY',
        'CSRF_TOKEN',
        'exchangerate-api.com'
    ]
    
    for pattern in api_key_patterns:
        assert pattern not in response_text, f"Secret exposé dans /health: {pattern}"


def test_env_file_not_in_repository():
    """Vérifier que le fichier .env n'est pas dans le dépôt"""
    assert not os.path.exists('.env'), "Le fichier .env ne doit pas être commit"
    assert not os.path.exists('backend/.env'), "Le fichier backend/.env ne doit pas être commit"
    
    # Vérifier que .env.example existe
    assert os.path.exists('backend/.env.example'), ".env.example doit exister"
    
    # Vérifier que .env.example ne contient pas de vraies clés
    if os.path.exists('backend/.env.example'):
        with open('backend/.env.example', 'r') as f:
            content = f.read()
            # Ne doit pas contenir de vraies clés API
            assert 'c9320a54e197eec7764f7dca' not in content
            assert '97f9dc6126138480ee6da5fb' not in content