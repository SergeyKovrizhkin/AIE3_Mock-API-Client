from embedding_client import get_embedding
import random
import pytest
import requests
import time

DEFAULT_RETRY_CONFIG = {
    'max_retries': 3,
    'start_delay': 0.01,
    'multiplier': 2.0
    }

@pytest.fixture
def make_success_response(mocker):
    def _make():
        response = mocker.MagicMock()
        response.ok = True
        response.status_code = 200
        embedding_data = [random.random() for _ in range(128)]
        response.json.return_value = {'embedding': embedding_data}
        return response
    return _make

@pytest.fixture
def make_error_response(mocker):
    def _make(status_code):
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = status_code
        return response
    return _make

def test_correct_scenario(mocker, make_success_response):
    text = "Hello World"
    mock_response = mocker.patch("embedding_client.requests.post")
    success_response = make_success_response()
    embedding = success_response.json.return_value['embedding']
    mock_response.return_value = success_response
    result = get_embedding(text, DEFAULT_RETRY_CONFIG)
    mock_response.assert_called_once()
    assert result == embedding
    
def test_500(mocker, make_success_response, make_error_response):
    text = "test_500"
    mock_response = mocker.patch("embedding_client.requests.post")
    success_response = make_success_response()
    embedding = success_response.json.return_value['embedding']
    response_500 = make_error_response(500)
    mock_response.side_effect = [response_500, success_response]
    result = get_embedding(text, DEFAULT_RETRY_CONFIG)
    assert mock_response.call_count == 2
    assert result == embedding
    
def test_404(mocker, make_error_response, capsys):
    text = "test_404"
    mock_response = mocker.patch("embedding_client.requests.post")
    response_404 = make_error_response(404)
    mock_response.return_value = response_404
    result = get_embedding(text, DEFAULT_RETRY_CONFIG)
    capture_stderr = capsys.readouterr().err
    mock_response.assert_called_once()
    assert result is None
    assert "Постоянная ошибка. Ответ не получен." in capture_stderr
    
def test_timeout(mocker, make_success_response):
    text = "test_timeout"
    mock_response = mocker.patch("embedding_client.requests.post")
    success_response = make_success_response()
    embedding = success_response.json.return_value['embedding']
    mock_response.side_effect = [requests.exceptions.Timeout, requests.exceptions.Timeout, success_response]
    result = get_embedding(text, DEFAULT_RETRY_CONFIG)
    assert mock_response.call_count == 3
    assert result == embedding
    
def test_zero_retries(mocker, make_error_response, capsys):
    text = "test_zero_retries"
    mock_response = mocker.patch("embedding_client.requests.post")
    response_500 = make_error_response(500)
    mock_response.side_effect = [response_500, response_500]
    curr_retry_config = DEFAULT_RETRY_CONFIG.copy()
    curr_retry_config['max_retries'] = 0
    result = get_embedding(text, curr_retry_config)
    capture_stderr = capsys.readouterr().err
    mock_response.assert_called_once()
    assert result is None
    assert "Превышен лимит попыток. Ответ не получен." in capture_stderr
    
def test_custom_config(mocker, make_success_response, make_error_response):
    text = "test_custom_config"
    mock_response = mocker.patch("embedding_client.requests.post")
    mock_sleep = mocker.patch("embedding_client.time.sleep")
    success_response = make_success_response()
    embedding = success_response.json.return_value['embedding']
    response_500 = make_error_response(500)
    mock_response.side_effect = [response_500, response_500, response_500, success_response]
    curr_retry_config = DEFAULT_RETRY_CONFIG.copy()
    curr_retry_config['max_retries'] = 4
    curr_retry_config['start_delay'] = 0.02
    curr_retry_config['multiplier'] = 2.5
    target_duration = 0
    delay = curr_retry_config['start_delay']
    for _ in range(curr_retry_config['max_retries'] - 1):
        target_duration += delay
        delay *= curr_retry_config['multiplier']
    result = get_embedding(text, curr_retry_config)
    fact_duration = 0
    for call in mock_sleep.call_args_list:
        fact_duration += call.args[0]
    assert target_duration == fact_duration
    assert mock_response.call_count == 4
    assert result == embedding