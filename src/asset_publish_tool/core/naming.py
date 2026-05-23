import re


def clean_name(name, required_checks=None):
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
