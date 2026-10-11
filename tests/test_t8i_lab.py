# -*- coding: utf-8 -*-
from pathlib import Path
import tempfile

import aurion_t8i_lab as t8i


def test_workspace_persistence():
    with tempfile.TemporaryDirectory() as td:
        ws = t8i.create_workspace(td, "Teste T8I")
        root = Path(ws["workspace"])
        assert (root / ".aurion_t8i" / "manifest.json").is_file()
        t8i.save_settings(str(root), {"exposure_ev": 1.0, "wb_mode": "camera"})
        t8i.save_conversation(str(root), "user", "nota de teste", kind="note")
        t8i.snapshot_workspace(str(root), "teste")
        loaded = t8i.load_workspace(str(root))
        assert loaded["settings"]["exposure_ev"] == 1.0
        assert loaded["conversations"][-1]["text"] == "nota de teste"
        assert list((root / "snapshots").glob("snapshot_*.json"))
