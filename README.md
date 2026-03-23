# Baumer VCXG.2-32C Headless Test Harness

This repository contains a small Python harness for validating a Baumer `VCXG.2-32C` GigE camera without a GUI.

The current implementation is focused on the first milestone documented in `docs\Baumer_VCXG_2-32C_headless_test_plan.md`:

- verify Python/runtime dependencies
- connect to the camera
- capture a fixed number of frames
- calculate effective FPS
- save the first and last frames for inspection
- report a clear pass/fail result

## Repository layout

```text
docs\                         Project notes, wiring, and implementation plans
src\                          Python test harness
requirements.txt              Python dependencies
README.md                     This file
```

## Requirements

- Windows host with Python available
- Baumer camera reachable over GigE
- Baumer official `neoAPI` Python package matching your installed Python version
- `numpy==1.26.4`
- `opencv-python`
- `onnxruntime==1.17.1` or `onnxruntime-gpu==1.17.1`
- `pillow==12.0.0`

## Network and hardware prerequisites

Before running the test, configure the camera link as described in the docs:

- connect the camera to the PC over Gigabit Ethernet
- power the camera correctly
- set a static IPv4 address on the PC and keep the camera on the same subnet
- enable Jumbo Frames on the NIC if supported
- install the Baumer GigE Filter Driver
- allow the required traffic through the Windows firewall if needed

See:

- `docs\baumer_camera_integration.md`
- `docs\Baumer_VCXG_2-32C_headless_test_plan.md`

## Installation

Create or activate your virtual environment, then install dependencies:

```powershell
pip install -r requirements.txt
```

For RF-DETR bundle inference, keep the environment aligned with the bundle runtime. The exported bundle you provided was built against:

- `numpy==1.26.4`
- `onnxruntime==1.17.1` or `onnxruntime-gpu==1.17.1`

Important environment warning for inference:

- do **not** keep `numpy 2.x` in this virtual environment for the current bundle/runtime stack
- install **only one** ONNX Runtime variant at a time:
  - `onnxruntime==1.17.1` for CPU
  - `onnxruntime-gpu==1.17.1` for CUDA
- if both `onnxruntime` and `onnxruntime-gpu` are installed together, Python may load the CPU wheel and you may see only `CPUExecutionProvider`

If this virtual environment already has `numpy 2.x`, force it back to the compatible stack before running preview inference:

```powershell
pip install --force-reinstall numpy==1.26.4 onnxruntime==1.17.1 pillow==12.0.0
```

If you want CUDA execution, install the GPU wheel instead of the CPU wheel:

```powershell
pip install --force-reinstall numpy==1.26.4 onnxruntime-gpu==1.17.1 pillow==12.0.0
```

If you previously installed both ONNX Runtime variants, clean the environment first:

```powershell
pip uninstall -y onnxruntime onnxruntime-gpu
pip install numpy==1.26.4 onnxruntime-gpu==1.17.1 pillow==12.0.0
```

You can verify that the GPU runtime is visible with:

```powershell
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

You should see `CUDAExecutionProvider` in the output before expecting GPU inference.

Then install the **official Baumer neoAPI Python package** that matches your Python version.

Important:

- do **not** rely on the unrelated `neoapi` package from PyPI if it throws Python 2 style syntax errors
- use the Baumer-provided wheel/installer that comes with their SDK or tools
- make sure the package matches your interpreter version, such as Python 3.10

## Commands

### Preflight check

This validates that Python can import the required runtime packages without trying to connect to the camera:

```powershell
python -m src.main --preflight-only
```

If preflight reports that `neoapi` is not Python 3 compatible, uninstall the incorrect package and install the Baumer-provided one instead.

Optional JSON output:

```powershell
python -m src.main --preflight-only --json
```

### Headless camera validation run

Run the default capture flow:

```powershell
python -m src.main --frame-count 200 --output-dir output
```

This command:

- connects to the camera
- captures `200` frames
- computes elapsed time and FPS
- writes:
  - `output\test_frame_first.jpg`
  - `output\test_frame_last.jpg`
- exits with code `0` on pass and non-zero on failure

### Live preview

If you want a lightweight visual check of the camera feed, use preview mode:

```powershell
python -m src.main --preview
```

This opens an OpenCV window with:

- the live camera image
- an FPS overlay
- the pixel format
- a quit hint

Press `q` or `Esc` to close the preview.

For a timed preview:

```powershell
python -m src.main --preview --stream-seconds 30
```

### Live preview with RF-DETR inference

To run your exported deployment bundle on top of the Baumer stream, use preview mode with inference enabled.

Recommended bundle location inside this repo:

- copy the **contents** of your exported folder into `bundles\rfdetr\`
- after copying, files such as `model.onnx`, `infer.py`, `model_config.json`, and `rfdetr_training\` should exist directly under `bundles\rfdetr\`

With your current export, that means copying the contents of:

- `C:\Users\andrea\projects\rfdetr_training\datasets\8cb2dc0f-6405-47fd-b4f9-332e2fdeaa19\deploy\checkpoint_portable_20260323_135651Z\`

Then run:

```powershell
python -m src.main --preview --infer
```

If you want to keep the timestamped export folder name instead, pass that directory explicitly:

```powershell
python -m src.main --preview --inference-bundle-dir C:\path\to\checkpoint_portable_20260323_135651Z
```

Useful inference options:

- `--inference-backend onnx` to force ONNX Runtime
- `--inference-threshold 0.5` to override the bundle score threshold
- `--inference-topk 100` to limit detections before final filtering
- `--inference-device cpu` to force CPU execution

For GPU inference, prefer this command once `CUDAExecutionProvider` is available:

```powershell
python -m src.main --preview --infer --inference-backend onnx --inference-device cuda
```

The preview overlay will show:

- stream FPS
- camera pixel format
- active inference backend
- detections found in the current frame

### Interactive parameter selection

If you want to interactively explore and test camera parameters (features), use the interactive mode:

```powershell
python -m src.main --interactive
```

Available commands in interactive mode:

- `ls [filter]`: List all available features (optionally filtered by name).
- `get <feature>`: Show the current value and metadata for a specific feature.
- `set <feature> <value>`: Update a feature's value.
- `info`: Display detailed camera metadata.
- `help`: Show the list of available commands.
- `exit` or `quit`: Disconnect and exit.

Example session:
```text
camera> ls Exposure
ExposureAuto                             | Enumeration     | Off
ExposureTime                             | Float           | 10000.0
...
camera> set ExposureTime 20000
Successfully updated ExposureTime: 10000.0 -> 20000.0
camera> info
...
camera> quit
```

### Useful options

```powershell
python -m src.main --camera-id <camera-id>
python -m src.main --grab-timeout-ms 1000
python -m src.main --expected-fps-threshold 30
python -m src.main --preview --preview-max-width 1280
python -m src.main --preview --infer
python -m src.main --preview --inference-bundle-dir bundles\rfdetr --inference-backend onnx
python -m src.main --json
```

Arguments:

- `--camera-id`: target a specific camera deterministically
- `--grab-timeout-ms`: per-frame timeout in milliseconds
- `--expected-fps-threshold`: minimum FPS required for a passing run
- `--preview`: open a lightweight live preview window
- `--stream-seconds`: auto-stop preview after the given duration
- `--preview-max-width`: downscale preview display width to keep the window light
- `--infer`: enable RF-DETR overlay using the default `bundles\rfdetr` bundle location
- `--inference-bundle-dir`: portable RF-DETR bundle directory to use instead of the default
- `--inference-backend`: choose `auto`, `onnx`, `tensorrt`, or `pytorch`
- `--inference-threshold`: override the bundle score threshold
- `--inference-topk`: override bundle top-k before post-processing
- `--inference-device`: choose a device such as `cpu` or `cuda`
- `--json`: machine-readable output

## Output format

Plain-text output includes:

- result status
- model
- camera identifier
- camera IP if available
- pixel format
- image size
- requested/captured frame count
- elapsed time
- FPS
- first/last frame paths
- error details on failure

## Typical workflow

1. Install dependencies.
2. Run `python -m src.main --preflight-only`.
3. Confirm the camera is powered and reachable on the configured network.
4. Run `python -m src.main --frame-count 200 --output-dir output`.
5. Inspect `output\test_frame_first.jpg` and `output\test_frame_last.jpg`.
6. Compare measured FPS with the expected operating range from the docs.
7. Copy your RF-DETR deployment bundle to `bundles\rfdetr` and run `python -m src.main --preview --infer` when you want live detection overlay.

## Current scope

This repository currently implements the baseline camera validation path plus optional RF-DETR inference overlay during live preview.

It does not yet include:

- Arduino-triggered motion coordination
- FFmpeg/H.265 encoding
- cloud upload
- long-running soak tests

Those are planned follow-on phases after the baseline camera workflow is stable.
