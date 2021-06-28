from functools import wraps


class BaseDecorator:
    """Base decorator class"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper._args = self.args
        wrapper._kwargs = self.kwargs
        return wrapper
