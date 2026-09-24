from aurion_remote.manual_vault import is_restricted, safe_original_name


def test_restricted_names_are_case_insensitive():
    assert is_restricted("YellowStar.exe")
    assert is_restricted("YELLOWSTAR.XDL64")
    assert is_restricted("license")
    assert is_restricted("otoy_credentials")


def test_regular_package_is_not_restricted():
    assert not is_restricted("c4dOctane-R2023.xdl64")
    assert not is_restricted("workflow.json")


def test_filename_is_reduced_to_leaf_and_sanitized():
    assert safe_original_name("../../pacote oficial.zip") == "pacote_oficial.zip"
