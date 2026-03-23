from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InferenceConfig:
    bundle_dir: Path
    backend: str = "auto"
    device: str | None = None
    score_threshold: float | None = None
    topk: int | None = None

    def resolved_bundle_dir(self) -> Path:
        return self.bundle_dir.expanduser().resolve()


@dataclass(frozen=True)
class TestConfig:
    frame_count: int = 200
    output_dir: Path = Path("output")
    camera_id: str | None = None
    grab_timeout_ms: int = 1000
    expected_fps_threshold: float = 30.0
    inference: InferenceConfig | None = None

    def resolved_output_dir(self) -> Path:
        return self.output_dir.resolve()
