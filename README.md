# Strong Type Hints with Traits

This package supplies simple decorators to enforce type hints on function parameters and return types.

```python
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
from traits.api import Either, Enum, Instance, Int, Str, Tuple


@enforce_type_hints
def complicated_function(
        a: Either(Str, Int),  # Either a string or an int
        b: Enum(2, 5, "foo"),  # One of a specific set of values
        c: Instance(MyClass),  # Class instances
        ) -> Tuple(Str, Either(Str, Int)):  # Complicated return specification
    ...
```

## Default Values

Valid default values are enforced as well.

```python
@enforce_type_hints
def add_numbers(
        a: float = 1,  # Can be coerced to float
        b: float = "two"  # ParameterTypeError
        ) -> float:
    return a + b
```

## Strict Enforcement

Type hints can also be required with the `@strict_type_hints` decorator. Both of the following examples will raise an exception. Without strict enforcement, parameters and return values without type hints can have any value.

```python
@strict_type_hints
def add_numbers(a, b: float) -> float:  # UnspecifiedParameterTypeError
    return a + b
```

```python
@strict_type_hints
def add_numbers(a: float, b: float):  # UnspecifiedReturnTypeError
    return a + b
```

## Coercion

Values are enforced to types based on coercibility - they are not actually explicitly coerced.

```python
@enforce_type_hints
def add_numbers(a: float, b: float) -> float:
    return a + b

type(add_numbers(1, 2))  # int
```

## Recovering from `ReturnTypeError`s

Because the function has to be executed to enforce the return value, the invalid value is stored on the exception. This makes it possible to recover from `ReturnTypeError`s programatically.

```python
@enforce_type_hints
def give_int(a) -> int:
    return a

try:
    give_int("a")
except ReturnTypeError as err:
    print(err.return_value)  # a
```
