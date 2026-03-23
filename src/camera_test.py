from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any

from .config import TestConfig
from .inference import InferenceError, LiveInferenceOverlay
from .result_types import CameraTestResult, LivePreviewResult


class CameraTestError(RuntimeError):
    """Raised when the headless camera test cannot complete."""


@dataclass(frozen=True)
class RuntimeDependencies:
    neoapi: Any
    cv2: Any
    numpy: Any


def load_runtime_dependencies(*, require_inference: bool = False) -> RuntimeDependencies:
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
    if require_inference:
        _load_optional_dependency(
            import_name="onnxruntime",
            package_name="onnxruntime",
            install_hint="Install it with `pip install -r requirements.txt`.",
            errors=errors,
        )
        _load_optional_dependency(
            import_name="PIL",
            package_name="pillow",
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

    dependencies = load_runtime_dependencies(require_inference=config.inference is not None)
    cam = dependencies.neoapi.Cam()
    window_name = "Baumer Live Preview"
    metadata = CameraMetadata(None, None, None, None, None, None)
    frames_displayed = 0
    frames_with_detections = 0
    started_at = 0.0
    inference_overlay = None
    inference_backend = None
    inference_bundle_dir = (
        config.inference.resolved_bundle_dir() if config.inference is not None else None
    )

    try:
        _connect_camera(cam, config.camera_id)
        metadata = _read_camera_metadata(cam)
        if config.inference is not None:
            try:
                inference_overlay = LiveInferenceOverlay(config.inference)
            except InferenceError as exc:
                raise CameraTestError(f"Failed to initialize RF-DETR inference: {exc}") from exc
            inference_backend = inference_overlay.backend
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
            preview_frame = _convert_frame_for_preview(
                frame=frame,
                pixel_format=metadata.pixel_format,
                cv2_module=dependencies.cv2,
            )
            detection_count = 0
            if inference_overlay is not None:
                try:
                    preview_frame, detection_count = inference_overlay.annotate_frame(
                        preview_frame,
                        cv2_module=dependencies.cv2,
                    )
                except InferenceError as exc:
                    raise CameraTestError(f"Failed to run RF-DETR inference: {exc}") from exc
                if detection_count > 0:
                    frames_with_detections += 1
            preview_frame = _resize_preview_frame(
                frame=preview_frame,
                cv2_module=dependencies.cv2,
                max_width=preview_max_width,
            )
            _draw_preview_overlay(
                frame=preview_frame,
                fps=frames_displayed / elapsed_seconds if elapsed_seconds > 0 else 0.0,
                pixel_format=metadata.pixel_format,
                cv2_module=dependencies.cv2,
                inference_backend=inference_backend,
                detection_count=detection_count,
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
            inference_enabled=config.inference is not None,
            inference_backend=inference_backend,
            inference_bundle_dir=inference_bundle_dir,
            frames_with_detections=frames_with_detections,
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
        inference_enabled=config.inference is not None,
        inference_backend=inference_backend,
        inference_bundle_dir=inference_bundle_dir,
        frames_with_detections=frames_with_detections,
    )


def run_interactive_mode(config: TestConfig) -> None:
    dependencies = load_runtime_dependencies()
    print(f"Connecting to camera '{config.camera_id or 'any'}'...")
    cam = dependencies.neoapi.Cam()

    try:
        _connect_camera(cam, config.camera_id)
        metadata = _read_camera_metadata(cam)
        
        # Ensure we show something even if metadata is empty
        model = metadata.model if metadata.model else "[Unknown Model]"
        device_id = metadata.device_id if metadata.device_id else "[Unknown ID]"
        ip = metadata.ip_address if metadata.ip_address else "[Unknown IP]"
        
        print(f"\nConnected to: {model} ({device_id}) at {ip}")
        print("Interactive mode active. Type 'help' for commands.\n")

        while True:
            try:
                line = input("camera> ").strip()
            except EOFError:
                print("\nExiting interactive mode (EOF).")
                break
            except KeyboardInterrupt:
                print("\nExiting interactive mode (Interrupt).")
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ("exit", "quit"):
                break
            elif cmd == "help":
                print("\nAvailable commands:")
                print("  ls [filter]         - List features (optional filter by name)")
                print("  get <feature>       - Get current value of a feature")
                print("  set <feature> <val> - Set a feature value")
                print("  info                - Show detailed camera metadata")
                print("  help                - Show this help message")
                print("  exit, quit          - Disconnect and exit\n")
            elif cmd == "ls":
                _list_features(cam, args[0] if args else "")
            elif cmd == "get":
                if not args:
                    print("Error: Missing feature name. Usage: get <feature>")
                else:
                    _get_feature(cam, args[0])
            elif cmd == "set":
                if len(args) < 2:
                    print("Error: Missing feature name or value. Usage: set <feature> <value>")
                else:
                    _set_feature(cam, args[0], args[1])
            elif cmd == "info":
                _print_camera_info(cam)
            else:
                print(f"Unknown command: {cmd}. Type 'help' for available commands.")

    except Exception as exc:
        print(f"\nInteractive session error: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        _disconnect_camera(cam)
        print("Camera disconnected.")


def _list_features(cam: Any, filter_str: str) -> None:
    try:
        features = cam.GetFeatureList()
        found = 0
        filter_str = filter_str.lower()
        print(f"{'Feature Name':<40} | {'Interface':<15} | {'Value'}")
        print("-" * 80)
        for feature in features:
            name = feature.GetName()
            if not filter_str or filter_str in name.lower():
                try:
                    val = _read_feature_value(feature)
                    interface = _read_feature_interface(feature)
                    print(f"{name:<40} | {interface:<15} | {val}")
                    found += 1
                except Exception as exc:
                    print(f"{name:<40} | {'[Unavailable]':<15} | [Error: {exc}]")
                    found += 1
        print(f"\nTotal: {found} features matched.")
    except Exception as exc:
        print(f"Failed to list features: {exc}")


def _get_feature(cam: Any, name: str) -> None:
    try:
        feature = _lookup_feature(cam, name)
        if feature is None:
            print(f"Error: Feature '{name}' not found.")
            return

        if not feature.IsReadable():
            print(f"Error: Feature '{name}' is not readable.")
            return

        print(f"{name} = {_read_feature_value(feature)}")
        print(f"  Interface: {_read_feature_interface(feature)}")
        print(f"  Access: {'RW' if feature.IsWritable() else 'R'}")
    except Exception as exc:
        print(f"Error reading feature '{name}': {exc}")


def _set_feature(cam: Any, name: str, value: str) -> None:
    try:
        feature = _lookup_feature(cam, name)
        if feature is None:
            print(f"Error: Feature '{name}' not found.")
            return

        if not feature.IsWritable():
            print(f"Error: Feature '{name}' is not writable.")
            return

        old_val = _read_feature_value(feature) if feature.IsReadable() else "[unknown]"
        feature.SetString(value)
        new_val = _read_feature_value(feature) if feature.IsReadable() else "[write-only]"
        print(f"Successfully updated {name}: {old_val} -> {new_val}")
    except Exception as exc:
        print(f"Error setting feature '{name}' to '{value}': {exc}")


def _print_camera_info(cam: Any) -> None:
    metadata = _read_camera_metadata(cam)
    print("\nCamera Information:")
    print(f"  Model Name:         {metadata.model}")
    print(f"  Device ID:          {metadata.device_id}")
    print(f"  Current IP:         {metadata.ip_address}")
    print(f"  Pixel Format:       {metadata.pixel_format}")
    print(f"  Image Size:         {metadata.width} x {metadata.height}")

    # Additional standard features if available
    for extra in ["DeviceVendorName", "DeviceVersion", "DeviceFirmwareVersion", "GevCurrentSubnetMask"]:
        val = _read_optional_feature(cam, extra)
        if val:
            print(f"  {extra:<20}: {val}")
    print("")


def describe_runtime() -> dict[str, str]:
    dependencies = load_runtime_dependencies()
    versions = {
        "neoapi": _read_module_version(dependencies.neoapi),
        "opencv-python": _read_module_version(dependencies.cv2),
        "numpy": _read_module_version(dependencies.numpy),
    }
    versions["onnxruntime"] = _read_optional_module_version("onnxruntime")
    versions["pillow"] = _read_optional_module_version("PIL")
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
        errors.append(_format_dependency_import_error(package_name, exc, install_hint))
    return None


def _format_dependency_import_error(
    package_name: str,
    exc: Exception,
    install_hint: str,
) -> str:
    message = f"{package_name} failed to import: {exc}. {install_hint}"
    error_text = f"{type(exc).__name__}: {exc}".lower()
    if package_name == "onnxruntime" and (
        "_array_api" in error_text
        or "compiled using numpy 1.x" in error_text
        or "numpy 2" in error_text
    ):
        return (
            f"{package_name} failed to import because the installed ONNX Runtime wheel is not compatible "
            "with the current NumPy version. Reinstall a NumPy 1.x runtime that matches the bundle, for example "
            "`pip install --force-reinstall numpy==1.26.4 onnxruntime==1.17.1`, or use "
            "`onnxruntime-gpu==1.17.1` instead of `onnxruntime==1.17.1` if you need CUDA."
        )
    return message


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


def _convert_frame_for_preview(frame: Any, pixel_format: str | None, cv2_module: Any) -> Any:
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

    return preview_frame


def _resize_preview_frame(frame: Any, cv2_module: Any, max_width: int) -> Any:
    height, width = frame.shape[:2]
    if width > max_width:
        scale = max_width / width
        return cv2_module.resize(
            frame,
            (int(width * scale), int(height * scale)),
            interpolation=cv2_module.INTER_AREA,
        )
    return frame


def _draw_preview_overlay(
    frame: Any,
    fps: float,
    pixel_format: str | None,
    cv2_module: Any,
    inference_backend: str | None = None,
    detection_count: int = 0,
) -> None:
    overlay_lines = [
        f"FPS {fps:.2f}",
        f"FORMAT {pixel_format or 'unknown'}",
    ]
    if inference_backend is not None:
        overlay_lines.extend(
            [
                f"INFER {inference_backend}",
                f"DETECTIONS {detection_count}",
            ]
        )
    overlay_lines.append("Press Q or Esc to quit")
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


def _lookup_feature(cam: Any, name: str) -> Any | None:
    features = getattr(cam, "f", None)
    if features is not None:
        feature = getattr(features, name, None)
        if feature is not None:
            return feature

    getter = getattr(cam, "GetFeature", None)
    if getter is None:
        return None

    try:
        return getter(name)
    except Exception:
        return None


def _read_feature_value(feature: Any) -> str:
    if not feature.IsReadable():
        return "[Not Readable]"

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

    raise RuntimeError("No readable value getter available.")


def _read_feature_interface(feature: Any) -> str:
    for getter_name in ("GetInterfaceName", "GetInterface"):
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

    return "[Unknown]"


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


def _read_optional_module_version(import_name: str) -> str:
    probe = (
        "import importlib, sys\n"
        "name = sys.argv[1]\n"
        "try:\n"
        "    module = importlib.import_module(name)\n"
        "except ModuleNotFoundError:\n"
        "    raise SystemExit(2)\n"
        "except Exception as exc:\n"
        "    print(f'import_failed: {exc}')\n"
        "    raise SystemExit(1)\n"
        "version = getattr(module, '__version__', None)\n"
        "print(version if version is not None else 'unknown')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe, import_name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip() or "unknown"
    if result.returncode == 2:
        return "not_installed"
    error = result.stdout.strip() or result.stderr.strip()
    return error or "import_failed"
