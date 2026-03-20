from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class CameraTestResult:
    success: bool
    camera_model: str | None
    camera_id: str | None
    camera_ip: str | None
    pixel_format: str | None
    image_width: int | None
    image_height: int | None
    frames_requested: int
    frames_captured: int
    elapsed_seconds: float
    fps: float
    first_frame_path: Path | None
    last_frame_path: Path | None
    error: str | None = None

    def to_summary(self) -> str:
        lines = [
            f"RESULT {'PASS' if self.success else 'FAIL'}",
            f"MODEL {self.camera_model or 'unknown'}",
            f"CAMERA_ID {self.camera_id or 'unknown'}",
            f"CAMERA_IP {self.camera_ip or 'unknown'}",
            f"PIXEL_FORMAT {self.pixel_format or 'unknown'}",
            f"IMAGE_SIZE {self.image_width or 'unknown'}x{self.image_height or 'unknown'}",
            f"FRAMES {self.frames_captured}/{self.frames_requested}",
            f"ELAPSED_SECONDS {self.elapsed_seconds:.3f}",
            f"FPS {self.fps:.3f}",
            f"FIRST_FRAME {self.first_frame_path if self.first_frame_path else 'not_saved'}",
            f"LAST_FRAME {self.last_frame_path if self.last_frame_path else 'not_saved'}",
        ]
        if self.error:
            lines.append(f"ERROR {self.error}")
        return "\n".join(lines)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["first_frame_path"] = str(self.first_frame_path) if self.first_frame_path else None
        payload["last_frame_path"] = str(self.last_frame_path) if self.last_frame_path else None
        return json.dumps(payload, indent=2)


@dataclass(frozen=True)
class LivePreviewResult:
    success: bool
    camera_model: str | None
    camera_id: str | None
    camera_ip: str | None
    pixel_format: str | None
    image_width: int | None
    image_height: int | None
    frames_displayed: int
    elapsed_seconds: float
    fps: float
    error: str | None = None

    def to_summary(self) -> str:
        lines = [
            f"RESULT {'PASS' if self.success else 'FAIL'}",
            f"MODEL {self.camera_model or 'unknown'}",
            f"CAMERA_ID {self.camera_id or 'unknown'}",
            f"CAMERA_IP {self.camera_ip or 'unknown'}",
            f"PIXEL_FORMAT {self.pixel_format or 'unknown'}",
            f"IMAGE_SIZE {self.image_width or 'unknown'}x{self.image_height or 'unknown'}",
            f"FRAMES_DISPLAYED {self.frames_displayed}",
            f"ELAPSED_SECONDS {self.elapsed_seconds:.3f}",
            f"FPS {self.fps:.3f}",
        ]
        if self.error:
            lines.append(f"ERROR {self.error}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
