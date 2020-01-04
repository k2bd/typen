class UnspecifiedParameterTypeError(Exception):
    """
    Parameter type hint required but not specified
    """
    pass


class UnspecifiedReturnTypeError(Exception):
    """
    Return type hint required but not specified
    """
    pass


class ParameterTypeError(Exception):
    """
    Passed parameter is invalid
    """
    pass


class ReturnTypeError(Exception):
    """
    Return type is invalid
    """
    pass


class TypenError(Exception):
    """
    General Typen error.
    """
    pass
