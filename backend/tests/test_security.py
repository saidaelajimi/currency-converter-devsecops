# Tests de sécurité de l'application
import pytest
from unittest.mock import patch, Mock
import os


def test_api_key_not_exposed_in_response(client):
    """CRITIQUE: Vérifier que la clé API n'est JAMAIS exposée"""
    mock_response = Mock()
    mock_response.json.return_value = {
        'result': 'success',
        'conversion_rates': {'EUR': 0.85}
    }
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        # Simuler une clé API de test
        with patch.dict(os.environ, {'EXCHANGE_RATE_API_KEY': 'TEST_KEY_123456'}):
            response = client.get('/rates')
            data_str = str(response.get_data())
            
            # Vérifier qu'aucune clé API n'est exposée
            assert 'EXCHANGE_RATE_API_KEY' not in data_str
            assert 'TEST_KEY_123456' not in data_str
            assert 'exchangerate-api.com/v6/' not in data_str
            
            # Vérifier les headers de sécurité
            assert 'X-Content-Type-Options' in response.headers
            assert 'X-Frame-Options' in response.headers


def test_no_hardcoded_api_key_in_app():
    """Vérifier que la clé API n'est pas codée en dur"""
    with open('app.py', 'r') as f:
        content = f.read()
        
    # Vérifier que l'ancienne clé n'est pas présente
    assert '97f9dc6126138480ee6da5fb' not in content
    assert 'c9320a54e197eec7764f7dca' not in content
    
    # Vérifier qu'on utilise bien os.environ
    assert 'os.environ.get("EXCHANGE_RATE_API_KEY")' in content


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
    app.config['FLASK_ENV'] = 'production'
    assert app.debug is False


def test_security_headers_present(client):
    """Vérifier la présence des headers de sécurité"""
    mock_response = Mock()
    mock_response.json.return_value = {'result': 'success', 'conversion_rates': {}}
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        response = client.get('/rates')
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        for header in security_headers:
            assert header in response.headers


def test_health_endpoint(client):
    """Test de l'endpoint de santé"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'