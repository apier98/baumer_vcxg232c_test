from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .camera_test import (
    CameraTestError,
    describe_runtime,
    run_headless_test,
    run_interactive_mode,
    run_live_preview,
)
from .config import InferenceConfig, TestConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Headless validation harness for the Baumer VCXG.2-32C camera."
    )
    parser.add_argument(
        "--frame-count",
        type=int,
        default=200,
        help="Number of frames to acquire during the validation run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where the first and last captured frames will be written.",
    )
    parser.add_argument(
        "--camera-id",
        type=str,
        default=None,
        help="Optional deterministic camera identifier to pass to neoapi.",
    )
    parser.add_argument(
        "--grab-timeout-ms",
        type=int,
        default=1000,
        help="Per-frame grab timeout in milliseconds.",
    )
    parser.add_argument(
        "--expected-fps-threshold",
        type=float,
        default=30.0,
        help="Minimum acceptable FPS for the test to pass.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate Python runtime dependencies without connecting to a camera.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the plain-text summary.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open a lightweight live preview window instead of running the bounded frame test.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enter interactive mode to get/set camera parameters.",
    )
    parser.add_argument(
        "--stream-seconds",
        type=float,
        default=None,
        help="Optional auto-stop duration for preview mode. Without this, preview runs until you press q or Esc.",
    )
    parser.add_argument(
        "--preview-max-width",
        type=int,
        default=1280,
        help="Maximum preview window width in pixels. Larger frames are downscaled for display only.",
    )
    parser.add_argument(
        "--infer",
        action="store_true",
        help=(
            "Run RF-DETR inference on preview frames. Uses bundles\\rfdetr by default unless "
            "--inference-bundle-dir is provided."
        ),
    )
    parser.add_argument(
        "--inference-bundle-dir",
        type=Path,
        default=None,
        help="Portable RF-DETR bundle directory. Preview mode only.",
    )
    parser.add_argument(
        "--inference-backend",
        choices=["auto", "tensorrt", "onnx", "pytorch"],
        default="auto",
        help="Inference backend preference for the RF-DETR bundle.",
    )
    parser.add_argument(
        "--inference-device",
        type=str,
        default=None,
        help="Inference device override, for example cpu, cuda, or cuda:0.",
    )
    parser.add_argument(
        "--inference-threshold",
        type=float,
        default=None,
        help="Optional RF-DETR score threshold override.",
    )
    parser.add_argument(
        "--inference-topk",
        type=int,
        default=None,
        help="Optional RF-DETR top-k override before post-processing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.json and not args.preflight_only:
        print(f"DEBUG: Starting main with args: {argv}")

    if args.preflight_only:
        return _run_preflight(json_output=args.json)

    inference_requested = args.infer or args.inference_bundle_dir is not None
    if inference_requested and not args.preview:
        parser.error("RF-DETR inference overlay is only supported with --preview.")
    if args.inference_threshold is not None and args.inference_threshold <= 0:
        parser.error("--inference-threshold must be greater than zero.")
    if args.inference_topk is not None and args.inference_topk <= 0:
        parser.error("--inference-topk must be greater than zero.")

    inference_config = None
    if inference_requested:
        inference_config = InferenceConfig(
            bundle_dir=args.inference_bundle_dir or Path("bundles") / "rfdetr",
            backend=args.inference_backend,
            device=args.inference_device,
            score_threshold=args.inference_threshold,
            topk=args.inference_topk,
        )

    config = TestConfig(
        frame_count=args.frame_count,
        output_dir=args.output_dir,
        camera_id=args.camera_id,
        grab_timeout_ms=args.grab_timeout_ms,
        expected_fps_threshold=args.expected_fps_threshold,
        inference=inference_config,
    )

    try:
        if args.interactive:
            run_interactive_mode(config)
            return 0
        elif args.preview:
            result = run_live_preview(
                config=config,
                stream_seconds=args.stream_seconds,
                preview_max_width=args.preview_max_width,
            )
        else:
            result = run_headless_test(config)
    except CameraTestError as exc:
        if args.json:
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"RESULT FAIL\nERROR {exc}")
        return 1

    if args.json:
        print(result.to_json())
    else:
        print(result.to_summary())

    return 0 if result.success else 1


def _run_preflight(json_output: bool) -> int:
    try:
        versions = describe_runtime()
    except CameraTestError as exc:
        if json_output:
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"RESULT FAIL\nERROR {exc}")
        return 1

    if json_output:
        print(json.dumps({"success": True, **versions}))
    else:
        print("RESULT PASS")
        print("RUNTIME neoapi=" + versions["neoapi"])
        print("RUNTIME opencv-python=" + versions["opencv-python"])
        print("RUNTIME numpy=" + versions["numpy"])
        print("RUNTIME onnxruntime=" + versions["onnxruntime"])
        print("RUNTIME pillow=" + versions["pillow"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
