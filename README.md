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
- Baumer Python SDK package: `neoapi`
- `numpy`
- `opencv-python`

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

## Commands

### Preflight check

This validates that Python can import the required runtime packages without trying to connect to the camera:

```powershell
python -m src.main --preflight-only
```

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

### Useful options

```powershell
python -m src.main --camera-id <camera-id>
python -m src.main --grab-timeout-ms 1000
python -m src.main --expected-fps-threshold 30
python -m src.main --json
```

Arguments:

- `--camera-id`: target a specific camera deterministically
- `--grab-timeout-ms`: per-frame timeout in milliseconds
- `--expected-fps-threshold`: minimum FPS required for a passing run
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

## Current scope

This repository currently implements the baseline camera-only validation path.

It does not yet include:

- Arduino-triggered motion coordination
- FFmpeg/H.265 encoding
- cloud upload
- long-running soak tests

Those are planned follow-on phases after the baseline camera workflow is stable.
