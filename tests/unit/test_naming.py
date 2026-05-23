from asset_publish_tool.core.naming import clean_name


def test_clean_name_converts_camel_case_to_lowercase():
    cleaned = clean_name(
        "BigChair",
        ["lowercase_name"],
    )

    assert cleaned == "big_chair"


def test_clean_name_replaces_spaces_with_underscores():
    cleaned = clean_name(
        "Big Chair",
        ["no_spaces"],
    )

    assert cleaned == "Big_Chair"


def test_clean_name_removes_invalid_characters():
    cleaned = clean_name(
        "Big@Chair",
        ["valid_characters"],
    )

    assert cleaned == "Big_Chair"
