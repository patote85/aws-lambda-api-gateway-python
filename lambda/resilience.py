# Retry com backoff + Circuit Breaker simples
import time
from functools import wraps

def circuit_breaker(max_failures=5, reset_timeout=30):
    failures = 0
    last_failure_time = 0
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal failures, last_failure_time
            if failures >= max_failures and time.time() - last_failure_time < reset_timeout:
                raise Exception("Circuit breaker open")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                failures += 1
                last_failure_time = time.time()
                raise
        return wrapper
    return decorator

@circuit_breaker()
def call_dynamodb_with_retry(func, *args, **kwargs):
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return None