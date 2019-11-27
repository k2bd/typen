from traits.api import List, Tuple
import unittest

from typen._enforcer import Enforcer
from typen.exceptions import ParameterTypeError


class TypingToTrait(unittest.TestCase):
    pass


class EnforceTypingTypes(unittest.TestCase):
    def test_enforce_typing_list(self):
        def test_function(a: List):
            pass
        e = Enforcer(test_function)

        e.verify_args([[1, 2]], {})
        e.verify_args([[1.1, 0.1]], {})
        e.verify_args([["a", "b"]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([1], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1, 2)], {})

    def test_enforce_typing_list_spec(self):
        def test_function(a: List(int)):
            pass
        e = Enforcer(test_function)

        e.verify_args([[1, 2]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([[1.1, 0.1]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([["a", "b"]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([1], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1, 2)], {})

    def test_enforce_typing_tuple(self):
        def test_function(a: Tuple):
            pass
        e = Enforcer(test_function)

        e.verify_args([(1, 2)], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([[1.1, 0.1]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([["a", "b"]], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([1], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1, 2)], {})

    def test_enforce_typing_tuple_spec(self):
        def test_function(a: Tuple(int, int)):
            pass
        e = Enforcer(test_function)

        e.verify_args([(1, 2)], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1.1, 0.1)], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1, "b")], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([("a", "b")], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args((1,), {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([(1, 2, 3)], {})
        with self.assertRaises(ParameterTypeError):
            e.verify_args([[1, 2]], {})
