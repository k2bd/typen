import inspect

from traits.api import HasTraits, TraitError

from typen.exceptions import (
    ParameterTypeError,
    ReturnTypeError,
    UnspecifiedParameterTypeError,
    UnspecifiedReturnTypeError,
)

UNSPECIFIED = object()

#: List of methods exempt from strict return type annotation
RETURN_EXEMPT = ["__init__"]


class Enforcer:
    """
    This class is used to enforce type hints on a function.

    Generally it should be used through a typen decorator.

    Parameters
    ----------
    func : Callable
        The function whose type hints should be enforced
    require_args : bool
        Require all parameter type hints to be specified
    require_return : bool
        Require the return type hint to be specified
    ignore_self : bool
        If type hints are required, ignore the self-reference paramter of
        methods

    Raises
    ------
    UnspecifiedParameterTypeError
        If the parameter type hin is required but not provided
    UnspecifiedReturnTypeError
        If the return type hint is required but not provided
    """
    def __init__(
            self, func,
            require_args=False,
            require_return=False,
            ignore_self=False):
        self.func = func
        spec = func.__annotations__
        params = dict(inspect.signature(func).parameters)

        if ignore_self:
            require_return = require_return and func.__name__ not in RETURN_EXEMPT

        # Support for annotations on arg and kwarg packing
        self.packed_args = None
        self.packed_args_pos = None
        self.packed_kwargs = None
        self.num_normal_keywords = None
        for i, (name, param) in enumerate(list(params.items())):
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                self.packed_args_pos = i
                if name in spec:
                    self.packed_args = Arg(name, spec.pop(name))
                elif require_args:
                    msg = (
                        "Packed positional argument {!r} must be given a type "
                        "hint"
                    )
                    raise UnspecifiedParameterTypeError(msg.format(name))
                params.pop(name)
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                if name in spec:
                    self.packed_kwargs = Arg(name, spec.pop(name))
                elif require_args:
                    msg = (
                        "Packed keyword argument {!r} must be given a type "
                        "hint"
                    )
                    raise UnspecifiedParameterTypeError(msg.format(name))
                params.pop(name)
                self.num_normal_keywords = len(params)

        # If this is a method of some kind, ignore the first argument
        # (usually "self")
        self.ignored_self_name = None
        if ignore_self:
            self.ignored_self_name = list(params.keys())[0]

        if self.ignored_self_name is not None:
            params.pop(self.ignored_self_name)
            if self.ignored_self_name in spec:
                spec.pop(self.ignored_self_name)

        unspecified = {key: UNSPECIFIED for key in params.keys() if key not in spec}
        if unspecified and require_args:
            msg = "The following parameters of {!r} must be given type hints: {!r}"
            raise UnspecifiedParameterTypeError(
                msg.format(func.__name__, list(unspecified.keys()))
            )

        spec.update(unspecified)

        if "return" in spec.keys():
            self.returns = spec.pop("return")
        else:
            self.returns = UNSPECIFIED
            if require_return:
                msg = "A return type hint must be specified for {!r}."
                raise UnspecifiedReturnTypeError(msg.format(func.__name__))

        # Restore order of args
        self.args = [Arg(k, spec[k]) for k in params.keys()]

        # Store defaults to be validated if they're used
        self.default_kwargs = {
            k: v.default for k, v in params.items()
            if v.default is not inspect.Parameter.empty
        }

        fs = FunctionSignature()
        rt = FunctionSignature()

        for arg in self.args:
            fs.add_trait(arg.name, arg.type)
            arg.validator = fs.trait(arg.name)

        if self.packed_args is not None:
            fs.add_trait(self.packed_args.name, self.packed_args.type)
            self.packed_args.validator = fs.trait(self.packed_args.name)

        if self.packed_kwargs is not None:
            fs.add_trait(self.packed_kwargs.name, self.packed_kwargs.type)
            self.packed_kwargs.validator = fs.trait(self.packed_kwargs.name)

        rt.add_trait("result", self.returns)
        self.result_validator = rt.trait("result")

    def verify_args(self, passed_args, passed_kwargs):
        """
        Validate input args to a function.

        Parameters
        ----------
        passed_args : list
            List of args passed to the function
        passed_kwargs : dict
            Dict of kwargs passed to the function

        Raises
        ------
        ParameterTypeError
            If an input parameter is not valid based on is type hint
        """
        if self.ignored_self_name is not None:
            # Handle the corner case that self is passed as a kwarg
            if self.ignored_self_name in passed_kwargs:
                passed_kwargs = {
                    k: v for k, v in passed_kwargs.items()
                    if k != self.ignored_self_name
                }
            else:
                passed_args = passed_args[1:]

        packed_args = []
        packed_kwargs = {}
        if self.packed_args is not None:
            packed_args = passed_args[self.packed_args_pos:]
            passed_args = passed_args[:self.packed_args_pos]
        if self.packed_kwargs is not None:
            packed_kwargs = {
                key: passed_kwargs[key] for key in
                list(passed_kwargs.keys())[self.num_normal_keywords-1:]
            }
            passed_kwargs = {
                key: passed_kwargs[key] for key in
                list(passed_kwargs.keys())[:self.num_normal_keywords-1]
            }

        for i, arg in enumerate(self.args):
            if arg.type is UNSPECIFIED:
                continue

            if i < len(passed_args):
                value = passed_args[i]
            elif arg.name in passed_kwargs:
                value = passed_kwargs[arg.name]
            elif arg.name in self.default_kwargs:
                value = self.default_kwargs[arg.name]
            else:
                continue

            try:
                arg.validator.validate(None, None, value)
            except TraitError:
                msg = (
                    "The {!r} parameter of {!r} must be {!r}, "
                    "but a value of {!r} {!r} was specified."
                )
                raise ParameterTypeError(
                    msg.format(
                        arg.name, self.func.__name__, arg.type, value, type(value))
                ) from None

        if self.packed_args is not None:
            for value in packed_args:
                try:
                    self.packed_args.validator.validate(None, None, value)
                except TraitError:
                    msg = (
                        "The {!r} parameters of {!r} must be {!r}, "
                        "but a value of {!r} {!r} was specified."
                    )
                    raise ParameterTypeError(
                        msg.format(
                            self.packed_args.name,
                            self.func.__name__,
                            self.packed_args.type,
                            value,
                            type(value)
                        )
                    ) from None
        if self.packed_kwargs is not None:
            for key, value in packed_kwargs.items():
                try:
                    self.packed_kwargs.validator.validate(None, None, value)
                except TraitError:
                    msg = (
                        "The {!r} keywords of {!r} must have values of type "
                        "{!r}, but {!r}:{!r} {!r} was specified."
                    )
                    raise ParameterTypeError(
                        msg.format(
                            self.packed_kwargs.name,
                            self.func.__name__,
                            self.packed_kwargs.type,
                            key,
                            value,
                            type(value),
                        )
                    ) from None

    def verify_result(self, value):
        """
        Validate return value of the function call

        Parameters
        ----------
        value : Any
            The return value of the function

        Raises
        ------
        ReturnTypeError
            If the return value is of the wrong type according to the type
            hint. Note that the computed return value is stored on the
            ``return_value`` attribute of the exception.
        """
        if self.returns is UNSPECIFIED:
            return

        try:
            self.result_validator.validate(None, None, value)
        except TraitError:
            msg = (
                "The return type of {!r} must be {!r}, "
                "but a value of {!r} {!r} was returned."
            )
            exception = ReturnTypeError(
                msg.format(self.func.__name__, self.returns, value, type(value)))
            exception.return_value = value
            raise exception from None


class FunctionSignature(HasTraits):
    pass


class Arg:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.validator = None
