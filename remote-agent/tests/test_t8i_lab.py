from pathlib import Path

from aurion_remote import t8i_lab


def test_workspace_structure_is_created_without_touching_other_files(tmp_path, monkeypatch):
    data_dir = tmp_path / "agent-data"
    config_file = data_dir / "t8i_workspace.json"
    monkeypatch.setattr(t8i_lab, "DATA_DIR", data_dir)
    monkeypatch.setattr(t8i_lab, "CONFIG_FILE", config_file)

    root = tmp_path / "meu-projeto-t8i"
    marker = root / "nao_apagar.txt"
    root.mkdir()
    marker.write_text("preservar", encoding="utf-8")

    saved = t8i_lab._save_workspace(root)

    assert saved["workspace"] == str(root)
    assert marker.read_text(encoding="utf-8") == "preservar"
    for folder in t8i_lab.FOLDERS:
        assert (root / folder).is_dir()


def test_unique_copy_never_overwrites_existing_raw(tmp_path):
    src_dir = tmp_path / "cartao"
    dst_dir = tmp_path / "RAW"
    src_dir.mkdir()
    dst_dir.mkdir()

    src = src_dir / "IMG_0001.CR3"
    src.write_bytes(b"original-novo")
    existing = dst_dir / "IMG_0001.CR3"
    existing.write_bytes(b"original-antigo")

    copied = t8i_lab._unique_copy(src, dst_dir)

    assert copied.name == "IMG_0001_001.CR3"
    assert existing.read_bytes() == b"original-antigo"
    assert copied.read_bytes() == b"original-novo"


def test_slug_is_safe_for_export_names():
    assert t8i_lab._slug(" Ensaio / T8i : 01 ") == "Ensaio-T8i-01"
    assert t8i_lab._slug("***") == "sessao"
