import typing

import traits.api as traits_api

from typen.exceptions import TypenError


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

    if not hasattr(arg_type, "__origin__"):
        return arg_type

    origin = arg_type.__origin__ or arg_type

    if origin is typing.List:
        if arg_type.__args__ is not None:
            contained = arg_type.__args__[0]
            return ValidatedList(typing_to_trait(contained))
        else:
            return traits_api.List()
    elif origin is typing.Tuple:
        if arg_type.__args__ is not None:
            contained = [typing_to_trait(arg) for arg in arg_type.__args__]
            return traits_api.Tuple(*contained)
        else:
            return traits_api.Tuple()

    raise TypenError("Could not convert {} to trait".format(arg_type))


class ValidatedList(traits_api.List):
    """
    Defines a list that does validation on the internal type
    """

    def validate(self, object, name, value):
        value = super(ValidatedList, self).validate(object, name, value)

        for item in value:
            self.item_trait.validate(object, name, item)
