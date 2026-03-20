from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestConfig:
    frame_count: int = 200
    output_dir: Path = Path("output")
    camera_id: str | None = None
    grab_timeout_ms: int = 1000
    expected_fps_threshold: float = 30.0

    def resolved_output_dir(self) -> Path:
        return self.output_dir.resolve()
