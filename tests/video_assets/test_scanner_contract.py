from src.video_assets.registry import Registry
from src.video_assets.scanner import Scanner


def test_scanner_dry_run_detects_video_without_importing(tmp_path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    (videos_dir / "clip.mp4").write_bytes(b"video")
    registry = Registry(str(tmp_path / "video_assets.jsonl"))
    scanner = Scanner(registry)

    result = scanner.scan(roots=[str(videos_dir)], dry_run=True)

    assert result["found"] == 1
    assert result["imported"] == 0
    assert registry.count() == 0
