import inspect
import random
from string import ascii_lowercase

import numpy as np

from traits.api import Any, Array, HasTraits, TraitError

from typen.exceptions import (
    ParameterTypeError,
    ReturnTypeError,
    UnspecifiedParameterTypeError,
    UnspecifiedReturnTypeError,
)


class Enforcer:
    def __init__(
            self, func,
            require_args=False,
            require_return=False,
            ignore_self=False):
        self.func = func
        spec = func.__annotations__
        params = dict(inspect.signature(func).parameters)

        # If this is a method of some kind, ignore the first argument
        # (usually "self")
        self.ignored_self_name = None
        if ignore_self:
            self.ignored_self_name = list(params.keys())[0]

        if self.ignored_self_name is not None:
            params.pop(self.ignored_self_name)
            # Ignore any annotations on self
            #TODO:test
            if self.ignored_self_name in spec:
                spec.pop(self.ignored_self_name)

        # Handle the edge case that we have an actual arg named "self"
        # This is done by replacing the "self" attribute for validation with a
        # random name.
        self._self = None
        if "self" in params:
            self._self = "".join(
                random.choice(ascii_lowercase) for _ in range(15))
            params[self._self] = params.pop("self")
            spec[self._self] = spec.pop("self")

        unspecified = {key: Any for key in params.keys() if key not in spec}
        if unspecified and require_args:
            msg = "The following parameters must be given type hints: {!r}"
            raise UnspecifiedParameterTypeError(msg.format(list(unspecified.keys())))

        spec.update(unspecified)

        if "return" in spec.keys():
            self.returns = spec.pop("return")
        else:
            if require_return:
                msg = "A return type hint must be specified."
                raise UnspecifiedReturnTypeError(msg)
            self.returns = Any

        # Restore order of args
        self.args = [Arg(k, spec[k]) for k in params.keys()]

        # Validate defaults
        self.default_kwargs = {
            k: v.default for k, v in params.items()
            if v.default is not inspect.Parameter.empty
        }

    def verify_args(self, passed_args, passed_kwargs):

        if self.ignored_self_name is not None:
            # handle the rare case that self is passed as a kwarg
            #TODO:test
            if self.ignored_self_name in passed_kwargs:
                passed_kwargs = {
                    k: v for k, v in passed_kwargs.items()
                    if k != self.ignored_self_name
                }
            else:
                passed_args = passed_args[1:]

        class FunctionSignature(HasTraits):
            pass

        fs = FunctionSignature()

        for arg in self.args:
            fs.add_trait(arg.name, arg.type)

        traits = {}
        for i, arg in enumerate(passed_args):
            expt_arg = self.args[i]
            traits[expt_arg.name] = arg
        traits.update(**passed_kwargs)

        for key, value in self.default_kwargs.items():
            if key not in traits:
                traits[key] = value

        # Handle the corner case that "self" is a normal arg
        if "self" in traits:
            traits[self._self] = traits.pop("self")

        # Extra validation for numpy array dtypes
        for arg in self.args:
            arg_name = arg.name
            arg_type = arg.type
            if arg_name not in traits:
                continue
            trait = traits[arg_name]
            if isinstance(arg_type, Array) and isinstance(trait, np.ndarray):
                try:
                    traits[arg_name].astype(arg_type.dtype, casting="safe")
                except TypeError:
                    msg = (
                        "The {!r} parameter of {!r} could not be cast to an "
                        "array of dtype {!r}"
                    )
                    raise ParameterTypeError(
                        msg.format(
                            arg_name,
                            self.func.__name__,
                            arg_type.dtype
                        )
                    )

        try:
            fs.trait_set(**traits)
        except TraitError as err:
            name = err.name
            expt_type, = [arg.type for arg in self.args if arg.name == name]
            value = traits[name]
            msg = (
                "The {!r} parameter of {!r} must be {!r}, "
                "but a value of {!r} {!r} was specified."
            )
            raise ParameterTypeError(
                msg.format(name, self.func.__name__, expt_type, value, type(value))
            ) from None

    def verify_result(self, value):
        class ReturnType(HasTraits):
            pass

        rt = ReturnType()
        rt.add_trait("result", self.returns)

        # Extra validation for numpy array dtypes
        if isinstance(self.returns, Array) and isinstance(value, np.ndarray):
            try:
                value.astype(self.returns.dtype, casting="safe")
            except TypeError:
                msg = (
                    "The return value of {!r} could not be cast to an array"
                    " of dtype {!r}"
                )
                exception = ReturnTypeError(
                    msg.format(self.func.__name__, self.returns.dtype)
                )
                exception.return_value = value
                raise exception

        try:
            rt.trait_set(result=value)
        except TraitError:
            msg = (
                "The return type of {!r} must be {!r}, "
                "but a value of {!r} {!r} was returned."
            )
            exception = ReturnTypeError(
                msg.format(self.func.__name__, self.returns, value, type(value)))
            exception.return_value = value
            raise exception from None


class Arg:
    def __init__(self, name, type):
        self.name = name
        self.type = type
