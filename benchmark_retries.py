from embedding_client import get_embedding, get_embedding_with_tenacity
import time

NUM_REQUESTS = 100

DEFAULT_RETRY_CONFIG = {
    'max_retries': 3,
    'start_delay': 0.01,
    'multiplier': 2.0
    }

def analyse_config(retry_config, title, use_tenacity):
    text = "analysis"
    total_accepted = 0
    start_time = time.perf_counter()
    for _ in range(NUM_REQUESTS):
        if use_tenacity:
            result = get_embedding_with_tenacity(text, retry_config)
        else:
            result = get_embedding(text, retry_config)
        if result is not None:
            total_accepted += 1
    end_time = time.perf_counter()
    total_duration = end_time - start_time
    average_duration = total_duration / NUM_REQUESTS
    print("-"*100)
    print(title)
    print(f"max_retries = {retry_config['max_retries']}, start_delay = {retry_config['start_delay']}, multiplier = {retry_config['multiplier']}\n")
    print(f"Общее время на {NUM_REQUESTS} запросов                            : {total_duration:.4f} сек")
    print(f"Среднее время на 1 запрос (с учетом повторных попыток) : {average_duration:.4f} сек")
    print(f"Получено успешных ответов от сервера                   : {total_accepted}/{NUM_REQUESTS}")
    print("-"*100)

def main():
    analyse_config(DEFAULT_RETRY_CONFIG, "СТАНДАРТНАЯ КОНФИГУРАЦИЯ", use_tenacity=False)    
    custom_retry_config = {
        'max_retries': 2,
        'start_delay': 0.1,
        'multiplier': 3.0    
    }
    analyse_config(custom_retry_config, "КАСТОМНАЯ КОНФИГУРАЦИЯ", use_tenacity=False)
    analyse_config(DEFAULT_RETRY_CONFIG, "СТАНДАРТНАЯ КОНФИГУРАЦИЯ С TENACITY", use_tenacity=True)
    no_retry_config = {
        'max_retries': 0,
        'start_delay': 0.0,
        'multiplier': 1.0    
    }    
    analyse_config(no_retry_config, "КОНФИГУРАЦИЯ БЕЗ ПОВТОРНЫХ ПОПЫТОК", use_tenacity=False)


if __name__ == "__main__":
    main()