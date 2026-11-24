import requests
import sys
import time
import argparse
import tenacity

BASE_URL = "http://127.0.0.1:8000/embed"
MAX_TIMEOUT = 1
TEMPORARY_ERRORS = {429, 500, 503}

DEFAULT_RETRY_CONFIG = {
    'max_retries': 3,
    'start_delay': 0.01,
    'multiplier': 2.0
    }

class ClientFinalError(Exception):
    pass

def get_embedding(text, retry_config):
    my_request = {'input' : text}
    result = []
    curr_try = 0
    curr_delay = retry_config['start_delay']
    response_accepted = False
    try:
        while not response_accepted and curr_try <= retry_config["max_retries"]:
            try:
                #if curr_try > 0:
                    #print("Warning: Пытаюсь отправить повторный запрос", file=sys.stderr)
                response = requests.post(BASE_URL, json=my_request, timeout=(MAX_TIMEOUT, MAX_TIMEOUT))
                if response.ok:
                    response_accepted = True
                    result = response.json()['embedding']
                elif response.status_code not in TEMPORARY_ERRORS:
                    raise ClientFinalError("Постоянная ошибка. Ответ не получен.")
                else:
                    curr_try, curr_delay = update_counters(curr_try, curr_delay, retry_config)
            except (requests.exceptions.Timeout, requests.exceptions.RequestException):
                curr_try, curr_delay = update_counters(curr_try, curr_delay, retry_config)
        if curr_try >= retry_config["max_retries"] and result == []:
            raise ClientFinalError("Превышен лимит попыток. Ответ не получен.")         
    except ClientFinalError as error:
        print(error, file=sys.stderr)
        result = None
    return result

def update_counters(curr_try, curr_delay, retry_config):
    curr_try += 1
    if curr_try <= retry_config['max_retries']:
        time.sleep(curr_delay)
        curr_delay *= retry_config['multiplier']
    return curr_try, curr_delay

def get_embedding_with_tenacity(text, retry_config):
    stop_condition = tenacity.stop_after_attempt(retry_config['max_retries'] + 1)
    delay_settings = tenacity.wait_exponential(multiplier=retry_config['start_delay'], exp_base=retry_config['multiplier'])
    acceptable_errors = (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    retry_condition = tenacity.retry_if_exception_type(acceptable_errors) | tenacity.retry_if_exception(check_http_error_for_tenacity)
    retrying_object = tenacity.Retrying(stop=stop_condition, wait=delay_settings, retry=retry_condition)
    my_request = {'input' : text}
    result = []
    try:
        try:
            for attempt in retrying_object:
                with attempt:
                    response = requests.post(BASE_URL, json=my_request, timeout=(MAX_TIMEOUT, MAX_TIMEOUT))
                    response.raise_for_status()
                    result = response.json()['embedding']
        except tenacity.RetryError:
            raise ClientFinalError("Превышен лимит попыток. Ответ не получен.")
        except requests.exceptions.HTTPError:
            raise ClientFinalError("Постоянная ошибка. Ответ не получен.")
    except ClientFinalError as error:
        print(error, file=sys.stderr)
        result = None    
    return result

def check_http_error_for_tenacity(exception):
    return (isinstance(exception, requests.exceptions.HTTPError) 
            and exception.response is not None 
            and exception.response.status_code in TEMPORARY_ERRORS)

def main():
    parser = argparse.ArgumentParser(description="Клиентская часть для отправки запросов на ембеддинг-сервер")
    parser.add_argument("--text", help="Текст запроса к серверу", default="Hello World")
    parser.add_argument("--max_retries", help="Максимальное количество повторных попыток", type=int, default=DEFAULT_RETRY_CONFIG['max_retries'])
    parser.add_argument("--start_delay", help="Начальная задержка между попытками", type=float, default=DEFAULT_RETRY_CONFIG['start_delay'])
    parser.add_argument("--multiplier", help="Множитель задержки", type=float, default=DEFAULT_RETRY_CONFIG['multiplier'])
    args = parser.parse_args()
    curr_retry_config = {
        'max_retries': args.max_retries,
        'start_delay': args.start_delay,
        'multiplier': args.multiplier
    }
    result = get_embedding(args.text, curr_retry_config)
    print(result)
    '''
    result = get_embedding_with_tenacity(args.text, curr_retry_config)
    print('-'*100)
    print(f"\nЗАПУСК КЛИЕНТА С TENACITY \n{result}")
    print('-'*100)
    '''

if __name__ == "__main__":
    main()