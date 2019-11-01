from functools import wraps

from typen._enforcer import Enforcer


def enforce_type_hints(func):
    """
    Enforce type hints on the parameters and return types decorated function.
    """
    return configure_enforce_type_hints(require_args=False, require_return=False)(func)


def strict_type_hints(func):
    """
    Enforce type hints on the parameters and return types decorated function.

    Also require type hints to be provided for all args and the return value.
    """
    return configure_enforce_type_hints(require_args=True, require_return=True)(func)


def configure_enforce_type_hints(require_args=False, require_return=False):
    def inner(func):
        enforcer = Enforcer(
            func,
            require_args=require_args,
            require_return=require_return,
        )

        @wraps(func)
        def new_func(*args, **kwargs):
            enforcer.verify_args(args, kwargs)
            result = func(*args, **kwargs)
            enforcer.verify_result(result)
            return result

        return new_func

    return inner
