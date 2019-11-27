import sys
import typing

import traits.api as traits_api

from typen.exceptions import TypenError


if sys.version_info[1] == 8:
    typing_generic = typing.GenericMeta
else:
    typing_generic = typing.Generic


def typing_to_trait(arg_type):
    """
    Attempt to convert a ``typing`` type into an appropriate ``traits`` type
    """
    if arg_type.__class__ is not typing.GenericMeta:
        return arg_type
    origin = arg_type.__origin__

    if origin is typing.List:
        contained = arg_type.__args__[0]
        return traits_api.List(typing_to_trait(contained))

    raise TypenError("Could not convert typing type to trait: {}".format(arg_type))
