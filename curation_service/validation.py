import re
from typing import Tuple


__all__ = ['validation_funcs']


signor_pattern = re.compile(r'^([a-zA-Z]+:[a-zA-Z0-9]+;)*([a-zA-Z]+:[a-zA-Z0-9]+)?$')


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
    valid_keys = {
        'CELL', 'TAXID', 'DIRECT', 'EFFECT', 'SENTENCE', 'MECHANISM', 'RESIDUE'
    }
    valid_str = f"'{', '.join(valid_keys)}'"
    # Check if the comment has a valid syntax
    m = signor_pattern.match(text)

    # Pattern is invalid
    if not m:
        return (
            False,
            "Invalid syntax. Should be 'KEY1:VALUE1;KEY2:VALUE2;...', where each key "
            f"is one of {valid_str}."
        )

    # Now test if the keys are valid
    invalid_keys = []
    for key_value in text.split(';'):
        if not key_value:
            # Skip empty strings e.g. from trailing ';'
            continue
        key, value = key_value.split(':', maxsplit=1)
        if key.upper() not in valid_keys:
            invalid_keys.append(key)
    if invalid_keys:
        return False, (f"Invalid key(s): '{', '.join(invalid_keys)}'. Must be one of "
                       f"{valid_str}.")
    return True, ""


validation_funcs = {
    "signor": validate_signor_comments
}
