Project Context: Baumer VCXG.2-32C Integration

1. Hardware Overview

Model: Baumer VCXG.2 - 32C (CX Series).

Resolution/Speed: 3.1 Megapixels (2048 x 1536) @ 39 fps.

Interface: Gigabit Ethernet (GigE Vision standard).

Power Options:

PoE (Power over Ethernet): Requires a PoE-enabled NIC, PoE Switch, or PoE Injector.

External Power: 8-pin M12 connector (typically 12-24V DC).

2. Network Configuration (Critical for Stability)

To ensure reliable high-speed data transfer and prevent dropped frames:

IP Addressing: Set a Static IP on the PC (e.g., 192.168.1.10, Subnet 255.255.255.0). Match the camera's subnet via "Force IP" in Baumer software if necessary.

Jumbo Frames: Must be enabled in the Network Card (NIC) settings, set to 9014 Bytes (or the highest available 9k value).

Drivers: Use the Baumer GigE Filter Driver to offload packet processing from the CPU.

Firewall: Ensure UDP ports are open or the firewall is disabled during testing to allow the GigE Vision stream.

3. Software Architecture (Python)

The goal is to manage two simultaneous streams, encode them efficiently, and upload to AWS S3.

Libraries & Tools

SDK: baumer-neoapi (The modern Pythonic successor to Baumer GAPI).

Encoding: FFmpeg (via subprocess pipes) is preferred over OpenCV VideoWriter for better control over compression (Size vs. Quality).

Cloud: boto3 for AWS S3 uploads.

Concurrency: Use multiprocessing for the dual-camera capture to bypass the Python GIL and threading for background S3 uploads.

Proposed Workflow

Capture: Use neoapi to grab frames as NumPy arrays (GetNPArray()).

Encode: Pipe raw bytes directly to an FFmpeg process using the H.265 (HEVC) codec for maximum quality-to-size ratio.

Note: Use hardware acceleration (NVENC for NVIDIA or QSV for Intel) if available to reduce CPU load.

Buffer: Implement a producer-consumer queue to handle potential spikes in processing/latency.

Storage: Save locally first, then trigger an asynchronous boto3 upload to S3 once the session ends.

4. Key Performance Tuning

Zero-Copy: Use neoapi's native memory handling to avoid expensive data duplication.

Interrupt Moderation: Disable in NIC settings to reduce latency.

FFmpeg Presets: Use -crf 23 (standard high quality) and -preset medium/slow for optimal compression.
