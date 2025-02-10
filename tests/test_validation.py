from indra_curation.validation import validate_comment


def test_validate_signor_bad_syntax():
    text = "abcd"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0
    assert "Invalid syntax" in error_msg


def test_validate_signor_bad_keys1a():
    text = "key:value"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0
    assert "Invalid key(s)" in error_msg


def test_validate_signor_bad_keys1b():
    text = "key:value;"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0
    assert "Invalid key(s)" in error_msg


def test_validate_signor_bad_keys2():
    text = "keya:value1;keyb:value2;keyc:value3"
    valid_pattern, error_msg = validate_comment(text)
    assert not valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0
    assert "Invalid key(s)" in error_msg


def test_validate_signor_valid():
    text = "CELL:ABCD1234;EFFECT:increases;MECHANISM:phosphorylation"
    valid_pattern, error_msg = validate_comment(text)
    assert valid_pattern
    assert isinstance(error_msg, str)
    assert len(error_msg) == 0
