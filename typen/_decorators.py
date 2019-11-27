from functools import wraps

from typen._enforcer import Enforcer


def enforce_type_hints(func):
    """
    Enforce type hints on the parameters and return types of the decorated
    function.
    """
    return EnforceTypeHints(func, require_args=False, require_return=False)


def strict_type_hints(func):
    """
    Enforce type hints on the parameters and return types of the decorated
    function.

    Also require type hints to be provided for all parmeters and the return
    value.
    """
    return EnforceTypeHints(func, require_args=True, require_return=True)


def strict_parameter_hints(func):
    """
    Enforce type hints on the parameters and return types of the decorated
    function.

    Also require type hints to be provided for all parameters.

    Note: This decorator does NOT stack with ``strict_return_hints``. Please
    use ``strict_type_hints`` to enforce both parameter and return value hints.
    """
    return EnforceTypeHints(func, require_args=True, require_return=False)


def strict_return_hint(func):
    """
    Enforce type hints on the parameters and return types of the decorated
    function.

    Also require a type hint to be provided for the return type.

    Note: This decorator does NOT stack with ``strict_parameter_hints``. Please
    use ``strict_type_hints`` to enforce both parameter and return value hints.
    """
    return EnforceTypeHints(func, require_args=False, require_return=True)


class EnforceTypeHints:
    def __init__(self, func, require_args, require_return):
        self.func = func
        self.enforcer = None
        self.require_args = require_args
        self.require_return = require_return

    def __call__(self, *args, **kwargs):
        if self.enforcer is None:
            self.decorate()

        return self.decorated_func(*args, **kwargs)

    def __set_name__(self, owner, name):
        # This is called on class creation so we can distinguish methods
        # from non-methods

        ignore_self = True

        # Get the actual function if this is a static or class method
        desc = None
        if isinstance(self.func, staticmethod):
            # Static methods don't take a `self` parameter
            desc = staticmethod
            ignore_self = False
        elif isinstance(self.func, classmethod):
            desc = classmethod

        if desc:
            self.func = self.func.__func__

        self.decorate(ignore_self=ignore_self)

        if desc:
            self.decorated_func = desc(self.decorated_func)
        setattr(owner, name, self.decorated_func)

    def decorate(self, ignore_self=False):
        self.enforcer = Enforcer(
            self.func,
            require_args=self.require_args,
            require_return=self.require_return,
            ignore_self=ignore_self,
        )

        @wraps(self.func)
        def new_func(*args, **kwargs):
            self.enforcer.verify_args(args, kwargs)
            result = self.func(*args, **kwargs)
            self.enforcer.verify_result(result)
            return result

        self.decorated_func = new_func

