"""fatsecret-chart: JSON in, PNG out. The credential-free half of the design —
if this ever needs a FatSecret key, it belongs in the MCP server instead."""
import json
import subprocess
import sys

import pytest

matplotlib = pytest.importorskip("matplotlib")

from fatsecret_mcp.cli.chart import render

SERIES = [{"date": "2026-07-20", "value": 82.4},
          {"date": "2026-07-21", "value": 82.1},
          {"date": "2026-07-22", "value": 81.7}]


def test_render_writes_a_png(tmp_path):
    out = render(SERIES, str(tmp_path / "w.png"), "Weight", "kg")
    assert out.endswith("w.png")
    assert (tmp_path / "w.png").stat().st_size > 1000


def test_render_rejects_an_empty_series(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        render([], str(tmp_path / "w.png"), "Weight", "kg")


def test_render_rejects_a_malformed_point(tmp_path):
    with pytest.raises(ValueError, match="date"):
        render([{"day": "2026-07-20", "value": 1}], str(tmp_path / "w.png"), "", "")


def test_the_cli_reads_stdin_and_prints_the_path(tmp_path):
    """Verbatim invocation shape the nutrition-analysis skill uses."""
    dest = tmp_path / "chart.png"
    proc = subprocess.run(
        [sys.executable, "-m", "fatsecret_mcp.cli.chart", "--out", str(dest),
         "--title", "Weight", "--ylabel", "kg"],
        input=json.dumps(SERIES), text=True, capture_output=True, check=True)
    assert proc.stdout.strip() == str(dest)
    assert dest.exists()


def test_the_module_never_imports_the_api_or_config_layer():
    """A credential-free script is only credential-free while nobody imports the
    thing that reads credentials."""
    body = (__import__("pathlib").Path(__file__).resolve().parents[1]
            / "src" / "fatsecret_mcp" / "cli" / "chart.py").read_text(encoding="utf-8")
    for banned in ("from ..api", "from ..config", "from ..auth", "os.environ"):
        assert banned not in body
