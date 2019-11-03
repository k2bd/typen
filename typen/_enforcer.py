import inspect
import random
from string import ascii_lowercase

import numpy as np

from traits.api import Any, Array, HasTraits, TraitError

from typen.exceptions import (
    ParameterTypeError,
    ReturnTypeError,
    TypenError,
    UnspecifiedParameterTypeError,
    UnspecifiedReturnTypeError,
)

UNSPECIFIED = object()


class Enforcer:
    def __init__(
            self, func,
            require_args=False,
            require_return=False,
            ignore_self=False):
        self.func = func
        spec = func.__annotations__
        params = dict(inspect.signature(func).parameters)

        # Support for annotations on arg and kwarg packing
        self.packed_args_name = None
        self.packed_args_pos = None
        self.packed_args_spec = UNSPECIFIED
        self.packed_kwargs_name = None
        self.num_normal_keywords = None
        self.packed_kwargs_spec = UNSPECIFIED
        for i, (name, param) in enumerate(list(params.items())):
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                self.packed_args_name = name
                self.packed_args_pos = i
                if name in spec:
                    self.packed_args_spec = spec.pop(name)
                elif require_args:
                    msg = (
                        "Packed positional argument {!r} must be given a type "
                        "hint"
                    )
                    raise UnspecifiedParameterTypeError(msg.format(name))#TODO:TEST
                params.pop(name)
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                self.packed_kwargs_name = name
                if name in spec:
                    self.packed_kwargs_spec = spec.pop(name)
                elif require_args:
                    msg = (
                        "Packed keyword argument {!r} must be given a type "
                        "hint"
                    )
                    raise UnspecifiedParameterTypeError(msg.format(name))#TODO:TEST
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

        # Handle the edge case that we have an actual arg named "self"
        # This is done by replacing the "self" attribute for validation with a
        # random name.
        self._self = None
        if "self" in params:
            self._self = random_attribute_name()
            params[self._self] = params.pop("self")
            if "self" in spec:
                spec[self._self] = spec.pop("self")

        unspecified = {key: UNSPECIFIED for key in params.keys() if key not in spec}
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
            self.returns = UNSPECIFIED

        # Restore order of args
        self.args = [Arg(k, spec[k]) for k in params.keys()]

        # Validate defaults
        self.default_kwargs = {
            k: v.default for k, v in params.items()
            if v.default is not inspect.Parameter.empty
        }

        class FunctionSignature(HasTraits):
            pass

        fs = FunctionSignature()
        rt = FunctionSignature()

        for arg in self.args:
            fs.add_trait(arg.name, arg.type)
            arg.validator = fs.trait(arg.name)

        if self.packed_args_spec is not UNSPECIFIED:
            fs.add_trait(self.packed_args_name, self.packed_args_spec)
            self.packed_args_validator = fs.trait(self.packed_args_name)

        if self.packed_kwargs_spec is not UNSPECIFIED:
            fs.add_trait(self.packed_kwargs_name, self.packed_kwargs_spec)
            self.packed_kwargs_validator = fs.trait(self.packed_kwargs_name)

        rt.add_trait("result", self.returns)
        self.result_validator = rt.trait("result")

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

        packed_args = []
        packed_kwargs = {}
        if self.packed_args_name is not None:
            packed_args = passed_args[self.packed_args_pos:]
            passed_args = passed_args[:self.packed_args_pos]
        if self.packed_kwargs_name is not None:
            packed_kwargs = {
                key: passed_kwargs[key] for key in
                list(passed_kwargs.keys())[self.num_normal_keywords-1:]
            }
            passed_kwargs = {
                key: passed_kwargs[key] for key in
                list(passed_kwargs.keys())[:self.num_normal_keywords-1]
            }

        traits = {}
        for i, arg in enumerate(passed_args):
            expt_arg = self.args[i]
            traits[expt_arg.name] = arg
        traits.update(**passed_kwargs)

        # Handle the corner case that "self" is the name of a normal parameter
        if "self" in traits:
            traits[self._self] = traits.pop("self")

        for key, value in self.default_kwargs.items():
            if key not in traits:
                traits[key] = value

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

        for arg in self.args:
            if arg.type is UNSPECIFIED:
                continue
            if arg.name in traits:
                value = traits[arg.name]
                try:
                    arg.validator.validate(None, None, value)
                except TraitError:
                    msg = (
                        "The {!r} parameter of {!r} must be {!r}, "
                        "but a value of {!r} {!r} was specified."
                    )
                    raise ParameterTypeError(
                        msg.format(arg.name, self.func.__name__, arg.type, value, type(value))
                    ) from None

        if self.packed_args_spec is not UNSPECIFIED:
            for value in packed_args:
                try:
                    self.packed_args_validator.validate(None, None, value)
                except TraitError:
                    msg = (
                        "The {!r} parameters of {!r} must be {!r}, "
                        "but a value of {!r} {!r} was specified."
                    )
                    raise ParameterTypeError(
                        msg.format(
                            self.packed_args_name,
                            self.func.__name__,
                            self.packed_args_spec,
                            value,
                            type(value)
                        )
                    ) from None
        if self.packed_kwargs_spec is not UNSPECIFIED:
            for key, value in packed_kwargs.items():
                try:
                    self.packed_kwargs_validator.validate(None, None, value)
                except TraitError:
                    msg = (
                        "The {!r} keywords of {!r} must have values of type "
                        "{!r}, but {!r}:{!r} {!r} was specified."
                    )
                    raise ParameterTypeError(
                        msg.format(
                            self.packed_kwargs_name,
                            self.func.__name__,
                            self.packed_kwargs_spec,
                            key,
                            value,
                            type(value),
                        )
                    ) from None

    def verify_result(self, value):
        if self.returns is UNSPECIFIED:
            return

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


class Arg:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.validator = None


def random_attribute_name():
    return "".join(random.choice(ascii_lowercase) for _ in range(15))
