import os
import subprocess
import sys
import sysconfig
import tempfile
from importlib.metadata import distribution
from pathlib import Path

import msite
from msite._vendor.mdown import to_html


dist = distribution("msite")
assert dist.version == msite.__version__ == "1.0.1"
assert dist.metadata["Requires-Python"] == ">=3.9"
assert not dist.requires
assert dist.read_text("top_level.txt").split() == ["msite"]
assert Path(msite.__file__).resolve() == Path(
    dist.locate_file("msite/__init__.py")).resolve()
assert any(
    ep.group == "console_scripts"
    and ep.name == "msite"
    and ep.value == "msite.cli:main"
    for ep in dist.entry_points
)
assert 'href="#"' in to_html('[x](javascript:alert(1))')
assert "javascript:" not in to_html('[x](javascript:alert(1))')
assert to_html('![a" onerror="alert(1)](image.png)') == (
    '<p><img src="image.png" alt="a&quot; onerror=&quot;alert(1)" /></p>')
assert to_html('![a`x" onerror="alert(1)`](image.png)') == (
    '<p><img src="image.png" alt="ax&quot; onerror=&quot;alert(1)" /></p>')

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "中文文档"
    (source / "sub").mkdir(parents=True)
    (source / "index.md").write_text(
        "# 首页\n\n回[指南](guide.md#进阶)。", encoding="utf-8")
    (source / "guide.md").write_text(
        '# 指南\n\n[危险](`javascript:alert(1)`)\n\n'
        '![a`x" onerror="alert(1)`](image.png)\n\n'
        '[进阶](sub/next.md)。', encoding="utf-8")
    (source / "sub" / "next.md").write_text("# 进阶\n\n返回指南。", encoding="utf-8")
    out_dir = root / "站点"
    out_dir.mkdir()
    (out_dir / "stale.html").write_text("old", encoding="utf-8")

    report = msite.build_site(
        source, out=str(out_dir), title='</title><script>alert("x")</script>',
        clean=True,
    )
    assert report["pages"] == 3
    assert not (out_dir / "stale.html").exists()
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    guide = (out_dir / "guide.html").read_text(encoding="utf-8")
    assert 'href="guide.html#进阶"' in index
    assert '<a href="#">危险</a>' in guide
    assert 'alt="ax&quot; onerror=&quot;alert(1)"' in guide
    assert "javascript:" not in guide
    assert "<script>" not in index
    assert "&lt;/title&gt;&lt;script&gt;" in index

    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-m", "msite", "--help"],
        cwd=tmp, capture_output=True, env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert "静态文档站" in result.stdout.decode("utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "msite", "--version"],
        cwd=tmp, capture_output=True, env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert "msite 1.0.1" in result.stdout.decode("utf-8")

    script = Path(sysconfig.get_path("scripts")) / (
        "msite.exe" if os.name == "nt" else "msite")
    assert script.is_file(), script
    result = subprocess.run(
        [str(script), str(source), "-o", str(root / "命令行站点"),
         "--title", "中文站点", "--json"],
        cwd=tmp, capture_output=True, env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert '"pages": 3' in result.stdout.decode("utf-8")
    assert (root / "命令行站点" / "index.html").is_file()

print("installed smoke: OK")
