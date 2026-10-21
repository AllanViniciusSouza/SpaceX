# TwinCAT 3 Project Instructions

## Project

This is an industrial automation project developed using Beckhoff TwinCAT 3.

PLC programming language:

- IEC 61131-3 Structured Text
- Beckhoff TwinCAT 3 ST syntax

Primary development environment:

- TwinCAT 3 XAE
- Visual Studio / TwinCAT XAE Shell

Do not assume Siemens TIA Portal syntax.

---

# Project structure

Active solution: SpaceX.sln -> TwinCAT Project1/SpaceX.tsproj
(TwinCAT 3.1.4026).

| Path | Content |
| --- | --- |
| TwinCAT Project1/Sys1_Inbound | PLC project of the Inbound system (ADS port 851, PlcTask 10 ms, VISU_TASK) |
| TwinCAT Project1/Main | Main panel PLC project (ADS port 852, PlcTask1) |
| TwinCAT Project1/Sys_1_Inbound | TwinSAFE project (EL6910, TwinSafeGroup1) |
| TwinCAT Project1/Sys1_Inbound/MigrationReview | Review drafts of TIA routines, NOT compiled (MSBuild None items) |
| Reference_Project | Siemens TIA exports (SCL, PDF), comparison baseline |
| docs | Project documentation |
| tools | Offline Python helpers (inventory, staging, validation, safety audit) |

Main_PLC, SpaceX/SpaceX.tspproj and TwinCAT Project1/Untitled1..5 are not
part of the solution.

Register new POUs, DUTs and GVLs as Compile items in the .plcproj of their
PLC project. Place them in the folder of their area, for example POUs/SEW,
DUTs/SEW, DUTs/HMI, GVLs/HMI or GVLs/IO.

---

# System architecture

The system contains Beckhoff PLC control and SEW drives.

SEW communication is based on:

- SBusPLUS

IMPORTANT:

The drives in this project are NOT controlled using CiA402 unless explicitly
documented for a specific device.

Do not generate CiA402 state-machine logic for SEW drives by default.

---

# SEW drives

Known devices include:

## MPX23A

Example drive:

MPX23A-DSI10A-MPI-0460-5E3-CA-C

Project name example:

MPX23A_22kW

Communication/control:

SBusPLUS

---

## MOVIMOT / MOVI-C

Example device:

MMF31S02-D11-5D3-SFDI0-C/IV/BW1/DSI10A-0025

Before implementing drive communication, inspect the existing process-data
mapping in the TwinCAT project.

Never invent process-data words or bit definitions.

---

## Drive applications in this project

| Machine function | Drive | MOVIKIT module | Fieldbus profile | PLC communication FB |
| --- | --- | --- | --- | --- |
| VTD (vertical transfer device) | MOVIPRO MPX23A (22 kW) | MOVIKIT Positioning Drive | Standard 8 PD (PO/PI 1..8) | FB_SEW_Drive |
| Turntable (carousel) | SEW MOVI-C | MOVIKIT Positioning Drive | 8 PD, confirm in MOVISUITE | FB_SEW_Drive, extended only after the external-position words are confirmed |
| Buffer conveyors, roller conveyors | MOVIMOT flexible (MOVI-C) | MOVIKIT Velocity Drive | 5 PD basic profile (PO/PI 1..5) | FB_SEW_VelocityDrive |

Process-data reference: SEW manual 33959862 "MOVIKIT Positioning, Velocity"
(movikit_positioning_velocity_drive_.pdf), chapter 9. Words and bits marked
"P" in that manual exist only with MOVIKIT Positioning; never use them with
MOVIKIT Velocity. MOVIKIT Velocity always runs operating mode Speed (200)
and has no PO 6 / PI 6.

SpaceX.tsproj also contains the EtherCAT boxes C1001 and T1301
(MOVI-C Decentralized Electronics). Confirm which machine function each one
drives before mapping or using its process data.

---

# Position feedback

## VTD

The VTD uses a SICK DL50-P2228 laser distance sensor (SSI output). The DL50
is connected directly to the VTD inverter (MOVIPRO). The drive closes the
position loop with MOVIKIT Positioning Drive.

The PLC receives the actual position from the drive in PI 7 (high word) and
PI 8 (low word): a signed 32-bit integer in MOVISUITE user units. It is a
numeric value, not an IEEE-754 bit pattern.

The PLC does not read the DL50 directly and does not close a position loop
for the VTD. It sends commands, target positions, speeds and ramps through
PO 1..8.

Position is expected to ultimately be represented in engineering units,
normally millimeters. Convert only after the MOVISUITE user units have been
confirmed.

## Turntable

The turntable encoder is connected to a remote I/O module on EtherCAT and is
read by the PLC. The PLC must forward this position to the turntable drive
(MOVIKIT Positioning Drive); the drive controls the position.

Before implementing the turntable:

1. Confirm the remote module and channel. The SSI terminal
   "ENCODER (EPP5001-0002)" in SpaceX.tsproj is the expected candidate;
   verify it against the electrical drawings.
2. Confirm the encoder data format: bit length, Gray or binary code,
   single-turn/multi-turn resolution, counting direction and status bits.
3. Confirm in MOVISUITE which process-data words receive the external
   position, their word order, sign and user units.
4. Supervise validity (EtherCAT state, working counter and module status of
   the encoder module). Never forward a position that is not valid.

Never invent the encoder format or the process-data words that carry the
position to the drive.

## Buffer and roller conveyors

Buffer and roller conveyors are speed controlled (MOVIKIT Velocity Drive).
They have no position feedback; they use the pallet sensors only.

## General

Never assume an incremental motor encoder is available.

Do not implement a PLC-side position loop or encoder-based positioning for
any axis unless it is documented in this file or explicitly requested.

---

# Coding rules

Use Structured Text.

Prefer explicit and readable logic over compact expressions.

Preferred naming:

FB_     Function Blocks
FC_     Functions
ST_     Structures
E_      Enumerations
GVL_    Global variable lists

Inputs:
i_

Outputs:
q_

InOut:
io_

Local variables:
local descriptive names

Temporary variables:
temp descriptive names

Boolean variables should preferably describe their state, for example:

bDriveReady
bDriveFault
bPositionReached
bEnable
bReset

Avoid meaningless variable names.

Existing names:

The project contains legacy objects converted from the Siemens reference,
for example VTD_FB, Buffer_Conveyor_FB, Set_Bit_F, VTD_Control_DUT,
Control.VTD_Sys or Settings.LCnv_Sys. Keep their names, interfaces and field
names as they are. Do not rename legacy objects.

Apply the naming convention of this section to everything new: new POUs,
DUTs and GVLs, and new variables or structure fields added to legacy
objects.

Variable prefixes for new code:

b       BOOL
by      BYTE
w       WORD
dw      DWORD
i       INT
ui      UINT
di      DINT
udi     UDINT
r       REAL
lr      LREAL
s       STRING
t       TIME
e       ENUM
a       ARRAY
st      STRUCT
fb      function block instance
ton / tof / tp      timer instances
rtrig / ftrig       edge detection instances

Combine with the interface prefixes, for example i_bEnable, q_stStatus,
io_stStatus.

---

# State machines

For sequences and positioning use explicit state machines.

Prefer ENUM states rather than unexplained numeric constants.

Example:

TYPE E_AxisState :
(
    Idle,
    EnableDrive,
    WaitDriveReady,
    Moving,
    PositionReached,
    Fault
);
END_TYPE

State transitions must be clearly visible.

Avoid hidden state changes.

---

# Drive architecture

Prefer separating responsibilities.

Suggested architecture:

FB_SEW_Drive
    Handles communication and drive status

FB_Positioning
    Handles positioning logic

FB_Axis
    Coordinates drive and positioning

MAIN
    Coordinates machine operation

Do not put all drive logic directly inside MAIN.

Existing SEW communication layers:

FB_SEW_Drive
    MOVIKIT Positioning Drive, Standard 8 PD (VTD, turntable).

FB_SEW_VelocityDrive
    MOVIKIT Velocity Drive, 5 PD basic profile (buffer and roller conveyors).

Both blocks only pack commands into PO words, decode PI words and supervise
the communication (EtherCAT state, working counter, MOVIKIT handshake).
They never decide motion. The owner of the axis (for example VTD_FB or
Buffer_Conveyor_FB) calls the block and copies q_aProcessOutput and
q_stStatus into Control.<device>.Motor. FC Inputs fills
Control.<device>.Motor.stProcessInput and FC Outputs sends
Control.<device>.Motor.aProcessOutput.

During commissioning, FB_VTD_ManualControl (TEST ONLY, screen
VTD_ManualTest, HMI GVL_HMI_VTD.stManualCommand/stManualStatus/stManualSettings)
is the owner of the VTD axis. MAIN lets only one source write the VTD PO:
the raw write of FB_SEW_ProcessDataTest or FB_VTD_ManualControl.

Keep the drive enable while the motor is still turning, so that a normal
stop uses the PO 4 deceleration ramp. Removing the enable stops the drive
with the emergency stop ramp (FCB 14).

---

# I/O access architecture

Physical I/O is accessed in exactly two places:

FC Inputs
    The only place where PLC I/O inputs are read.

FC Outputs
    The only place where PLC I/O outputs are written.

Rules:

1. Inputs copies variables from the I/O GVLs (IO_*) to internal variables
   in GVL Control, inside the structure of the device they belong to.
   Example: Control.VTD_Sys[n].Motor.
   Outputs does the reverse: from Control to the IO_* GVLs.
2. Organize both FCs in one region per device or device group, using the
   same device order in Inputs and Outputs:

   {region "<Device> - <description>"}
   ...
   {endregion}

   Example: {region "VTD 1 - MOVIPRO process inputs (SEW Standard 8 PD)"}
3. Function blocks, logic functions and the HMI never access IO_* GVLs
   directly. They work only on the internal variables in Control
   (and the HMI only on its HMI GVL).
4. MAIN calls Inputs() first and Outputs() last in the cycle.
5. Do not create separate per-device FCs for reading or writing I/O; add a
   region to Inputs or Outputs instead.

---

# I/O mapping

Physical I/O mapping is safety critical.

Do NOT automatically change:

- EtherCAT topology
- EtherCAT addresses
- Process image offsets
- PDO mapping
- EL terminal configuration
- EL6633 configuration
- Profinet configuration
- SBusPLUS process data
- Device IDs
- hardware addresses

If an I/O change appears necessary:

1. Explain the required change.
2. Identify the affected variables.
3. Ask for human review before modifying hardware configuration.

---

# Byte conversion

Some external devices may expose process data as individual BYTE variables.

When reconstructing WORD, DWORD or REAL values:

Always verify:

- byte order
- endianness
- signed/unsigned representation
- IEEE-754 representation
- source device documentation

Do not assume byte order.

Example reconstruction may look like:

dwValue :=
    DWORD(b0)
    OR SHL(DWORD(b1), 8)
    OR SHL(DWORD(b2), 16)
    OR SHL(DWORD(b3), 24);

But this must only be used when the process-data byte order has been confirmed.

---

# REAL conversion

Do not perform a numeric conversion when the incoming DWORD represents an
IEEE-754 floating-point bit pattern.

A bit reinterpretation may be required instead.

Always distinguish between:

numeric conversion

and

bit reinterpretation.

---

# Safety

This is industrial automation software.

Safety-related code requires human verification.

Never silently modify:

- Emergency Stop logic
- STO
- PROFIsafe
- TwinSAFE
- safety I/O
- safety interlocks
- machine protection functions

If safety logic is encountered:

Analyze and explain it.

Do not modify it unless explicitly instructed.

Clearly identify any proposed safety-related change.

---

# Motion safety

Never bypass:

- limits
- interlocks
- end stops
- drive faults
- position validation
- emergency-stop conditions

Any bypass used for testing must be clearly labeled as TEST ONLY.

---

# PLC cycle

Avoid unnecessary blocking logic.

Do not generate:

- WHILE loops with uncontrolled execution time
- long blocking loops
- sleep/wait operations

PLC code must execute deterministically every cycle.

Use state machines and timers instead.

---

# Timers

Use TwinCAT IEC timers where appropriate:

TON
TOF
TP

Do not implement time delays using blocking loops.

---

# Edge detection

Use standard TwinCAT edge detection blocks where appropriate:

R_TRIG
F_TRIG

Do not recreate edge detection manually unless there is a specific reason.

---

# Error handling

Drive Function Blocks should expose diagnostic information.

Prefer outputs such as:

bReady
bBusy
bDone
bError
udiErrorId
eState

Do not clear errors automatically without understanding the fault source.

---

# Position control

Positioning logic must explicitly consider:

ActualPosition
TargetPosition
PositionTolerance

Typical condition:

ABS(ActualPosition - TargetPosition) <= PositionTolerance

Do not compare REAL/LREAL positions for exact equality.

---

# Units

Always document engineering units.

Examples:

Position_mm
Velocity_mm_s
Acceleration_mm_s2

Do not mix:

mm
m
encoder counts
drive internal units

without explicit conversion.

---

# Existing code

Before creating a new Function Block:

1. Search the project for similar functionality.
2. Reuse the project's existing architecture when possible.
3. Follow existing naming conventions.
4. Avoid creating duplicate functionality.

---

# Siemens legacy code

Some POUs were converted from the Siemens TIA reference and may still
contain Siemens-only code: SinaSpeed, SCALE_X/NORM_X, G120 hardware IDs,
global DBs such as "Screen_DB_1", quoted identifiers, %X bit access or
{REGION} blocks.

Rules:

1. Do not leave Siemens-only code active in a compiled POU.
2. Comment it out instead of deleting it. Prefix every commented line with

   // SIEMENS-LEGACY:

   so that all of it can be found and removed later with one search.
3. Put the TwinCAT replacement next to the commented code. Siemens drives
   (SinaSpeed/G120) are replaced by the SEW layers described in
   "Drive architecture".
4. Pure syntax may be converted directly, without keeping the original:

   {REGION Name} ... {END_REGION}  ->  {region "Name"} ... {endregion}
   Var.%X3                        ->  Var.3

5. Where no TwinCAT equivalent exists yet (for example HMI DBs), comment
   the code and add a TODO that names the missing interface. The dependent
   variable keeps its safe default (FALSE / 0).
6. Do not delete SIEMENS-LEGACY code until the user asks for that cleanup.
7. Reference_Project is the comparison baseline. Do not change it as part
   of a conversion.

---

# Editing scope

The agent may edit any file in this repository, including PLC sources,
project files, documentation, tools and this file.

The sections "I/O mapping", "Safety" and "Motion safety" still apply:
hardware configuration and safety logic are changed only on explicit
instruction, and every such change must be clearly reported.

When behavior, interfaces or open points change, update the related
documentation in docs/ in the same change.

---

# Editing TwinCAT XML files

TcPOU, TcGVL, TcDUT and project files contain XML generated by TwinCAT.

Modify them carefully.

Do not unnecessarily reformat entire XML files.

Keep diffs minimal.

Never regenerate a complete project file just to change a few lines of ST.

---

# Build validation

After changing PLC source code:

1. Review changed files.
2. Check ST syntax.
3. Check type compatibility.
4. Check variable declarations.
5. Check Function Block interfaces.
6. Report anything that cannot be validated without TwinCAT.

Do not claim that a TwinCAT project compiles unless an actual TwinCAT build
was successfully executed.

---

# Git

Before substantial modifications:

Check git status.

Prefer small, understandable changes.

Do not overwrite unrelated user modifications.

Never perform:

git reset --hard
git clean -fd
force push

unless explicitly requested.

---

# Agent behavior

When asked to implement something:

First inspect the relevant existing code.

Then briefly describe the proposed architecture.

Then modify the smallest necessary set of files.

Afterward report:

- files changed
- important logic added
- assumptions made
- anything requiring TwinCAT validation

For industrial-control logic, correctness and readability are more important
than minimizing the number of lines.

---

# Project language

Write all new project content in English, including code comments, identifiers,
documentation, and visualization labels and messages.
