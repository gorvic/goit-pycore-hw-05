import re
from collections.abc import Callable, Generator
from typing import Final


# Flexible number pattern for extracting income values from free-form text.
#
# Supported formats:
# - 100
# - -100
# - +100
# - 100.50
# - 100,50
# - 1 000
# - 1_000 (Pythonic style)
# - 1 000.50
#
# The pattern avoids partial matches inside identifiers or malformed numbers.
NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\d._])"
    r"(?P<number>[+-]?(?:\d{1,3}(?:[ _]\d{3})+|\d+)(?:[.,]\d+)?)"
    r"(?![\d._])"
)


def generator_numbers(text: str) -> Generator[float, None, None]:
    """
    Yield all real numbers found in text.

    The parser supports optional sign, decimal separators,
    and grouped thousands separated by spaces or underscores.

    Args:
        text: Source text containing numeric values.

    Yields:
        Parsed floating-point numbers.
    """
    for match in NUMBER_PATTERN.finditer(text):
        # Normalize decimal separator and remove thousands separators.
        raw_number = (
            match.group("number")
            .replace(",", ".")
            .replace(" ", "")
            .replace("_", "")
        )

        yield float(raw_number)


def sum_profit(
    text: str,
    generator: Callable[[str], Generator[float, None, None]],
) -> float:
    """
    Calculate total profit from all numbers extracted from text.

    Args:
        text: Source text containing income values.
        generator: Number extraction generator function.

    Returns:
        Sum of all extracted numeric values.
    """

    return sum(generator(text))


text = ("Загальний дохід працівника складається з декількох частин: 1 000.01 як основний дохід, "
        "доповнений додатковими надходженнями 27.45 і 324.00 доларів.")
total_income = sum_profit(text, generator_numbers)
print(f"Загальний дохід: {total_income}")
