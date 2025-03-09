import asyncio
import inspect
from functools import wraps
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

def with_retry(func):
    """Decorator to add retry logic to a function."""
    retry_decorator = retry(
        wait=wait_random_exponential(min=1, max=60),
        # stop=stop_after_attempt(6) # stop_never is the default
    )
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        @retry_decorator
        async def retried_func():
            return await func(*args, **kwargs)
        return await retried_func()
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        @retry_decorator
        def retried_func():
            return func(*args, **kwargs)
        return retried_func()
    
    # Return appropriate wrapper based on whether the function is async or not
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

class RetryOpenAIChatCompletionClient(OpenAIChatCompletionClient):
    """OpenAI chat completion client with exponential backoff retry logic for all methods."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply retry decorator to all methods from the parent class
        for name, method in inspect.getmembers(OpenAIChatCompletionClient, inspect.isfunction):
            if not name.startswith('_'):  # Skip private/special methods
                setattr(self, name, with_retry(getattr(self, name)))