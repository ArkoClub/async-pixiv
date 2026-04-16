import re
from pathlib import Path


def test_readme_awaits_link_download_example():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(
        encoding="utf-8"
    )

    assert re.search(
        r"file_data\s*=\s*await\s+client\.download\(illust\.link\)", readme
    )
    assert not re.search(r"file_data\s*=\s*await\s+illust\.link\.download\(\)", readme)
    assert not re.search(r"file_data\s*=\s*illust\.link\.download\(\)", readme)
