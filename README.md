# Strong Type Hints with Traits

[![Build Status](https://travis-ci.org/k2bd/typen.svg?branch=master)](https://travis-ci.org/k2bd/typen)

This package supplies simple decorators to enforce Python type hints on function parameters and return types.

```python
from typen import enforce_type_hints


@enforce_type_hints
def halve_integer(a: int) -> float:
    return a / 2

halve_integer(5)  # 2.5

halve_integer(5.0)  # ParameterTypeError
```

```python
@enforce_type_hints
def give_int(a) -> int:
    return a

give_int(1)  # 1

give_int("a")  # ReturnTypeError
```

## Trait Type Hints

[Trait](https://github.com/enthought/traits) types can also be used to define complex patterns in type hints

```python
from traits.api import Array, Either, Enum, Instance, Int, Str, Tuple


@enforce_type_hints
def complicated_function(
        a: Either(Str, Int),  # Either a string or an int
        b: Enum(2, 5, "foo"),  # One of a specific set of values
        c: Instance(MyClass),  # Class instances
        d: Array(size=(None, 2)),  # Numpy array validation
        ) -> Tuple(Str, Either(Str, Int)):  # Complicated return specification
    ...
```

## Strict Enforcement

Type hints can also be required with the `@strict_type_hints` decorator. Both of the following examples will raise an exception when the function is first called. Without strict enforcement, parameters and return values without type hints can have any value.

```python
from typen import strict_type_hints


@strict_type_hints
def add_numbers(a, b: float) -> float:
    return a + b

add_numbers(1, 2)  # UnspecifiedParameterTypeError
```

```python
@strict_type_hints
def add_numbers(a: float, b: float):
    return a + b

add_numbers(1, 2)  # UnspecifiedReturnTypeError
```

## Packed args and kwargs

Type hints on packed parameters apply to all values passed through that packing.

```python
@enforce_type_hints
def foos_vs_bars(*foos: int, **bars: str) -> bool:
    return sum(foos) >= len(bars)


foos_vs_bars(1, 2, 3, a="a", b="b", c="c")  # True

foos_vs_bars(2, 3, 5, d=4)  # ParameterTypeError

foos_vs_bars(2, "three", 5, e="e")  # ParameterTypeError
```

## Method Decoration

Methods can be decorated as well. `self`-references are exempt from strict type hint requirements, as is the return type of `__init__`.

```python
class ExClass:
    @strict_type_hints
    def __init__(self, a: int, b: int):
        ...

    @classmethod
    @strict_type_hints
    def a_class_method(cls, a: int, c: int) -> int:
        ...

    @staticmethod
    @strict_type_hints
    def a_static_method(a: int, c: int) -> int:
        ...

```

## Coercion

Values are enforced to types based on [Trait type coercion](https://docs.enthought.com/traits/traits_user_manual/defining.html#trait-type-coercion). Casting behaviour is not added to the function:

```python
@enforce_type_hints
def add_numbers(a: float, b: float) -> float:
    return a + b

type(add_numbers(1, 2))  # int
```

## Recovering from `ReturnTypeError`

Because the function has to be executed to enforce the return value, the invalid value is stored on the exception. This makes it possible to recover from a `ReturnTypeError` programatically.

```python
from typen.exceptions import ReturnTypeError


@enforce_type_hints
def give_int(a) -> int:
    return a

try:
    give_int("a")
except ReturnTypeError as err:
    print(err.return_value)  # a
```