Baumer VCXG.2-32C Headless Test Plan

This plan is designed to verify the camera's baseline functionality, network stability, and lighting/focus without introducing the complexity of a GUI or the final AWS S3 pipeline.

Phase 1: Network & Physical Setup (Crucial for GigE)

Before running any code, the Lenovo Legion laptop must be configured to handle the high throughput of the GigE camera.

Physical Connections:

Ensure the Baumer camera is connected via the Gigabit Ethernet cable (blue wire in your diagram) to the laptop.

Ensure the 24V step-down converter is powering the camera via the 8-pin M12 connector.

Turn on the NEEWER lighting system.

Network Adapter Settings (Windows):

Go to Network Connections -> Right-click the Ethernet adapter -> Properties.

Select Internet Protocol Version 4 (TCP/IPv4) -> Properties.

Set a Static IP (e.g., 192.168.1.10) and Subnet Mask (255.255.255.0).

Go back to Adapter Properties -> Configure... -> Advanced tab.

Find Jumbo Frames (or Jumbo Packet) and set it to 9014 Bytes (or the maximum 9KB option). This prevents dropped frames.

Find Interrupt Moderation and ensure it is Disabled (reduces latency).

Baumer GAPI / neoAPI Installation:

Ensure the Baumer GigE Filter Driver is installed on the Ethernet adapter (usually done via the Baumer Camera Explorer installer).

Install the python SDK: pip install neoapi opencv-python.

Phase 2: Headless Behavior Test

We will run a Python script that performs the following automated sequence:

Detects and connects to the camera.

Reads the camera's current IP and model name to verify communication.

Grabs a defined number of frames (e.g., 200) as fast as possible.

Uses GetNPArray() to convert the buffer to a NumPy array (Zero-Copy evaluation).

Saves the very first frame and the very last frame to disk.

Calculates the actual Frames Per Second (FPS) to ensure we are hitting near the 39 fps maximum of the camera.

Phase 3: Verification

After running the script, check the terminal output for:

No exceptions/errors: Validates neoapi and the IP setup.

FPS: Should be stable (around 35-39 FPS depending on exposure time).

Saved Images: Open test_frame_first.jpg and test_frame_last.jpg in your file explorer. Check if the focus is sharp on the FSK40 linear guide and if the NEEWER lighting is providing sufficient illumination without overexposing the scene.

Phase 4: Next Steps (Post-Test)

Once this test passes reliably:

We will integrate the subprocess FFmpeg pipe to encode the Numpy arrays into H.265 (HEVC).

We will merge this script with the Arduino serial commands to trigger the camera exactly when the stepper motor reaches the target positions.

## Implemented baseline entry point

The project now includes a Python headless test harness aligned with this plan:

`pip install -r requirements.txt`

Installs the open-source runtime packages for the harness.

Install the official Baumer `neoAPI` Python package separately from Baumer's SDK/tooling for your Python version.

`python -m src.main --preflight-only`

Validates that the Python runtime can import `neoapi`, `opencv-python`, and `numpy`.

`python -m src.main --frame-count 200 --output-dir output`

Runs the bounded capture test, prints a pass/fail summary, and writes:

`output\test_frame_first.jpg`

`output\test_frame_last.jpg`

The script also supports:

- `--camera-id <id>` for deterministic camera selection
- `--grab-timeout-ms <ms>` for acquisition timeout tuning
- `--expected-fps-threshold <fps>` for pass/fail tuning
- `--json` for machine-readable output
