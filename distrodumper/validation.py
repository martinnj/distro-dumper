""" Library of validation helpers. """

# System imports.
from typing import Any
from typing import Collection


def is_atomic_csv(val: Any, atoms: Collection[str]) -> bool:
    """
    Checks if a value is a string containing a comma separated list fo valid string-atoms.
    Must contain at least one element.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if the value is a string containing a comma separated list of valid string-atoms,
            with at least one element.
    """
    if not isinstance(val, str):
        return False

    values = [value.strip() for value in val.split(",")]
    return len(values) > 0 and all(value in atoms for value in values)


def is_bool_string(val: Any) -> bool:
    """
    Checks if a given value is a string containing either the word `true` or `false`.
    Case-insensitive.

    ### Arguments
    - val : Any
      An object to check.

    ### Returns:
    - bool: True of the value is a string containing either `true` or `false`.
    """
    return isinstance(val, str) and val.lower() in {"true", "false"}


def is_non_empty_string(val: Any) -> bool:
    """
    Checks if a value is a non-empty string

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if `val` was a string with at least one character, False otherwise.
    """
    return isinstance(val, str) and len(val) > 0


def is_non_zero_int(val: Any) -> bool:
    """
    Checks if a value is an integer > 0 or a string containing an integer > 0.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if `val` was an integer > 0 or a string containing an integer > 0, False otherwise.
    """
    return not isinstance(val, bool) \
        and (
                (isinstance(val, int) and val > 0) \
                or (isinstance(val, str) and val.isdigit() and int(val) > 0)
        )
