import unittest

from traits.api import Float, Int, List, Str

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


# Note: Type checking is found in test_enforcer.py
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

    def test_enforce_type_hints_packed_args_vanilla(self):
        def example_function(a, *args, b=5, c=6):
            return sum([a, *args, b, c])
        new_func = enforce_type_hints(example_function)

        result = new_func(1, 2, 3, b=3, c=2)
        self.assertEqual(result, 11)

    def test_enforce_type_hints_packed_args_hint(self):
        def example_function(a: int, b: float, *args: str):
            return str(a) + str(b) + "".join(str(arg) for arg in args)
        new_func = enforce_type_hints(example_function)

        result = new_func(1, 0.5, "a", "b", "c")
        self.assertEqual(result, "10.5abc")

        result = new_func(2, 3.0)
        self.assertEqual(result, "23.0")

        with self.assertRaises(ParameterTypeError) as err:
            new_func(1, 0.5, "a", "b", "c", 6)

        self.assertEqual(
            "The 'args' parameters of 'example_function' must be "
            "<class 'str'>, but a value of 6 <class 'int'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_packed_kwargs_vanilla(self):
        def example_function(a, b, **kwargs):
            return (a, b, *kwargs.keys(), *kwargs.values())
        new_func = enforce_type_hints(example_function)

        result = new_func(1, 2, y=2, z="v", x=4.5)
        self.assertEqual(
            (1, 2, "y", "z", "x", 2, "v", 4.5),
            result
        )

    def test_enforce_type_hints_packed_kwargs_hint(self):
        def example_function(a: float, b: float, **kwargs: str):
            return (a, b, *kwargs.keys(), *kwargs.values())
        new_func = enforce_type_hints(example_function)

        result = new_func(0.5, 1.0, y="a", word="bird", g="c")
        self.assertEqual(
            (0.5, 1.0, "y", "word", "g", "a", "bird", "c"),
            result
        )

        result = new_func(0.5, 2.0)
        self.assertEqual((0.5, 2.0), result)

        with self.assertRaises(ParameterTypeError) as err:
            new_func(0.5, 1.0, g="r", word=10)

        self.assertEqual(
            "The 'kwargs' keywords of 'example_function' must have values of "
            "type <class 'str'>, but 'word':10 <class 'int'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_packed_args_kwargs_vanilla(self):
        pass

    def test_enforce_type_hints_packed_args_kwargs_hint(self):
        pass

    def test_enforce_type_hints_packed_args_kwargs_method(self):
        pass

    def test_enforce_type_hints_on_init_method(self):
        class ExClass:
            @enforce_type_hints
            def __init__(self, a: int, b: str):
                self.a = a
                self.b = b

        ExClass(1, "b")

        with self.assertRaises(ParameterTypeError) as err:
            ExClass("a", "b")

        self.assertEqual(
            "The 'a' parameter of '__init__' must be <class 'int'>, "
            "but a value of 'a' <class 'str'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_on_method(self):
        class ExClass:
            @enforce_type_hints
            def __init__(self, a: int, b: int):
                self.a = a
                self.b = b

            @enforce_type_hints
            def ex_method(self, c: int, d) -> int:
                return self.a + self.b + c + d

        inst = ExClass(1, 2)
        self.assertEqual(
            inst.ex_method(6, 0), 9
        )

        with self.assertRaises(ParameterTypeError) as err:
            inst.ex_method(1.0, 2)

        self.assertEqual(
            "The 'c' parameter of 'ex_method' must be <class 'int'>, but a "
            "value of 1.0 <class 'float'> was specified.",
            str(err.exception)
        )

        with self.assertRaises(ReturnTypeError) as err:
            inst.ex_method(1, 1.0)

        self.assertEqual(
            "The return type of 'ex_method' must be <class 'int'>, "
            "but a value of 5.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(5.0, err.exception.return_value)

    def test_enforce_type_hints_on_method_self_not_named_self_params(self):
        class ExClass:
            @enforce_type_hints
            def __init__(this, self):
                this.self = self

            @enforce_type_hints
            def ex_method(this, self: int) -> int:
                return this.self + self

        inst = ExClass(1)
        self.assertEqual(inst.ex_method(6), 7)

        inst = ExClass(self=1)
        self.assertEqual(inst.ex_method(self=6), 7)

    def test_enforce_type_hints_on_method_self_not_named_self_return(self):
        class ExClass:
            @enforce_type_hints
            def __init__(this, self: int):
                this.self = self

            @enforce_type_hints
            def ex_method(this, self) -> int:
                return this.self*self

        inst = ExClass(2)
        self.assertEqual(inst.ex_method(5), 10)

        with self.assertRaises(ReturnTypeError) as err:
            inst.ex_method(5.0)

        self.assertEqual(
            "The return type of 'ex_method' must be <class 'int'>, "
            "but a value of 10.0 <class 'float'> was returned.",
            str(err.exception)
        )

    def test_enforce_type_hints_on_class_method_params(self):
        class ExClass:
            @enforce_type_hints
            def __init__(self, a: int, b: int):
                self.a = a
                self.b = b

            @classmethod
            @enforce_type_hints
            def ex_method1(cls, a: int, c: int) -> int:
                return a + c

            @enforce_type_hints
            @classmethod
            def ex_method2(cls, a: int, c: int) -> int:
                return a + c

        result = ExClass.ex_method1(2, 4)
        self.assertEqual(result, 6)
        with self.assertRaises(ParameterTypeError) as err:
            ExClass.ex_method1("a", 4)

        self.assertEqual(
            "The 'a' parameter of 'ex_method1' must be <class 'int'>, "
            "but a value of 'a' <class 'str'> was specified.",
            str(err.exception)
        )

        result = ExClass.ex_method2(5, 4)
        self.assertEqual(result, 9)

        with self.assertRaises(ParameterTypeError) as err:
            ExClass.ex_method2("b", 4)

        self.assertEqual(
            "The 'a' parameter of 'ex_method2' must be <class 'int'>, "
            "but a value of 'b' <class 'str'> was specified.",
            str(err.exception)
        )

        inst = ExClass(1, 2)
        result = inst.ex_method1(5, 3)
        self.assertEqual(result, 8)

        with self.assertRaises(ParameterTypeError) as err:
            inst.ex_method1("c", 5)

        self.assertEqual(
            "The 'a' parameter of 'ex_method1' must be <class 'int'>, "
            "but a value of 'c' <class 'str'> was specified.",
            str(err.exception)
        )

        result = inst.ex_method2(9, 3)
        self.assertEqual(result, 12)

        with self.assertRaises(ParameterTypeError) as err:
            inst.ex_method2("d", 5)

        self.assertEqual(
            "The 'a' parameter of 'ex_method2' must be <class 'int'>, "
            "but a value of 'd' <class 'str'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_on_class_method_return(self):
        class ExClass:
            @classmethod
            @enforce_type_hints
            def ex_method1(cls, self) -> int:
                return self * 2

            @enforce_type_hints
            @classmethod
            def ex_method2(cls, self) -> int:
                return self * 2

        result = ExClass.ex_method1(4)
        self.assertEqual(result, 8)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass.ex_method1(6.0)

        self.assertEqual(
            "The return type of 'ex_method1' must be <class 'int'>, "
            "but a value of 12.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(12.0, err.exception.return_value)

        result = ExClass.ex_method2(5)
        self.assertEqual(result, 10)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass.ex_method2(7.0)

        self.assertEqual(
            "The return type of 'ex_method2' must be <class 'int'>, "
            "but a value of 14.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(14.0, err.exception.return_value)

        result = ExClass().ex_method1(6)
        self.assertEqual(result, 12)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass().ex_method1(8.0)

        self.assertEqual(
            "The return type of 'ex_method1' must be <class 'int'>, "
            "but a value of 16.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(16.0, err.exception.return_value)

        result = ExClass().ex_method2(7)
        self.assertEqual(result, 14)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass().ex_method2(9.0)

        self.assertEqual(
            "The return type of 'ex_method2' must be <class 'int'>, "
            "but a value of 18.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(18.0, err.exception.return_value)

    def test_enforce_type_hints_on_static_method_params(self):
        class ExClass:
            @enforce_type_hints
            def __init__(self, a: int, b: int):
                self.a = a
                self.b = b

            @staticmethod
            @enforce_type_hints
            def ex_method1(a: int, c: int) -> int:
                return a + c

            @enforce_type_hints
            @staticmethod
            def ex_method2(a: int, c: int) -> int:
                return a + c

        result = ExClass.ex_method1(2, 4)
        self.assertEqual(result, 6)
        with self.assertRaises(ParameterTypeError) as err:
            ExClass.ex_method1("a", 4)

        self.assertEqual(
            "The 'a' parameter of 'ex_method1' must be <class 'int'>, "
            "but a value of 'a' <class 'str'> was specified.",
            str(err.exception)
        )

        result = ExClass.ex_method2(5, 4)
        self.assertEqual(result, 9)

        with self.assertRaises(ParameterTypeError) as err:
            ExClass.ex_method2("b", 4)

        self.assertEqual(
            "The 'a' parameter of 'ex_method2' must be <class 'int'>, "
            "but a value of 'b' <class 'str'> was specified.",
            str(err.exception)
        )

        inst = ExClass(1, 2)
        result = inst.ex_method1(5, 3)
        self.assertEqual(result, 8)

        with self.assertRaises(ParameterTypeError) as err:
            inst.ex_method1("c", 5)

        self.assertEqual(
            "The 'a' parameter of 'ex_method1' must be <class 'int'>, "
            "but a value of 'c' <class 'str'> was specified.",
            str(err.exception)
        )

        result = inst.ex_method2(9, 3)
        self.assertEqual(result, 12)

        with self.assertRaises(ParameterTypeError) as err:
            inst.ex_method2("d", 5)

        self.assertEqual(
            "The 'a' parameter of 'ex_method2' must be <class 'int'>, "
            "but a value of 'd' <class 'str'> was specified.",
            str(err.exception)
        )

    def test_enforce_type_hints_on_static_method_return(self):
        class ExClass:
            @staticmethod
            @enforce_type_hints
            def ex_method1(self) -> int:
                return self * 2

            @enforce_type_hints
            @staticmethod
            def ex_method2(self) -> int:
                return self * 2

        result = ExClass.ex_method1(4)
        self.assertEqual(result, 8)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass.ex_method1(6.0)

        self.assertEqual(
            "The return type of 'ex_method1' must be <class 'int'>, "
            "but a value of 12.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(12.0, err.exception.return_value)

        result = ExClass.ex_method2(5)
        self.assertEqual(result, 10)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass.ex_method2(7.0)

        self.assertEqual(
            "The return type of 'ex_method2' must be <class 'int'>, "
            "but a value of 14.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(14.0, err.exception.return_value)

        result = ExClass().ex_method1(6)
        self.assertEqual(result, 12)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass().ex_method1(8.0)

        self.assertEqual(
            "The return type of 'ex_method1' must be <class 'int'>, "
            "but a value of 16.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(16.0, err.exception.return_value)

        result = ExClass().ex_method2(7)
        self.assertEqual(result, 14)
        with self.assertRaises(ReturnTypeError) as err:
            ExClass().ex_method2(9.0)

        self.assertEqual(
            "The return type of 'ex_method2' must be <class 'int'>, "
            "but a value of 18.0 <class 'float'> was returned.",
            str(err.exception)
        )
        self.assertEqual(18.0, err.exception.return_value)

    def test_enforce_type_hints_incorrect_self_annotations(self):
        # The results of this are inconsistent. See k2bd/typen#3
        class ExClass:
            @enforce_type_hints
            def __init__(self: int):
                pass

            @enforce_type_hints
            def method1(cls: int):
                pass

            @classmethod
            @enforce_type_hints
            def method2(cls: int):
                pass

            @enforce_type_hints
            @classmethod
            def method3(cls: int):
                pass

            @enforce_type_hints
            def method4(self: int):
                pass

            @classmethod
            @enforce_type_hints
            def method5(self: int):
                pass

            @enforce_type_hints
            @classmethod
            def method6(self: int):
                pass

        with self.assertRaises(ParameterTypeError) as err:
            ExClass.method2()
        self.assertIn("must be <class 'int'>", str(err.exception))

        ExClass.method3()

        with self.assertRaises(ParameterTypeError) as err:
            ExClass.method5()
        self.assertIn("must be <class 'int'>", str(err.exception))

        ExClass.method6()

        inst = ExClass()
        inst.method1()

        self.assertIn("must be <class 'int'>", str(err.exception))
        with self.assertRaises(ParameterTypeError) as err:
            inst.method2()
        self.assertIn("must be <class 'int'>", str(err.exception))

        inst.method3()

        inst.method4()

        with self.assertRaises(ParameterTypeError) as err:
            inst.method5()
        self.assertIn("must be <class 'int'>", str(err.exception))

        inst.method6()


#TODO: test strict decorators on methods
#TODO: test passing self as kwarg
#TODO: test strict self not named self
#TODO: test packed args, kwargs with self
#TODO: test packed arg and kwarg numpy arrays
#TODO: test method with self as an arg or kwarg name
