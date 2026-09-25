from pathlib import Path

from aurion_remote.c4d_diagnostics import EXPECTED_PLUGIN, solutions_for


def test_expected_binary_matches_cinema_4d_2023():
    assert EXPECTED_PLUGIN == "c4dOctane-R2023.xdl64"


def test_wrong_plugin_version_produces_path_aware_solution():
    plugins = [{
        "name": "c4dOctane-R23.xdl64",
        "path": r"C:\\Program Files\\Maxon Cinema 4D 2023\\plugins\\c4doctane\\c4dOctane-R23.xdl64",
        "expected_for_c4d_2023": False,
        "size": 1,
        "modified_at": "test",
    }]
    solutions = solutions_for(plugins, [], True)
    assert any("outras versões" in item for item in solutions)
    assert any(EXPECTED_PLUGIN in item for item in solutions)


def test_resource_error_recommends_consistent_build():
    solutions = solutions_for([], ["ERROR: res:1729548976"], True)
    assert any("res ou Lib300" in item for item in solutions)
