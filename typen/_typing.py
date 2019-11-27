import sys
import typing

import traits.api as traits_api

from typen.exceptions import TypenError


if sys.version_info[1] == 8:
    typing_generic = typing.Generic
else:
    typing_generic = typing.GenericMeta


def typing_to_trait(arg_type):
    """
    Attempt to convert a ``typing`` type into an appropriate ``traits`` type

    Raises
    ------
    TypenError
        If the input type is a ``typing`` type but it could not be converted
        to a traits type. This may be because the type is not currently
        supported.
    """
    if arg_type.__class__ is not typing_generic:
        return arg_type

    origin = arg_type.__origin__ or arg_type

    if origin is typing.List:
        if arg_type.__args__ is not None:
            contained = arg_type.__args__[0]
            temp=typing_to_trait(contained)
            print(temp)
            return traits_api.List(temp)
        else:
            return traits_api.List()

    raise TypenError("Could not convert {} to trait".format(arg_type))
