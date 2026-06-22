import json
import pytest
from unittest.mock import patch, MagicMock
from lambda.app import app, hello, save_item

mock_table = MagicMock()
mock_table.put_item.return_value = {}

@pytest.fixture
def mock_dynamodb():
    with patch('lambda.app.table', mock_table):
        yield mock_table

def test_hello_default():
    result = hello()
    assert result['message'] == 'Hello World from Lambda!'

def test_save_item_success(mock_dynamodb):
    item = {'id': '123', 'name': 'Test'}
    result = save_item(item)
    assert result['status'] == 'saved'
    mock_dynamodb.put_item.assert_called_once_with(Item=item)