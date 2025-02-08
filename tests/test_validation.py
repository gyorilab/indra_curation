from curation_service.validation import validate_comment


def test_validate_signor_bad_syntax():
    text = "abcd"
    invalid_pattern, bad_keys = validate_comment(text)
    assert invalid_pattern
    assert isinstance(bad_keys, list)
    assert len(bad_keys) == 0


def test_validate_signor_bad_keys1a():
    text = "key:value"
    invalid_pattern, bad_keys = validate_comment(text)
    assert isinstance(bad_keys, list)
    assert len(bad_keys) == 1
    assert bad_keys[0] == "key"


def test_validate_signor_bad_keys1b():
    text = "key:value;"
    invalid_pattern, bad_keys = validate_comment(text)
    assert not invalid_pattern
    assert isinstance(bad_keys, list)
    assert len(bad_keys) == 1
    assert bad_keys[0] == "key"


def test_validate_signor_bad_keys2():
    text = "keya:value1;keyb:value2;keyc:value3"
    invalid_pattern, bad_keys = validate_comment(text)
    assert not invalid_pattern
    assert isinstance(bad_keys, list)
    assert len(bad_keys) == 3
    assert bad_keys[0] == "keya"


def test_validate_signor_valid():
    text = "CELL:ABCD1234;EFFECT:increases;MECHANISM:phosphorylation"
    invalid_pattern, bad_keys = validate_comment(text)
    assert not invalid_pattern
    assert isinstance(bad_keys, list)
    assert len(bad_keys) == 0
