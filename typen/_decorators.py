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

    Also require type hints to be provided for all parmeters and the return
    value.
    """
    return configure_enforce_type_hints(require_args=True, require_return=True)(func)


def strict_parameter_hints(func):
    """
    Enforce type hints on the parameters and return types decorated function.

    Also require type hints to be provided for all parameters.

    Note: This decorator does NOT stack with ``strict_return_hints``. Please
    use ``strict_type_hints`` to enforce both parameter and return value hints.
    """
    return configure_enforce_type_hints(require_args=True, require_return=False)(func)


def strict_return_hint(func):
    """
    Enforce type hints on the parameters and return types decorated function.

    Also require a type hint to be provided for the return type.

    Note: This decorator does NOT stack with ``strict_parameter_hints``. Please
    use ``strict_type_hints`` to enforce both parameter and return value hints.
    """
    return configure_enforce_type_hints(require_args=False, require_return=True)(func)


def configure_enforce_type_hints(require_args=False, require_return=False):
    def inner(func):
        #desc = next(
        #    (
        #        desc for desc in (staticmethod, classmethod)
        #        if isinstance(func, desc)
        #    ), None
        #)
        #if desc:
        #    func = func.__func__

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
