import functools
import inspect
from typing import Awaitable, Callable, Concatenate, ParamSpec, Type, TypeVar

import redis
import redis.asyncio as redis_sync
import redis.asyncio.client as redis_async_client

# Generic type for a function that takes a pipeline and some other parameters
P = ParamSpec("P")
R = TypeVar("R")


def pipeline_watch(
    redis_pool: redis_sync.Redis,
    watch_param_name: str,
    key_not_found_excepton: Type[Exception] = ValueError,
):
    """
    Decorator for setting a watch and pipeline on some data.

    IMPORTANT: To use this decorator the wrapped function must
    be asyncronous and accept an asyncronous redis pipeline as
    its first parameter

    Parameters:
        redis_pool[redis_sync.Redis]:
            redis pool to use the operation

        watch_param_name[str]:
            name of the parameter in the decorated function to watch

        key_not_found_excepton[Optional[Exception]]:
            Exception to raise if key to watch is not found
    """

    def decorator(
        fn: Callable[Concatenate[redis_async_client.Pipeline, P], Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Gets signature of the wrapped function
            func_sig = inspect.signature(fn)

            # This works because the paramter we need to pass to will always be the first one
            # because of the type definition of this decorator
            func_params = func_sig.bind(None, *args, **kwargs)

            # Makes sure the watch param exists
            if watch_param_name in func_params.arguments:
                watch_data = func_params.arguments[watch_param_name]

                async with redis_pool.pipeline() as pipe:
                    await pipe.watch(watch_data)
                    # Make sure game exists while operating on it
                    # and reruns function till it completes without a watch error
                    while await pipe.exists(watch_data):
                        try:
                            return await fn(pipe, *args, **kwargs)
                        except redis.WatchError:
                            continue

                    raise key_not_found_excepton(
                        f"key {watch_param_name} not found in db"
                    )

            else:
                raise TypeError("Missing required parameter: " + watch_param_name)

        return wrapper

    return decorator