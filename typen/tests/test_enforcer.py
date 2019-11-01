import unittest

from typen._enforcer import Enforcer
from typen.exceptions import (
    ParameterTypeError,
    ReturnTypeError,
    UnspecifiedParameterTypeError,
    UnspecifiedReturnTypeError,
)


class TestEnforcer(unittest.TestCase):
    def test_instantiate_vanilla_function(self):
        def example_function(a):
            pass

        Enforcer(example_function)  # No errors

    def test_instantiate_with_type_hints(self):
        def example_function(a: int, b, c: str, d) -> float:
            return 1.0

        Enforcer(example_function)  # No errors

    def test_instantiate_with_defaults(self):
        def example_function(a: int, b, c: str = "a", d=6) -> float:
            return 1.0

        Enforcer(example_function)  # No errors

    def test_instantiate_with_invalid_defaults(self):
        def example_function(a: int, b, c: int = "a", d=6) -> float:
            return 1.0

        with self.assertRaises(ParameterTypeError) as err:
            Enforcer(example_function)

        self.assertEqual(
            "The 'c' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 'a' <class 'str'> was specified.",
            str(err.exception)
        )

    def test_instantiate_return_type_validity_not_checked(self):
        def example_function(a: int, b, c: int = 1, d=6) -> float:
            return "asd"

        Enforcer(example_function)  # No errors

    def test_validate_args_vanilla_function(self):
        def example_function(a, b, c="a", d=6):
            return 1.0

        enforcer = Enforcer(example_function)

        enforcer.verify_args([1, 2, 3, "a"], {})

    def test_validate_args_with_type_hints(self):
        def example_function(a: int, b, c: str = "aa", d=5):
            pass

        enforcer = Enforcer(example_function)

        enforcer.verify_args([1, 2, "string", "string2"], {})
        enforcer.verify_args([], {"d": 10, "c": "bb", "b": "cc", "a": 2})

    def test_validate_args_invalid_args(self):
        def example_function(a: int, b, c: str = "aa", d=5):
            pass
        enforcer = Enforcer(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([1, "ok", 0, "ok"], {})

        self.assertEqual(
            "The 'c' parameter of 'example_function' must be <class 'str'>, "
            "but a value of 0 <class 'int'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([], {"d": 10, "c": "ok", "b": "cc", "a": "y"})

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 'y' <class 'str'> was specified.",
            str(err.exception)
        )

    def test_validate_args_multiple_invalid_args_order(self):
        def example_function(a: int, b, c: str = "aa", d=5):
            pass
        enforcer = Enforcer(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args(["bad", "ok", 0, "ok"], {})

        # The first invalid arg raises
        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 'bad' <class 'str'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([], {"d": 10, "c": 200, "b": "cc", "a": "y"})

        # The first invalid kwarg raises
        self.assertEqual(
            "The 'c' parameter of 'example_function' must be <class 'str'>, "
            "but a value of 200 <class 'int'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args(["y", "cc"], {"d": 10, "c": 200})

        # Arg raises before kwarg
        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 'y' <class 'str'> was specified.",
            str(err.exception)
        )


class TestStrictEnforcer(unittest.TestCase):
    pass


class TestEnforcerTraits(unittest.TestCase):
    pass
