import unittest

import numpy as np
from traits.api import Array, Either, Enum, Float, Instance, Int, Str, Tuple

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

    def test_validate_args_with_invalid_defaults(self):
        def example_function(a: int, b, c: int = "a", d=6) -> float:
            return 1.0
        enforcer = Enforcer(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([], {})

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

    def test_valdate_result_vanilla_function(self):
        def example_function(a, b, c, d):
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_result(10)

    def test_validate_result_with_type_hint(self):
        def example_function(a, b, c, d) -> str:
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_result("a")  # No errors

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result(6)

        self.assertEqual(
            "The return type of 'example_function' must be <class 'str'>, "
            "but a value of 6 <class 'int'> was returned.",
            str(err.exception)
        )
        # Invalid return value is added to the exception
        self.assertEqual(err.exception.return_value, 6)

    def test_widening_coercion(self):
        def example_function(a: float, b: float) -> float:
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args([1, 1], {})  # No errors
        enforcer.verify_result(1)  # No errors

    def test_narrowing_coercion(self):
        def example_function(a: int, b: int) -> int:
            pass
        enforcer = Enforcer(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([1.0, 2.0], {})

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'int'>, "
            "but a value of 1.0 <class 'float'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result(1.0)

        self.assertEqual(
            "The return type of 'example_function' must be <class 'int'>, "
            "but a value of 1.0 <class 'float'> was returned.",
            str(err.exception)
        )

    def test_validate_with_none(self):
        def example_function(a: None) -> None:
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args([None], {})
        enforcer.verify_result(None)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([0], {})

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be None, "
            "but a value of 0 <class 'int'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result(0)

        self.assertEqual(
            "The return type of 'example_function' must be None, "
            "but a value of 0 <class 'int'> was returned.",
            str(err.exception)
        )

    def test_validate_with_lists(self):
        def example_function(a: list) -> list:
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args([[1, 2, "a"]], {})
        enforcer.verify_result([])

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([(1, 2, "a")], {})

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be <class 'list'>, "
            "but a value of (1, 2, 'a') <class 'tuple'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result(tuple())

        self.assertEqual(
            "The return type of 'example_function' must be <class 'list'>, "
            "but a value of () <class 'tuple'> was returned.",
            str(err.exception)
        )


class TestStrictEnforcer(unittest.TestCase):
    def test_instantiate_with_missing_parameter_hints(self):
        def example_function(a, b: int, c):
            pass
        with self.assertRaises(UnspecifiedParameterTypeError) as err:
            Enforcer(example_function, require_args=True, require_return=False)

        self.assertEqual(
            "The following parameters must be given type hints: ['a', 'c']",
            str(err.exception)
        )

    def test_instantiate_with_missing_return_hint(self):
        def example_function(a, b: int, c):
            pass
        with self.assertRaises(UnspecifiedReturnTypeError) as err:
            Enforcer(example_function, require_args=False, require_return=True)

        self.assertEqual(
            "A return type hint must be specified.",
            str(err.exception)
        )


class TestEnforcerTraits(unittest.TestCase):
    def test_validate_trait_types(self):
        def example_function(a: Str, b: Int) -> Float:
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args(["aa", 0], {})
        enforcer.verify_args([], {"b": 0, "a": "string"})
        enforcer.verify_result(0.1)
        enforcer.verify_result(1)

    def test_validate_args_invalid_args(self):
        def example_function(a: Str, b: Int) -> Float:
            pass
        enforcer = Enforcer(example_function)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([90, 10], {})

        self.assertEqual(
            "The 'a' parameter of 'example_function' must be "
            "<class 'traits.trait_types.Str'>, but a value of 90 "
            "<class 'int'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result("bad")

        self.assertEqual(
            "The return type of 'example_function' must be "
            "<class 'traits.trait_types.Float'>, but a value of 'bad' "
            "<class 'str'> was returned.",
            str(err.exception)
        )

    def test_validete_with_invalid_defaults(self):
        def example_function(a: Str = "a", b: Int = "b"):
            pass
        enforcer = Enforcer(example_function)

        # Emulate passing no args, i.e. using defaults
        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args([], {})

        self.assertEqual(
            "The 'b' parameter of 'example_function' must be "
            "<class 'traits.trait_types.Int'>, but a value of 'b' "
            "<class 'str'> was specified.",
            str(err.exception)
        )

    def test_validate_either(self):
        def example_function(a: Either(Str, Int)) -> Either(Int, Str):
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args(["a"], {})
        enforcer.verify_args([1], {})
        enforcer.verify_result(2)
        enforcer.verify_result("b")

        with self.assertRaises(ParameterTypeError):
            enforcer.verify_args([1.0], {})

        with self.assertRaises(ReturnTypeError):
            enforcer.verify_result(1.0)

    def test_validate_enum(self):
        def example_function(
                a: Enum(1, 5, "c", 4.0)
                ) -> Enum(7, "d"):
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args([1], {})
        enforcer.verify_args([5], {})
        enforcer.verify_args(["c"], {})
        enforcer.verify_args([4.0], {})
        enforcer.verify_result(7)
        enforcer.verify_result("d")

        with self.assertRaises(ParameterTypeError):
            enforcer.verify_args([7], {})

        with self.assertRaises(ReturnTypeError):
            enforcer.verify_result("c")

    def test_validate_instance(self):
        class MyClass:
            pass

        class BabClass(MyClass):
            pass

        class UnrelatedClass:
            pass

        def example_function(a: Instance(MyClass)) -> Instance(BabClass):
            pass
        enforcer = Enforcer(example_function)

        parent = MyClass()
        child = BabClass()
        other = UnrelatedClass()

        enforcer.verify_args([parent], {})
        enforcer.verify_args([child], {})
        enforcer.verify_result(child)

        with self.assertRaises(ParameterTypeError):
            enforcer.verify_args([other], {})

        with self.assertRaises(ReturnTypeError):
            enforcer.verify_result(parent)

        with self.assertRaises(ReturnTypeError):
            enforcer.verify_result(other)

    def test_validate_array(self):
        def example_function(
                a: Array(dtype="float64", shape=(2, 2)),
                b: Array(dtype="float64", shape=(2, None)),
                c: Array(shape=(2, 2)),
                d: Array(dtype="float64"),
                e: Array(dtype="int64"),
                ) -> Array(dtype="int64"):
            pass
        enforcer = Enforcer(example_function)

        array_f22 = np.array([[1, 2], [3, 4]], dtype="float64")
        array_f32 = np.array([[1, 2], [3, 4], [5, 6]], dtype="float64")
        array_f23 = np.array([[1, 2, 3], [4, 5, 6]], dtype="float64")
        array_i22 = np.array([[1, 2], [3, 4]], dtype="int64")

        enforcer.verify_args(
            [array_f22, array_f22, array_f22, array_f22, array_i22], {})
        # N.B. numpy casting applies according to the "safe" rule
        enforcer.verify_args(
            [array_i22, array_f23, array_i22, array_i22, array_i22], {})
        enforcer.verify_result(array_i22)

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args(
                [array_f22, array_f32, array_i22, array_f32, array_i22], {})

        self.assertIn(
            "The 'b' parameter of 'example_function'",
            str(err.exception)
        )

        with self.assertRaises(ParameterTypeError) as err:
            enforcer.verify_args(
                [array_f22, array_f22, array_f22, array_f22, array_f22], {})

        self.assertEqual(
            "The 'e' parameter of 'example_function' could not be cast to an "
            "array of dtype dtype('int64')",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            enforcer.verify_result(array_f22)

        self.assertEqual(
            "The return value of 'example_function' could not be cast to an "
            "array of dtype dtype('int64')",
            str(err.exception)
        )

    def test_validate_tuple(self):
        def example_function(a: Tuple(Str, Int)) -> Tuple(Int, Str):
            pass
        enforcer = Enforcer(example_function)

        enforcer.verify_args([("a", 2)], {})
        enforcer.verify_result((2, "b"))

        with self.assertRaises(ParameterTypeError):
            enforcer.verify_args([(2, "a")], {})

        with self.assertRaises(ReturnTypeError):
            enforcer.verify_result(("b", 2))
