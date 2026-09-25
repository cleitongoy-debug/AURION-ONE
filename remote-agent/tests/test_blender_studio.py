from pathlib import Path

from aurion_remote import blender_studio


def test_workspace_categories_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(blender_studio, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(blender_studio, "ACTION_LOG", tmp_path / "actions.jsonl")
    paths = blender_studio.ensure_workspace()
    assert set(paths) == {"projects", "renders", "nodes", "textures", "rigs", "clothes", "logs"}
    assert all(path.is_dir() for path in paths.values())


def test_inventory_filters_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(blender_studio, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(blender_studio, "ACTION_LOG", tmp_path / "actions.jsonl")
    paths = blender_studio.ensure_workspace()
    (paths["textures"] / "material.png").write_bytes(b"png")
    (paths["textures"] / "ignore.exe").write_bytes(b"no")
    (paths["rigs"] / "character.fbx").write_bytes(b"fbx")
    inventory = blender_studio.asset_inventory()
    assert [item["name"] for item in inventory["textures"]] == ["material.png"]
    assert [item["name"] for item in inventory["rigs"]] == ["character.fbx"]


def test_default_blender_path_targets_52():
    assert Path(blender_studio.BLENDER_EXE).name.casefold() == "blender.exe"
    assert "Blender 5.2" in str(blender_studio.BLENDER_ROOT)
