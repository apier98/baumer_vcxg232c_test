# Wiring Manual

## Practical Step-by-Step Guide

**System:** FUYU FSK40 linear guide + TB6600 driver + FPS-1A-NPN-NO limit switches + Arduino Uno + 220VAC ? 36VDC power

---

## Components

* 1 × FUYU FSK40 linear guide with 4-wire stepper motor
* 2 × FUYU FPS-1A-NPN-NO limit switches (3-wire)
* 1 × TB6600 microstep driver (9–42 VDC)
* 1 × 220 VAC ? 36 VDC power supply
* 1 × XL4016 step-down converter (for 12 VDC)
* 1 × Arduino Uno R3

---

## Guiding Principle

* Do NOT connect everything at once.
* Build and test one block at a time.
* Always work with power OFF, then verify with measurements.

---

## System Overview

### Functional Blocks

1. **Main power**: 220 VAC ? 36 VDC
2. **Motor power**: 36 VDC ? TB6600 ? stepper motor
3. **Sensor power**: 36 VDC ? XL4016 ? 12 VDC ? limit switches
4. **Control logic**: Arduino ? TB6600 + limit switch inputs

### Logical Diagram

```
220 VAC ? Power Supply (36V)
36V ? TB6600
36V ? XL4016 ? 12V ? limit switches
Arduino ? STEP / DIR / ENA
Limit switches ? Arduino (pull-up logic)
```

---

## Terminal Definitions

### Power Supply (220VAC ? 36VDC)

| Terminal | Meaning      | Use                               |
| -------- | ------------ | --------------------------------- |
| L        | AC Line      | 220VAC input                      |
| N        | AC Neutral   | 220VAC input                      |
| GROUND   | Earth        | Safety grounding                  |
| +V       | +36V DC      | To TB6600 and XL4016              |
| -V       | 0V DC        | Common ground                     |
| V-ADJ    | Voltage trim | Do not adjust without measurement |

---

### TB6600 Driver

| Terminal    | Function           |
| ----------- | ------------------ |
| VCC         | Power input (+36V) |
| GND         | Ground             |
| A+ / A-     | Motor coil 1       |
| B+ / B-     | Motor coil 2       |
| PUL+ / PUL- | Step signal        |
| DIR+ / DIR- | Direction          |
| ENA+ / ENA- | Enable (optional)  |

---

### Limit Switch (FPS-1A-NPN-NO)

| Wire  | Meaning         | Notes            |
| ----- | --------------- | ---------------- |
| Brown | +12V            | From XL4016      |
| Blue  | 0V              | Shared ground    |
| Black | Output (NPN-NO) | To Arduino input |

---

## Limit Switch Logic (Pull-up)

* **Inactive** ? open circuit ? Arduino reads HIGH
* **Active** ? pulled to GND ? Arduino reads LOW

Use:

* `INPUT_PULLUP` or
* External resistor (4.7k–10k)

---

## Wiring Map

### Main Power

| From   | To         | Purpose         |
| ------ | ---------- | --------------- |
| 220V L | PSU L      | Line            |
| 220V N | PSU N      | Neutral         |
| Earth  | PSU GND    | Safety          |
| PSU +V | TB6600 VCC | Driver power    |
| PSU -V | TB6600 GND | Reference       |
| PSU +V | XL4016 IN+ | Step-down input |
| PSU -V | XL4016 IN- | Ground          |

---

### XL4016 + Sensors

| From             | To               |
| ---------------- | ---------------- |
| OUT+             | Brown (switch 1) |
| OUT-             | Blue (switch 1)  |
| OUT+             | Brown (switch 2) |
| OUT-             | Blue (switch 2)  |
| OUT-             | Arduino GND      |
| Black (switch 1) | Arduino D2       |
| Black (switch 2) | Arduino D3       |

---

### Arduino ? TB6600

| Arduino | TB6600 | Notes        |
| ------- | ------ | ------------ |
| 5V      | PUL+   | Common-anode |
| 5V      | DIR+   |              |
| 5V      | ENA+   | Optional     |
| D8      | PUL-   | STEP         |
| D9      | DIR-   | Direction    |
| D10     | ENA-   | Optional     |

?? Never connect 36V to Arduino

---

### Stepper Motor

* Identify coils with multimeter
* Connect one pair ? A+/A-
* Connect other pair ? B+/B-

---

## Step-by-Step Procedure

### Step 0 – Preparation

* Label wires
* Prepare tools
* Ensure power OFF

---

### Step 1 – Power Supply

* Connect AC
* Measure output: ~36V

---

### Step 2 – XL4016 Setup

* Connect input
* Adjust output to 12V
* Verify stability

---

### Step 3 – Power Sensors

* Brown ? +12V
* Blue ? GND

---

### Step 4 – Test Sensor Output

* Measure black wire behavior
* Confirm sinking output

---

### Step 5 – TB6600 Power

* Connect 36V to driver
* Verify polarity

---

### Step 6 – Motor Wiring

* Identify coils
* Connect to A/B terminals

---

### Step 7 – Arduino ? Driver

* Connect STEP/DIR
* Keep logic separate from power

---

### Step 8 – Sensors ? Arduino

* Connect black wires to D2/D3
* Enable pull-up
* Share ground

---

### Step 9 – First Startup

* Power logic first
* Test small movements
* Verify limit switches

---

## Pin Summary

| Function | Pin |
| -------- | --- |
| STEP     | D8  |
| DIR      | D9  |
| ENA      | D10 |
| Limit 1  | D2  |
| Limit 2  | D3  |

---

## Common Mistakes

* Applying 36V or 12V to Arduino pins
* Not identifying motor coils
* Powering sensors before setting 12V
* Working under power
* Misusing NPN output
* Missing common ground

---

## Arduino Software Plan

### Purpose

This section defines the minimum software specification needed to write, test, and validate the Arduino firmware for the vertical motion axis.

The firmware is responsible for:

* driving the TB6600 stepper driver
* reading the two FUYU FPS-1A-NPN-NO limit switches
* enforcing safe motion limits
* exposing a simple command interface to the host PC

---

## Firmware Scope

### Main responsibilities

1. Initialize pins and safe startup states
2. Read limit switches with pull-up logic
3. Control motor direction and step pulses
4. Manage driver enable/disable
5. Execute homing sequence
6. Move to requested positions within allowed travel
7. Stop motion on faults or switch events
8. Report status to the host computer over serial

---

## Hardware Assumptions

### Pin Mapping

| Function       | Arduino Pin | TB6600 / Device          |
| -------------- | ----------- | ------------------------ |
| STEP           | D8          | PUL-                     |
| DIR            | D9          | DIR-                     |
| ENABLE         | D10         | ENA-                     |
| Limit switch 1 | D2          | Black wire sensor 1      |
| Limit switch 2 | D3          | Black wire sensor 2      |
| Logic +5V      | 5V          | PUL+, DIR+, ENA+         |
| Logic GND      | GND         | Sensor 0V / common logic |

### Input Logic

Both sensors are assumed to be wired as NPN-NO with `INPUT_PULLUP`.

* `HIGH` = sensor inactive
* `LOW` = sensor active

### Naming Convention

The two switches must be assigned explicit meanings in software:

* `LIMIT_BOTTOM`
* `LIMIT_TOP`

Do not leave them as generic switch 1 and switch 2 in code.

---

## Configuration Values

These values must be filled in before final firmware is considered complete.

```md
MOTOR_FULL_STEPS_PER_REV = [example: 200]
TB6600_MICROSTEP = [example: 8, 16, 32]
SCREW_MM_PER_REV = [mechanical value]
STEPS_PER_MM = MOTOR_FULL_STEPS_PER_REV * TB6600_MICROSTEP / SCREW_MM_PER_REV

MAX_TRAVEL_MM = [usable axis travel]
HOMING_DIRECTION = [UP or DOWN]
HOMING_FAST_SPEED = [steps/s]
HOMING_SLOW_SPEED = [steps/s]
MOVE_SPEED = [steps/s]
ACCELERATION = [steps/s^2]
HOMING_BACKOFF_MM = [small safe value]
MOTION_TIMEOUT_MS = [maximum allowed duration]
```

### Required Mechanical Inputs

Before coding final motion logic, collect these values:

* motor step angle or steps/rev
* TB6600 microstep DIP setting
* FKS40 transmission pitch or mm/rev
* total usable Z travel
* desired home reference position
* maximum safe speed
* maximum safe acceleration

---

## Firmware State Model

The firmware should use a simple state machine.

### Suggested states

* `BOOT`
* `IDLE`
* `HOMING`
* `READY`
* `MOVING`
* `STOPPED`
* `FAULT`

### State meanings

| State   | Meaning                               |
| ------- | ------------------------------------- |
| BOOT    | Startup, pins not yet validated       |
| IDLE    | Powered but not homed yet             |
| HOMING  | Performing homing cycle               |
| READY   | Homed and ready to receive moves      |
| MOVING  | Executing commanded move              |
| STOPPED | Motion stopped by user or limit event |
| FAULT   | Unsafe or undefined condition         |

### State rules

* On power-up, enter `BOOT`
* After initialization, enter `IDLE`
* No normal move is allowed before successful homing
* Any invalid sensor condition or timeout moves system to `FAULT`
* Recovery from `FAULT` should require explicit reset or re-homing

---

## Startup Behavior

### Required startup sequence

1. Configure STEP, DIR, ENA as outputs
2. Configure limit switch pins as `INPUT_PULLUP`
3. Put motor output in a safe state
4. Start serial communication
5. Read both limit switches
6. Validate switch state combination
7. Stay in `IDLE` until homing command is received, or auto-home if desired

### Safe startup rules

* Motor must not move automatically unless this is explicitly required
* Driver should start disabled or in known safe state
* If both limit switches are active at boot, enter `FAULT`
* If home-direction switch is already active at boot, use a recovery routine before homing

---

## Homing Plan

### Goal

Establish a repeatable mechanical zero position.

### Recommended homing sequence

1. Enable driver
2. Move in homing direction at low or medium speed
3. Stop when home switch activates
4. Back off by `HOMING_BACKOFF_MM`
5. Approach again slowly
6. Stop on switch activation
7. Set current position as zero or defined home offset
8. Enter `READY`

### Homing safety checks

* If the opposite limit activates unexpectedly, stop and go to `FAULT`
* If no switch is reached before timeout, go to `FAULT`
* If both switches become active, go to `FAULT`

### Home reference

Define one switch as the real home switch:

```md
HOME_SWITCH = LIMIT_BOTTOM   # or LIMIT_TOP
ZERO_OFFSET_MM = [value]
```

---

## Motion Control Plan

### Required motion commands

* relative move
* absolute move
* jog positive
* jog negative
* stop
* enable driver
* disable driver

### Motion rules

* No motion unless system is in `READY`
* Reject commands beyond software travel range
* Stop immediately if forbidden limit switch activates
* Keep current position updated in steps and in mm

### Coordinate system

```md
position_steps
position_mm = position_steps / STEPS_PER_MM
```

### Software limits

```md
MIN_POS_MM = 0
MAX_POS_MM = [usable travel]
```

Moves outside this range must be rejected before motion begins.

---

## Limit Switch Handling Plan

### Sensor interpretation

| Sensor state | Arduino read | Meaning    |
| ------------ | ------------ | ---------- |
| Inactive     | HIGH         | No trigger |
| Active       | LOW          | Triggered  |

### Runtime behavior

* If `LIMIT_TOP` activates while moving upward, stop immediately
* If `LIMIT_BOTTOM` activates while moving downward, stop immediately
* If a limit activates when moving away from it, log status but do not fault unless behavior is inconsistent

### Fault conditions

Trigger `FAULT` when:

* both limits are active together
* motion continues after a stop request
* homing times out
* switch behavior is electrically unstable

### Debounce / filtering

Even with non-contact sensors, add a small validation window.

Suggested approach:

* sample input multiple times over a few milliseconds
* only accept state change if stable

---

## Driver Control Plan

### TB6600 usage

Assumed common-anode wiring:

* Arduino 5V ? `PUL+`, `DIR+`, `ENA+`
* Arduino digital outputs ? `PUL-`, `DIR-`, `ENA-`

### Enable strategy

Decide one of the two modes and document it clearly:

#### Mode A – Always enabled during operation

* enable once after startup
* disable only on fault or shutdown

#### Mode B – Enable only during movement

* enable before motion
* disable after move complete

For initial development, **Mode A** is simpler.

### Pulse generation requirements

The code must define:

* minimum pulse HIGH time
* minimum pulse LOW time
* DIR setup time before STEP pulses

These values should be taken from the TB6600 documentation or tested conservatively.

---

## Serial Command Interface Plan

### Goal

Allow the PC to command the axis from a terminal, script, or vision application.

### Recommended command set

```text
PING
STATUS
HOME
STOP
ENABLE
DISABLE
MOVE_ABS <mm>
MOVE_REL <mm>
JOG_UP <mm>
JOG_DOWN <mm>
GET_POS
SET_ZERO
HELP
```

### Example responses

```text
OK
ERR NOT_HOMED
ERR LIMIT_ACTIVE
ERR OUT_OF_RANGE
STATE READY
POS 123.40
LIMITS TOP=0 BOTTOM=1
```

### Parsing rules

* one command per line
* trim spaces
* reject malformed commands cleanly
* always return a response string

---

## Status Reporting Plan

The firmware should expose at least:

* current state
* current position in steps and mm
* homed / not homed
* limit switch states
* driver enabled / disabled
* last error code

### Suggested status format

```text
STATE=READY;POS_MM=125.00;TOP=0;BOTTOM=0;EN=1;ERR=0
```

---

## Fault Handling Plan

### Enter `FAULT` on

* both limits active
* timeout during homing or move
* command beyond software limits
* impossible state transition
* driver disabled unexpectedly during commanded motion

### On fault

1. stop pulse generation
2. disable movement commands
3. optionally disable driver
4. report error over serial
5. require `RESET` or new `HOME`

### Suggested fault codes

```text
1 = BOTH_LIMITS_ACTIVE
2 = HOMING_TIMEOUT
3 = MOVE_TIMEOUT
4 = OUT_OF_RANGE
5 = NOT_HOMED
6 = INVALID_STATE
7 = SENSOR_FAULT
```

---

## Minimum Test Plan

### Test 1 – Pin sanity

* verify serial starts
* verify sensor states print correctly
* verify enable toggles correctly

### Test 2 – Single-step motion

* issue a few slow steps
* confirm axis direction
* reverse and confirm opposite direction

### Test 3 – Homing

* run homing at low speed
* verify first contact, backoff, second contact
* confirm zero set correctly

### Test 4 – Limit protection

* move toward top limit and verify stop
* move toward bottom limit and verify stop

### Test 5 – Command parser

* send valid and invalid commands
* verify clean responses

### Test 6 – Fault recovery

* simulate timeout or conflicting switch state
* verify transition to `FAULT`
* verify re-home procedure works

---

## Code Structure Recommendation

Suggested file/module layout:

```text
config.h           // pins, constants, motion limits
io.h / io.cpp      // read switches, control enable pin
motion.h / motion.cpp  // step generation and movement
protocol.h / protocol.cpp // serial command parsing
main.ino           // setup(), loop(), state machine
```

If written as a single sketch initially, still keep the logic separated into sections:

* configuration
* state machine
* switch reading
* stepping functions
* motion routines
* serial parsing

---

## Open Items Before Final Code

Fill in these blanks before implementing the production firmware:

```md
[ ] Which switch is TOP and which is BOTTOM?
[ ] Which switch is the HOME reference?
[ ] What is the exact TB6600 microstep setting?
[ ] What is the real steps/mm value?
[ ] What is the usable travel in mm?
[ ] What max speed is mechanically safe?
[ ] What acceleration is mechanically safe?
[ ] Should homing happen automatically at boot?
[ ] Should ENA be used dynamically or kept always enabled?
[ ] Which serial commands are required by the PC software?
```

---

## Deliverables To Prepare Next

After this Markdown plan, the next useful documents are:

1. **Minimal Arduino test sketch**

   * pin setup
   * limit switch readout
   * manual jog test

2. **Operational firmware spec**

   * filled mechanical constants
   * final command protocol
   * state diagram

3. **Host integration note**

   * how the PC software sends commands
   * expected command/response timing

---

## Final Note

This document is now sufficient to serve as a **code-planning context file** for the Arduino firmware.
It is not yet the final firmware itself, but it defines the structure, safety rules, and missing parameters needed before implementation.

