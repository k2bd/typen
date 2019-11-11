import unittest

from typen._decorators import (
    enforce_type_hints,
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
            new_func(b=1.0, a=2)

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
        def example_function(*foos, **bars):
            return sum(foos) >= len(bars)
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(1, 2, 3, a="a", b="b", c="c"), True)

    def test_enforce_type_hints_packed_args_kwargs_hint(self):
        def example_function(*foos: int, **bars: str) -> bool:
            return sum(foos) >= len(bars)
        new_func = enforce_type_hints(example_function)

        self.assertEqual(new_func(1, 2, 3, a="a", b="b", c="c"), True)

        with self.assertRaises(ParameterTypeError):
            new_func(2, 3, 5, d=4)

        with self.assertRaises(ParameterTypeError):
            new_func(2, "three", 5, e="e")

    def test_enforce_type_hints_packed_args_kwargs_method(self):
        class ExClass:
            @enforce_type_hints
            def example_method(self, *foos: int, **bars: str) -> bool:
                return sum(foos) >= len(bars)

        inst = ExClass()

        self.assertEqual(inst.example_method(1, 2, 3, a="a", b="b", c="c"), True)

        with self.assertRaises(ParameterTypeError):
            inst.example_method(2, 3, 5, d=4)

        with self.assertRaises(ParameterTypeError):
            inst.example_method(2, "three", 5, e="e")

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

    def test_enforce_type_hints_self_passed_as_kwarg(self):
        class ExClass:
            @enforce_type_hints
            def ex_method(self, a: int, b: float) -> float:
                return a + b
        inst = ExClass()

        self.assertEqual(ExClass.ex_method(a=1, b=2, self=inst), 3)

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
        # TODO: The results of this are inconsistent. See k2bd/typen#3
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


class TestStrictTypeHints(unittest.TestCase):
    def test_strict_type_hints(self):
        def example_function(a: int, b: float = 0.5) -> str:
            return "a"
        new_func = strict_type_hints(example_function)

        new_func(1, 2.5)  # No errors

    def test_strict_type_hints_missing_arg(self):
        def example_function(a, b: float = 0.5) -> str:
            pass
        new_func = strict_type_hints(example_function)

        with self.assertRaises(UnspecifiedParameterTypeError) as err:
            new_func(1, 2)

        self.assertEqual(
            "The following parameters of 'example_function' must be given "
            "type hints: ['a']",
            str(err.exception)
        )

    def test_strict_type_hints_missing_return(self):
        def example_function(a: int, b: float):
            pass
        new_func = strict_type_hints(example_function)

        with self.assertRaises(UnspecifiedReturnTypeError) as err:
            new_func(1, 2)

        self.assertEqual(
            "A return type hint must be specified for 'example_function'.",
            str(err.exception)
        )

    def test_strict_type_hints_packed_args(self):
        def example_function(a: str, *args: int) -> float:
            return sum(args)
        new_func = strict_type_hints(example_function)

        self.assertEqual(new_func("aa", 2, 3, 4, 5), 14)

    def test_strict_type_hints_packed_args_missing(self):
        def example_function(a: str, *args) -> float:
            return sum(args)
        new_func = strict_type_hints(example_function)

        with self.assertRaises(UnspecifiedParameterTypeError) as err:
            new_func("aa", 2, 3, 4, 5)

        self.assertEqual(
            "Packed positional argument 'args' must be given a type hint",
            str(err.exception)
        )

    def test_strict_type_hints_packed_kwargs(self):
        def example_function(a: str, **kwargs: int) -> float:
            return sum(kwargs.values())
        new_func = strict_type_hints(example_function)

        self.assertEqual(new_func("aa", b=2, c=3, d=4, e=5), 14)

    def test_strict_type_hints_packed_kwargs_missing(self):
        def example_function(a: str, **kwargs) -> float:
            return sum(kwargs.values())
        new_func = strict_type_hints(example_function)

        with self.assertRaises(UnspecifiedParameterTypeError) as err:
            new_func("aa", b=2, c=3, d=4, e=5)

        self.assertEqual(
            "Packed keyword argument 'kwargs' must be given a type hint",
            str(err.exception)
        )

    def test_strict_type_hints_on_method(self):
        class ExClass:
            # __init__ is exempt from return hint requirement
            @strict_type_hints
            def __init__(self, a: int, b: int):
                pass

            @strict_type_hints
            def ex_method(self, c: int, d: float) -> float:
                return c * d

        inst = ExClass(1, 2)
        inst.ex_method(1, 2)

    def test_strict_type_hints_on_method_self_not_named_self(self):
        class ExClass:
            @strict_type_hints
            def __init__(this, self: float):
                pass

            @strict_type_hints
            def ex_method(this, self: int) -> int:
                return 2*self

        inst = ExClass(1)
        inst.ex_method(2)

    def test_strict_type_hints_on_class_method(self):
        class ExClass:
            @strict_type_hints
            @classmethod
            def ex_method(cls, a: int, c: int) -> int:
                return a + c

        ExClass.ex_method(1, 2)

    def test_strict_type_hints_on_class_method_missing(self):
        with self.assertRaises(RuntimeError) as err:
            class ExClass1:
                @strict_type_hints
                @classmethod
                def ex_method(cls, a: int, c) -> int:
                    return a + c

        self.assertIsInstance(
            err.exception.__cause__,
            UnspecifiedParameterTypeError
        )

        with self.assertRaises(RuntimeError) as err:
            class ExClass2:
                @strict_type_hints
                @classmethod
                def ex_method(cls, a: int, c: int):
                    return a + c

        self.assertIsInstance(
            err.exception.__cause__,
            UnspecifiedReturnTypeError
        )

    def test_strict_type_hints_on_static_method(self):
        class ExClass:
            @staticmethod
            @strict_type_hints
            def ex_method1(a: int, c: int) -> int:
                return a + c

            @strict_type_hints
            @staticmethod
            def ex_method2(a: int, c: int) -> int:
                return a + c

        ExClass.ex_method1(1, 2)
        ExClass.ex_method2(1, 2)

        inst = ExClass()

        inst.ex_method1(1, 2)
        inst.ex_method2(1, 2)

    def test_strict_type_hints_on_static_method_missing(self):
        with self.assertRaises(RuntimeError) as err:
            class ExClass1:
                @strict_type_hints
                @staticmethod
                def ex_method(a, c: int) -> int:
                    return a + c

        self.assertIsInstance(
            err.exception.__cause__,
            UnspecifiedParameterTypeError
        )

        with self.assertRaises(RuntimeError) as err:
            class ExClass3:
                @strict_type_hints
                @staticmethod
                def ex_method(a: int, c: int):
                    return a + c

        self.assertIsInstance(
            err.exception.__cause__,
            UnspecifiedReturnTypeError
        )
