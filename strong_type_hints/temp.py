from strong_type_hints.decorators import enforce_type_hints, strict_type_hints
from strong_type_hints.exceptions import ReturnTypeError


@enforce_type_hints
def halve_integer(a: int) -> float:
    return a / 2


print(halve_integer(5))


from traits.api import Either, Enum, Int, Str, Tuple


@enforce_type_hints
def complicated_function(
        a: Either(Str, Int),  # Either a string or an int
        b: Enum(2, 5, "foo"),  # One of a specific set of values
        ) -> Tuple(Str, Either(Str, Int)):
    pass


@enforce_type_hints
def give_int(a) -> int:
    return a

try:
    give_int("a")
except ReturnTypeError as err:
    print(err.return_value)


from traits.api import Float  # Anything castable to a float


@enforce_type_hints
def add_numbers(a: float, b: float) -> float:
    return a + b

print(type(add_numbers(1, 2)))

@strict_type_hints
def add_numbers(a, b: float) -> float:
    return a + b

@strict_type_hints
def add_numbers(a: float, b: float):
    return a + b

