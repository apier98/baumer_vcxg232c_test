from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from time import perf_counter
from typing import Any

from .config import TestConfig
from .result_types import CameraTestResult


class CameraTestError(RuntimeError):
    """Raised when the headless camera test cannot complete."""


@dataclass(frozen=True)
class RuntimeDependencies:
    neoapi: Any
    cv2: Any
    numpy: Any


def load_runtime_dependencies() -> RuntimeDependencies:
    missing: list[str] = []

    try:
        neoapi = import_module("neoapi")
    except ModuleNotFoundError:
        neoapi = None
        missing.append("neoapi")

    try:
        cv2 = import_module("cv2")
    except ModuleNotFoundError:
        cv2 = None
        missing.append("opencv-python")

    try:
        numpy = import_module("numpy")
    except ModuleNotFoundError:
        numpy = None
        missing.append("numpy")

    if missing:
        raise CameraTestError(
            "Missing runtime dependencies: "
            + ", ".join(missing)
            + ". Install them with `pip install -r requirements.txt`."
        )

    return RuntimeDependencies(neoapi=neoapi, cv2=cv2, numpy=numpy)


def run_headless_test(config: TestConfig) -> CameraTestResult:
    if config.frame_count <= 0:
        raise CameraTestError("frame_count must be greater than zero.")
    if config.grab_timeout_ms <= 0:
        raise CameraTestError("grab_timeout_ms must be greater than zero.")
    if config.expected_fps_threshold <= 0:
        raise CameraTestError("expected_fps_threshold must be greater than zero.")

    dependencies = load_runtime_dependencies()
    output_dir = config.resolved_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    cam = dependencies.neoapi.Cam()

    try:
        _connect_camera(cam, config.camera_id)
        metadata = _read_camera_metadata(cam)
        first_frame, last_frame, frames_captured, elapsed_seconds = _capture_frames(
            cam=cam,
            frame_count=config.frame_count,
            grab_timeout_ms=config.grab_timeout_ms,
            numpy_module=dependencies.numpy,
        )
        first_frame_path, last_frame_path = _save_artifacts(
            first_frame=first_frame,
            last_frame=last_frame,
            output_dir=output_dir,
            cv2_module=dependencies.cv2,
        )
    except CameraTestError as exc:
        return CameraTestResult(
            success=False,
            camera_model=_read_optional_feature(cam, "DeviceModelName"),
            camera_id=_read_optional_feature(cam, "DeviceID", "DeviceSerialNumber", "DeviceUserID"),
            camera_ip=_read_optional_feature(cam, "GevCurrentIPAddress", "GevPersistentIPAddress"),
            pixel_format=_read_optional_feature(cam, "PixelFormat"),
            image_width=_coerce_int(_read_optional_feature(cam, "Width")),
            image_height=_coerce_int(_read_optional_feature(cam, "Height")),
            frames_requested=config.frame_count,
            frames_captured=0,
            elapsed_seconds=0.0,
            fps=0.0,
            first_frame_path=None,
            last_frame_path=None,
            error=str(exc),
        )
    finally:
        _disconnect_camera(cam)

    fps = frames_captured / elapsed_seconds if elapsed_seconds > 0 else 0.0
    error: str | None = None
    success = True

    if frames_captured != config.frame_count:
        success = False
        error = (
            f"Expected {config.frame_count} frames but captured {frames_captured}."
        )
    elif fps < config.expected_fps_threshold:
        success = False
        error = (
            f"Measured FPS {fps:.3f} is below the threshold "
            f"{config.expected_fps_threshold:.3f}."
        )

    return CameraTestResult(
        success=success,
        camera_model=metadata.model,
        camera_id=metadata.device_id,
        camera_ip=metadata.ip_address,
        pixel_format=metadata.pixel_format,
        image_width=metadata.width,
        image_height=metadata.height,
        frames_requested=config.frame_count,
        frames_captured=frames_captured,
        elapsed_seconds=elapsed_seconds,
        fps=fps,
        first_frame_path=first_frame_path,
        last_frame_path=last_frame_path,
        error=error,
    )


def describe_runtime() -> dict[str, str]:
    dependencies = load_runtime_dependencies()
    versions = {
        "neoapi": _read_module_version(dependencies.neoapi),
        "opencv-python": _read_module_version(dependencies.cv2),
        "numpy": _read_module_version(dependencies.numpy),
    }
    return versions


@dataclass(frozen=True)
class CameraMetadata:
    model: str | None
    device_id: str | None
    ip_address: str | None
    pixel_format: str | None
    width: int | None
    height: int | None


def _connect_camera(cam: Any, camera_id: str | None) -> None:
    try:
        if camera_id:
            cam.Connect(camera_id)
        else:
            cam.Connect()
    except Exception as exc:  # neoapi exposes SDK-specific exception types
        target = f" '{camera_id}'" if camera_id else ""
        raise CameraTestError(f"Failed to connect to camera{target}: {exc}") from exc

    if hasattr(cam, "IsConnected"):
        try:
            is_connected = cam.IsConnected()
        except Exception as exc:
            raise CameraTestError(f"Camera connection could not be verified: {exc}") from exc
        if not is_connected:
            raise CameraTestError("Camera connection did not reach a connected state.")


def _capture_frames(
    cam: Any,
    frame_count: int,
    grab_timeout_ms: int,
    numpy_module: Any,
) -> tuple[Any, Any, int, float]:
    first_frame = None
    last_frame = None
    frames_captured = 0
    started_at = perf_counter()

    for index in range(frame_count):
        image = _get_image(cam, grab_timeout_ms)
        try:
            frame = image.GetNPArray()
        except Exception as exc:
            raise CameraTestError(f"Failed to convert frame {index} to a NumPy array: {exc}") from exc

        if not isinstance(frame, numpy_module.ndarray):
            frame = numpy_module.asarray(frame)

        if first_frame is None:
            first_frame = frame.copy()
        last_frame = frame.copy()
        frames_captured += 1

    elapsed_seconds = perf_counter() - started_at
    if first_frame is None or last_frame is None:
        raise CameraTestError("No image frames were captured.")

    return first_frame, last_frame, frames_captured, elapsed_seconds


def _get_image(cam: Any, grab_timeout_ms: int) -> Any:
    try:
        return cam.GetImage(grab_timeout_ms)
    except TypeError:
        try:
            return cam.GetImage()
        except Exception as exc:
            raise CameraTestError(f"Failed to acquire image from camera: {exc}") from exc
    except Exception as exc:
        raise CameraTestError(f"Failed to acquire image from camera: {exc}") from exc


def _save_artifacts(first_frame: Any, last_frame: Any, output_dir: Path, cv2_module: Any) -> tuple[Path, Path]:
    first_frame_path = output_dir / "test_frame_first.jpg"
    last_frame_path = output_dir / "test_frame_last.jpg"

    if not cv2_module.imwrite(str(first_frame_path), first_frame):
        raise CameraTestError(f"Failed to write artifact: {first_frame_path}")
    if not cv2_module.imwrite(str(last_frame_path), last_frame):
        raise CameraTestError(f"Failed to write artifact: {last_frame_path}")

    return first_frame_path, last_frame_path


def _read_camera_metadata(cam: Any) -> CameraMetadata:
    return CameraMetadata(
        model=_read_optional_feature(cam, "DeviceModelName"),
        device_id=_read_optional_feature(cam, "DeviceID", "DeviceSerialNumber", "DeviceUserID"),
        ip_address=_read_optional_feature(cam, "GevCurrentIPAddress", "GevPersistentIPAddress"),
        pixel_format=_read_optional_feature(cam, "PixelFormat"),
        width=_coerce_int(_read_optional_feature(cam, "Width")),
        height=_coerce_int(_read_optional_feature(cam, "Height")),
    )


def _read_optional_feature(cam: Any, *feature_names: str) -> str | None:
    features = getattr(cam, "f", None)
    if features is None:
        return None

    for feature_name in feature_names:
        feature = getattr(features, feature_name, None)
        if feature is None:
            continue
        for getter_name in ("GetString", "GetValue", "GetInt", "Get"):
            getter = getattr(feature, getter_name, None)
            if getter is None:
                continue
            try:
                value = getter()
            except Exception:
                continue
            if value is None:
                continue
            return str(value)
        value = getattr(feature, "value", None)
        if value is not None:
            return str(value)

    return None


def _coerce_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _disconnect_camera(cam: Any) -> None:
    for method_name in ("Disconnect", "Close"):
        method = getattr(cam, method_name, None)
        if method is None:
            continue
        try:
            method()
        except Exception:
            return
        return


def _read_module_version(module: Any) -> str:
    version = getattr(module, "__version__", None)
    if version is not None:
        return str(version)
    return "unknown"
