import json
import pytest
from unittest.mock import patch, MagicMock
from lambda.app import app, solicitar_exclusao, get_status

mock_table = MagicMock()

@pytest.fixture
def mock_dynamodb():
    with patch('lambda.app.table', mock_table):
        yield

def test_solicitar_exclusao(mock_dynamodb):
    event = {'httpMethod': 'POST', 'path': '/solicitar-exclusao-cliente', 'body': json.dumps({'cliente_id': '123', 'motivo': 'Test'})}
    # Simplified test - in real use moto or full mock
    # assert response has qr_code etc.
    pass  # Expand with full mocks

def test_get_status(mock_dynamodb):
    pass