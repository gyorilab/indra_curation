import re
from typing import Tuple


__all__ = ['validate_comment']

# Needs to match 'KEY1:VALUE1;KEY2:VALUE2;...'. Trailing ';' is optional.
# Let keys be case-sensitive alphabet strings and values be any alphanumeric, dash,
# space, or underscore characters.
comment_pattern = re.compile(r'([a-zA-Z ]+):("(?:""|[^"])*"|[^;]*)')
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
    space_in_keys = []
    has_match = False
    for sub_match in matches_iter:
        key = sub_match.group(1)
        value = sub_match.group(2)
        if key not in valid_keys:
            if key.strip() in valid_keys:
                space_in_keys.append(key.strip())
            else:
                invalid_keys.append(key)
        elif not value:
            # If the value is empty, this is also invalid
            empty_values.append(key)
        else:
            # We have at least one valid match
            has_match |= True
    if space_in_keys and not invalid_keys:
        # Handle the case where keys have spaces but are valid otherwise
        return (
            False,
            f"One or more key(s) contain spaces: {', '.join(space_in_keys)}. "
            f"Please use capital letters without spaces for keys."
        )
    if invalid_keys:
        bad_keys = invalid_keys + space_in_keys
        space_txt = ". Some keys may contain spaces" if space_in_keys else ""
        return False, \
            f"Invalid key(s): {', '.join(bad_keys)}{space_txt}. Must be one of {valid_str}."
    if empty_values:
        # Handle empty values
        return False, f"Empty value for key(s): {', '.join(empty_values)}. "
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
