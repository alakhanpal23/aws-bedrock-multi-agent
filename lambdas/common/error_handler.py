import json
import logging
import time
import functools
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger()

class RetryableError(Exception):
    """Exception that should trigger a retry"""
    pass

class NonRetryableError(Exception):
    """Exception that should not trigger a retry"""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (RetryableError, ConnectionError, TimeoutError)
):
    """
    Decorator for exponential backoff retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    # Non-retryable error
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator

def handle_lambda_errors(func: Callable) -> Callable:
    """
    Decorator for standardized Lambda error handling
    """
    @functools.wraps(func)
    def wrapper(event, context):
        try:
            # Log the incoming event (sanitized)
            sanitized_event = sanitize_event_for_logging(event)
            logger.info(f"Processing event: {json.dumps(sanitized_event)}")
            
            # Execute the function
            result = func(event, context)
            
            # Log successful completion
            logger.info(f"Function {func.__name__} completed successfully")
            
            return result
            
        except NonRetryableError as e:
            error_response = {
                "error": "NonRetryableError",
                "message": str(e),
                "function": func.__name__,
                "retryable": False
            }
            logger.error(f"Non-retryable error: {json.dumps(error_response)}")
            return error_response
            
        except RetryableError as e:
            error_response = {
                "error": "RetryableError", 
                "message": str(e),
                "function": func.__name__,
                "retryable": True
            }
            logger.error(f"Retryable error: {json.dumps(error_response)}")
            raise  # Re-raise to trigger Step Functions retry
            
        except Exception as e:
            error_response = {
                "error": "UnexpectedError",
                "message": str(e),
                "function": func.__name__,
                "retryable": True  # Default to retryable for unexpected errors
            }
            logger.error(f"Unexpected error: {json.dumps(error_response)}")
            raise  # Re-raise to trigger Step Functions retry
            
    return wrapper

def sanitize_event_for_logging(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from event before logging
    """
    sensitive_keys = ['password', 'token', 'key', 'secret', 'credential']
    
    def sanitize_dict(d):
        if not isinstance(d, dict):
            return d
            
        sanitized = {}
        for k, v in d.items():
            if any(sensitive_key in k.lower() for sensitive_key in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = sanitize_dict(v)
            elif isinstance(v, list):
                sanitized[k] = [sanitize_dict(item) if isinstance(item, dict) else item for item in v]
            else:
                sanitized[k] = v
        return sanitized
    
    return sanitize_dict(event)

def validate_required_fields(event: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in the event
    """
    missing_fields = []
    
    for field in required_fields:
        if '.' in field:
            # Handle nested fields like 'inputs.query'
            parts = field.split('.')
            current = event
            
            try:
                for part in parts:
                    current = current[part]
            except (KeyError, TypeError):
                missing_fields.append(field)
        else:
            if field not in event:
                missing_fields.append(field)
    
    if missing_fields:
        raise NonRetryableError(f"Missing required fields: {', '.join(missing_fields)}")

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    """
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise RetryableError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit breaker
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise

# Global circuit breakers for common services
bedrock_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30.0)
opensearch_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)