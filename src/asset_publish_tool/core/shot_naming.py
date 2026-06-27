"""
Shot naming utilities.

This module provides consistent naming conventions for shot-based
publishing workflows.
"""


def format_shot_name(shot_number):
    """
    Convert a shot number into the standard shot name format.

    Examples:
        1 -> shot001
        10 -> shot010
        120 -> shot120

    Args:
        shot_number (int | str): Shot number.

    Returns:
        str: Formatted shot name.

    Raises:
        ValueError: If the shot number is invalid.
    """
    try:
        number = int(shot_number)
    except ValueError:
        raise ValueError("Shot number must be numeric.")

    if number < 0:
        raise ValueError("Shot number must be positive.")

    return f"shot{number:03d}"
