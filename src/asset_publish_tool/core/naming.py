"""
Name cleaning utilities for Maya scene objects.

This module standardises object names according to the configured
validation rules used by the publishing pipeline.
"""

import re


def clean_name(name, required_checks=None):
    """
    Clean and standardise a Maya object name.

    The cleaning process can enforce:
    - lowercase naming
    - space removal
    - valid character filtering

    Maya hierarchy paths and namespaces are removed before processing.

    Args:
        name (str): Original Maya object name.
        required_checks (list | None): Validation checks controlling
            which cleaning operations are applied.

    Returns:
        str: Cleaned object name.
    """
    required_checks = required_checks or []

    short_name = name.split("|")[-1]
    short_name = short_name.split(":")[-1]

    clean = short_name

    if "lowercase_name" in required_checks:
        clean = re.sub(r"(?<!^)(?=[A-Z])", "_", clean)
        clean = clean.lower()

    if "no_spaces" in required_checks:
        clean = clean.replace(" ", "_")

    if "valid_characters" in required_checks:
        clean = re.sub(r"[^A-Za-z0-9_]+", "_", clean)

    clean = re.sub(r"_+", "_", clean)
    clean = clean.strip("_")

    return clean
