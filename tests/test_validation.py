from indra_curation.validation import validate_comment


def test_validate_signor_bad_syntax():
    text = "abcd"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid syntax" in error_msg


def test_validate_signor_bad_syntax2():
    text = ";:::;;;:CELL"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "No valid key-value pairs found." in error_msg, error_msg


def test_validate_signor_bad_syntax3():
    text = "CELL:fnejf;ccece:fffssffg fnmfnfefnkdfvmn n vnvrn;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid key(s): ccece" in error_msg, error_msg


def test_validate_signor_bad_syntax_spce_in_key():
    text = "CELL   :fnejf;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "One or more key(s) contain spaces: CELL" in error_msg, error_msg


def test_validate_signor_bad_syntax_spce_in_key2():
    text = "   CELL:fnejf;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "One or more key(s) contain spaces: CELL" in error_msg, error_msg


def test_validate_signor_bad_keys1a():
    text = "key:value"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid key(s): key" in error_msg, error_msg


def test_validate_signor_bad_keys1b():
    text = "key:value;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid key(s): key" in error_msg, error_msg


def test_validate_signor_bad_keys2():
    text = "keya:value1;keyb:value2;keyc:value3"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid key(s): keya, keyb, keyc" in error_msg, error_msg


def test_validate_signor_bad_keys3():
    text = "KEYA:value1;KEYB:value2;KEYC:value3"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Invalid key(s): KEYA, KEYB, KEYC" in error_msg, error_msg


def test_validate_signor_empty_value():
    text = "CELL:;EFFECT:increases;MECHANISM:phosphorylation"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Empty value for key(s): CELL" in error_msg, error_msg


def test_validate_signor_empty_value2():
    text = "CELL:"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Empty value for key(s): CELL" in error_msg, error_msg


def test_validate_signor_empty_value3():
    text = "CELL:;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Empty value for key(s): CELL" in error_msg, error_msg


def test_validate_signor_empty_value4():
    text = "CELL:;EFFECT:"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) > 0, "Expected an error message to be returned"
    assert "Empty value for key(s): CELL, EFFECT" in error_msg, error_msg


def test_validate_signor_valid():
    text = "CELL:ABCD1234;EFFECT:increases;MECHANISM:phosphorylation"
    valid_pattern, error_msg = validate_comment(text)
    assert valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) == 0, error_msg


def test_validate_signor_valid2():
    text = (
        "EFFECT:down-regulates quantity by destabilizing;EFFECT:down-regulates quantity;"
    )
    valid_pattern, error_msg = validate_comment(text)
    assert valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) == 0, error_msg


def test_validate_signor_valid_with_quotes():
    text = 'CELL:"text;more text";EFFECT:increases;MECHANISM:phosphorylation'
    valid_pattern, error_msg = validate_comment(text)
    assert valid_pattern
    assert isinstance(error_msg, str), error_msg.__class__
    assert len(error_msg) == 0, error_msg
