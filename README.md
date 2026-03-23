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
python -m src.main --json
```

Arguments:

- `--camera-id`: target a specific camera deterministically
- `--grab-timeout-ms`: per-frame timeout in milliseconds
- `--expected-fps-threshold`: minimum FPS required for a passing run
- `--preview`: open a lightweight live preview window
- `--stream-seconds`: auto-stop preview after the given duration
- `--preview-max-width`: downscale preview display width to keep the window light
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
