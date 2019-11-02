import unittest

from typen._decorators import (
    enforce_type_hints,
    strict_parameter_hints,
    strict_return_hint,
    strict_type_hints,
)
from typen.exceptions import (
    ParameterTypeError,
    ReturnTypeError,
    UnspecifiedParameterTypeError,
    UnspecifiedReturnTypeError,
)


# Note: Most functionality tests are found in test_enforcer.py
class TestEnforceTypeHints(unittest.TestCase):
    def test_enforce_type_hints_vanilla(self):
        def example_function(a, b):
            return a+b
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(1, 2), 3)

    def test_enforce_type_hints_parameters_with_hints(self):
        def example_function(a: int, b: int) -> int:
            return a+b
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(1, 2), 3)

        with self.assertRaises(ParameterTypeError) as err:
            new_func(1.0, 2)

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 1.0 <class 'float'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ParameterTypeError) as err:
            new_func(b=1.0, a=2.0)

        self.assertEqual(
            "The 'b' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 1.0 <class 'float'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_return_with_hints(self):
        def example_function(a) -> int:
            return a
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(1), 1)

        with self.assertRaises(ReturnTypeError) as err:
            new_func("a")

        self.assertEqual(
            "The return type of 'example_function' must be <class 'int'>, "
            "but a value of 'a' <class 'str'> was returned.",
            str(err.exception)
        )
        self.assertEqual("a", err.exception.return_value)

    def test_enforce_type_hints_return_coercibility(self):
        def example_function(a: float, b: float) -> float:
            return a + b
        new_func = enforce_type_hints(example_function)

        # Result is not cast to a float
        result = new_func(2, 3)
        self.assertEqual(result, 5)
        self.assertIsInstance(result, int)

    def test_enforce_type_hints_defaults(self):
        def example_function(a: int = 5, b: int = 6) -> int:
            return a + b
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(), 11)

    def test_enforce_type_hints_invalid_defaults(self):
        def example_function(a: int = 0.5, b: int = 6) -> int:
            return a + b
        new_func = enforce_type_hints(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            new_func()

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 0.5 <class 'float'> was specified.",
            str(err.exception)
        )

    #def test_enforce_type_hints_on_method(self):
    #    class ExClass:
    #        def __init__(self, a: int, b: int):
    #            self.a = a
    #            self.b = b
#
    #        @enforce_type_hints
    #        def ex_method(self, c: int) -> int:
    #            return self.a + self.b + c
#
    #    inst = ExClass(1, 2)
    #    inst.ex_method(6)
#
#TODO: test strict decorators on methods
#TODO: test passing self as kwarg
#TODO: test self not named self
#TODO: test all the kinds of methods here https://stackoverflow.com/questions/19314405/how-to-detect-is-decorator-has-been-applied-to-method-or-function
#TODO: update documentation if defaults aren't checked on decoration
