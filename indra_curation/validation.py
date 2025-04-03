import re
from typing import Tuple


__all__ = ['validate_comment']

# Needs to match 'KEY1:VALUE1;KEY2:VALUE2;...'. Trailing ';' is optional.
# Let keys be case-sensitive alphabet strings and values be any alphanumeric, dash,
# space, or underscore characters.
comment_pattern = re.compile(r'([A-Z]+):("(?:""|[^"])*"|[^;]*)')
valid_keys = {
    'CELL', 'TAXID', 'DIRECT', 'EFFECT', 'SENTENCE', 'MECHANISM', 'RESIDUE'
}


def validate_comment(text: str) -> Tuple[bool, str]:
    """Validate comment string of a curation for a signor evidence

    Parameters
    ----------
    text :
        The comment string to validate

    Returns
    -------
    :
        A tuple of two values. The first value is a boolean indicating if the comment
        string is valid. The second value is a string with an error message if the
        comment string is invalid, or an empty string if the comment string is valid.
    """
    valid_str = f"'{', '.join(valid_keys)}'"
    # Check if the comment has a valid syntax
    matches_iter = comment_pattern.finditer(text)

    # Pattern is invalid
    if matches_iter is None or ":" not in text:
        return (
            False,
            "Invalid syntax. Should be 'KEY1:VALUE1;KEY2:VALUE2;...', where each key "
            f"is one of {valid_str}, in capital letters. If a value string contains "
            f"semi-colons, ';', please enclose it in quotes (e.g. 'CELL:\"text;more "
            f"text\";MECHANISM:phosphorylation'). "
        )

    # Now test if the keys are valid
    invalid_keys = []
    empty_values = []
    has_match = False
    for sub_match in matches_iter:
        key = sub_match.group(1)
        value = sub_match.group(2)
        if key.upper() not in valid_keys:
            invalid_keys.append(key)
        elif not value:
            # If the value is empty, this is also invalid
            empty_values.append(key)
        else:
            # We have at least one valid match
            has_match |= True
    if invalid_keys:
        return False, (f"Invalid key(s): '{', '.join(invalid_keys)}'. Must be one of "
                       f"{valid_str}.")
    if empty_values:
        # Handle empty values
        return False, f"Empty value for key(s): '{', '.join(empty_values)}'. "
    if not has_match:
        # If no valid matches were found, return invalid
        return (
            False,
            "No valid key-value pairs found. At least one key-value pair must be "
            f"provided of the format 'KEY1:VALUE1;KEY2:VALUE2;...', where each key "
            f"is one of {valid_str}, in capital letters. If a value string contains "
            f"semi-colons, ';', please enclose it in quotes (e.g. 'CELL:\"text;more text\"'). "
        )
    return True, ""
