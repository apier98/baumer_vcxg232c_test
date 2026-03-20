from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from time import perf_counter
from typing import Any

from .config import TestConfig
from .result_types import CameraTestResult, LivePreviewResult


class CameraTestError(RuntimeError):
    """Raised when the headless camera test cannot complete."""


@dataclass(frozen=True)
class RuntimeDependencies:
    neoapi: Any
    cv2: Any
    numpy: Any


def load_runtime_dependencies() -> RuntimeDependencies:
    errors: list[str] = []

    neoapi = _load_optional_dependency(
        import_name="neoapi",
        package_name="neoapi",
        install_hint=(
            "Install Baumer's official neoAPI Python package for your Python version. "
            "Do not rely on the unrelated `neoapi` package from PyPI if it imports with Python 2 syntax."
        ),
        errors=errors,
    )
    cv2 = _load_optional_dependency(
        import_name="cv2",
        package_name="opencv-python",
        install_hint="Install it with `pip install -r requirements.txt`.",
        errors=errors,
    )
    numpy = _load_optional_dependency(
        import_name="numpy",
        package_name="numpy",
        install_hint="Install it with `pip install -r requirements.txt`.",
        errors=errors,
    )

    if errors:
        raise CameraTestError("Runtime dependency check failed:\n- " + "\n- ".join(errors))

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


def run_live_preview(
    config: TestConfig,
    stream_seconds: float | None = None,
    preview_max_width: int = 1280,
) -> LivePreviewResult:
    if config.grab_timeout_ms <= 0:
        raise CameraTestError("grab_timeout_ms must be greater than zero.")
    if preview_max_width <= 0:
        raise CameraTestError("preview_max_width must be greater than zero.")
    if stream_seconds is not None and stream_seconds <= 0:
        raise CameraTestError("stream_seconds must be greater than zero when provided.")

    dependencies = load_runtime_dependencies()
    cam = dependencies.neoapi.Cam()
    window_name = "Baumer Live Preview"
    metadata = CameraMetadata(None, None, None, None, None, None)
    frames_displayed = 0
    started_at = 0.0

    try:
        _connect_camera(cam, config.camera_id)
        metadata = _read_camera_metadata(cam)
        dependencies.cv2.namedWindow(window_name, dependencies.cv2.WINDOW_NORMAL)
        started_at = perf_counter()

        while True:
            image = _get_image(cam, config.grab_timeout_ms)
            try:
                frame = image.GetNPArray()
            except Exception as exc:
                raise CameraTestError(f"Failed to convert preview frame to a NumPy array: {exc}") from exc

            if not isinstance(frame, dependencies.numpy.ndarray):
                frame = dependencies.numpy.asarray(frame)

            frames_displayed += 1
            elapsed_seconds = perf_counter() - started_at
            preview_frame = _prepare_preview_frame(
                frame=frame,
                pixel_format=metadata.pixel_format,
                cv2_module=dependencies.cv2,
                max_width=preview_max_width,
            )
            _draw_preview_overlay(
                frame=preview_frame,
                fps=frames_displayed / elapsed_seconds if elapsed_seconds > 0 else 0.0,
                pixel_format=metadata.pixel_format,
                cv2_module=dependencies.cv2,
            )
            dependencies.cv2.imshow(window_name, preview_frame)

            key = dependencies.cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break

            if stream_seconds is not None and elapsed_seconds >= stream_seconds:
                break

            if dependencies.cv2.getWindowProperty(window_name, dependencies.cv2.WND_PROP_VISIBLE) < 1:
                break
    except CameraTestError as exc:
        return LivePreviewResult(
            success=False,
            camera_model=metadata.model,
            camera_id=metadata.device_id,
            camera_ip=metadata.ip_address,
            pixel_format=metadata.pixel_format,
            image_width=metadata.width,
            image_height=metadata.height,
            frames_displayed=frames_displayed,
            elapsed_seconds=0.0 if started_at == 0.0 else perf_counter() - started_at,
            fps=0.0,
            error=str(exc),
        )
    finally:
        try:
            dependencies.cv2.destroyAllWindows()
        except Exception:
            pass
        _disconnect_camera(cam)

    elapsed_seconds = perf_counter() - started_at
    fps = frames_displayed / elapsed_seconds if elapsed_seconds > 0 else 0.0
    return LivePreviewResult(
        success=True,
        camera_model=metadata.model,
        camera_id=metadata.device_id,
        camera_ip=metadata.ip_address,
        pixel_format=metadata.pixel_format,
        image_width=metadata.width,
        image_height=metadata.height,
        frames_displayed=frames_displayed,
        elapsed_seconds=elapsed_seconds,
        fps=fps,
    )


def describe_runtime() -> dict[str, str]:
    dependencies = load_runtime_dependencies()
    versions = {
        "neoapi": _read_module_version(dependencies.neoapi),
        "opencv-python": _read_module_version(dependencies.cv2),
        "numpy": _read_module_version(dependencies.numpy),
    }
    return versions


def _load_optional_dependency(
    import_name: str,
    package_name: str,
    install_hint: str,
    errors: list[str],
) -> Any:
    try:
        return import_module(import_name)
    except ModuleNotFoundError:
        errors.append(
            f"{package_name} is not installed or not visible to this interpreter. {install_hint}"
        )
    except SyntaxError as exc:
        errors.append(
            f"{package_name} failed to import because the installed package is not Python 3 compatible "
            f"({exc.msg} in {exc.filename}:{exc.lineno}). {install_hint}"
        )
    except Exception as exc:
        errors.append(f"{package_name} failed to import: {exc}. {install_hint}")
    return None


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


def _prepare_preview_frame(frame: Any, pixel_format: str | None, cv2_module: Any, max_width: int) -> Any:
    preview_frame = frame
    normalized_format = (pixel_format or "").lower()

    if normalized_format == "bayerrg8":
        preview_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_BayerRG2BGR)
    elif normalized_format == "bayerbg8":
        preview_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_BayerBG2BGR)
    elif normalized_format == "bayergr8":
        preview_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_BayerGR2BGR)
    elif normalized_format == "bayergb8":
        preview_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_BayerGB2BGR)
    elif len(getattr(frame, "shape", ())) == 2:
        preview_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_GRAY2BGR)

    height, width = preview_frame.shape[:2]
    if width > max_width:
        scale = max_width / width
        preview_frame = cv2_module.resize(
            preview_frame,
            (int(width * scale), int(height * scale)),
            interpolation=cv2_module.INTER_AREA,
        )

    return preview_frame


def _draw_preview_overlay(frame: Any, fps: float, pixel_format: str | None, cv2_module: Any) -> None:
    overlay_lines = [
        f"FPS {fps:.2f}",
        f"FORMAT {pixel_format or 'unknown'}",
        "Press Q or Esc to quit",
    ]
    y = 30
    for line in overlay_lines:
        cv2_module.putText(
            frame,
            line,
            (10, y),
            cv2_module.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2_module.LINE_AA,
        )
        y += 30


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
