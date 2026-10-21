# 04 - I/O and HMI Architecture

---

# Data flow

```
Hardware (EtherCAT, PROFINET, ...)
   │  linked in TwinCAT XAE
   ▼
GVLs/IO/IO_<Group>          raw signals, AT %I* / AT %Q*
   │  Inputs()              the only reader of physical inputs
   ▼
GVL Control                 internal state, one structure per device
   │      ▲
   ▼      │  FBs: communication layers and owner FBs
GVL Control
   │  Outputs()             the only writer of physical outputs
   ▼
GVLs/IO/IO_<Group>  ->  hardware


GVL_HMI_<Area>  <-->  MAIN / HMI update FCs  <-->  FBs, Control
(the visualization reads and writes only GVL_HMI_<Area>)
```

Rules:

1. Physical I/O is accessed in exactly two places: FC Inputs and FC
   Outputs.
2. FBs, functions and the HMI never access IO_* GVLs.
3. The HMI never accesses Control, IO_* GVLs or FB instances. It uses only
   its GVL_HMI_<Area>.
4. MAIN calls Inputs() first and Outputs() last.

---

# I/O GVLs (IO_<Group>)

```
// Source: <electrical drawing>, sheets <n>.
// Local rack cards only. Remote module signals belong in a separate GVL.
// AT %I* / AT %Q* declarations require individual channel links in TwinCAT XAE.
{attribute 'qualified_only'}
VAR_GLOBAL
    // DI-01 (EL1809) - card 23.0-1, sheet 24.0.
    HANDHELD_HMI_CONNECTED AT %I* : BOOL; // DI-01 CH04 | Wire 24.04

    // VTD drive, Standard 8 PD. Drive -> PLC: PDO 16#1A02 / object 16#7002.
    // Read only by FC Inputs, into Control.VTD_Sys[1].Motor.stProcessInput.
    VTD_PI_01 AT %I* : UINT;              // PI 1, 16#7002:01 - Status word
    VTD_PI_02 AT %I* : UINT;              // PI 2, 16#7002:02 - Actual speed

    // EtherCAT diagnostics of the VTD box. Read only by FC Inputs.
    VTD_WcState AT %I* : BOOL;            // WcState (TRUE = data invalid)
    VTD_EcState AT %I* : UINT;            // InfoData.State (8 = OP)
END_VAR
```

Rules:

1. Only `AT %I*` / `AT %Q*` variables. No logic, no scaling, no decoding.
2. Data type exactly as the hardware delivers it (BOOL bit, UINT word).
3. One GVL per I/O group (local rack cards, remote modules, drives,
   fieldbus gateways).
4. One header comment per device or card: device, module or profile,
   direction, PDO / object index, drawing sheet, and who reads or writes it.
5. One comment per variable with the physical reference:
   - discrete I/O: `// <card> CH<nn> | Wire <wire no.> | <description>`;
   - process data: `// PI <n>, <object index> - <meaning>`.
6. Discrete I/O names follow the signal names of the electrical drawing.
   Process-data names: `<Device>_<PI|PO>_<nn>`.
7. Every fieldbus device also gets its diagnostic variables (working
   counter state, device state), read through Inputs.
8. Spare channels are declared as reserved and never used in logic.
9. Never change EtherCAT topology, PDO mapping, process-image offsets,
   links or device configuration without explicit instruction.

---

# FC Inputs and FC Outputs

```
// Input mapping: the only place where PLC IO inputs are read.
// Copies IO GVL variables to internal variables (GVL Control). One region per device.
// Called first in MAIN.
FUNCTION Inputs : BOOL
```

```
{region "VTD 1 - MOVIPRO process inputs (SEW Standard 8 PD)"}
Control.VTD_Sys[1].Motor.stProcessInput.aWord[1] := IO_VFDs.VTD_PI_01; // Status word
Control.VTD_Sys[1].Motor.stProcessInput.aWord[2] := IO_VFDs.VTD_PI_02; // Actual speed

Control.VTD_Sys[1].Motor.stProcessInput.bWcStateError := IO_VFDs.VTD_WcState;
Control.VTD_Sys[1].Motor.stProcessInput.uiEcState := IO_VFDs.VTD_EcState;
{endregion}

Inputs := TRUE;
```

Rules:

1. Inputs copies IO_* -> Control. Outputs copies Control -> IO_*.
2. Copy only. Decoding, scaling, edge detection and logic belong to the
   device FBs.
3. One region per device or device group:
   `{region "<Device> <n> - <description>"}`.
4. The same device order in Inputs and Outputs.
5. One assignment per line, with the signal meaning as comment.
6. An unfinished mapping stays commented out inside its region, with a
   TODO that lists what must be confirmed before enabling it.
7. Do not create per-device input or output FCs. Add a region instead.
8. Both functions return TRUE.

---

# GVL Control

1. `{attribute 'qualified_only'}`.
2. Internal state of all devices, one entry per device type, an array when
   there is more than one device: `Control.<Device>[n]`.
3. Address signals as `Control.<Device>[n].<Group>.<Signal>`
   (for example `Control.VTD_Sys[1].Motor.stProcessInput`).
4. The device structure groups its signals in sub-structures
   (motor / drive, sensors, outputs, status).
5. Process images are stored raw (`stProcessInput`, `aProcessOutput`).
   Decoded status comes from the FB outputs.
6. Parameters live in a settings GVL. Parameters that must survive a
   restart are `VAR_GLOBAL PERSISTENT`.

---

# HMI contract

The visualization uses only `GVL_HMI_<Area>`.

```
// HMI interface of the VTD. The visualization uses only these variables;
// it must not access IO GVLs or FB instances directly.
{attribute 'qualified_only'}
VAR_GLOBAL
    // Screen "VTD" - operation
    stStatus : ST_HMI_VtdStatus;     // PLC -> HMI, written by FC_VTD_HmiUpdateStatus
    stCommand : ST_HMI_VtdCommand;   // HMI -> PLC, read by VTD owner FB
END_VAR

VAR_GLOBAL PERSISTENT
    stSettings : ST_VTD_Settings;    // HMI <-> PLC, validated by the PLC
END_VAR
```

Structures per screen or device:

| Structure | Direction | Written by | Read by |
| --- | --- | --- | --- |
| Command | HMI -> PLC | Visualization (the PLC may reset toggles) | Owner FB or MAIN |
| Status | PLC -> HMI | One HMI update FC or MAIN, once per cycle | Visualization |
| Settings | HMI <-> PLC | Visualization, validated by the PLC | Owner FB (PERSISTENT) |
| Summary | PLC -> HMI | HMI update FC | Overview screens |

Rules:

1. GVL variable names: `stCommand`, `stStatus`, `stSettings`; with a
   screen prefix when a GVL serves several screens
   (`stManualCommand`, `stManualStatus`).
2. Comment every GVL variable with its direction and its writer:
   `// PLC -> HMI, written by MAIN`.
3. Status is written in exactly one place per cycle.
4. HMI update functions are named `FC_<Area>_[<Screen>]HmiUpdate<What>`
   (`FC_VTD_HmiUpdateStatus`, `FC_VTD_PdHmiUpdateStatus`), take the FB and
   the status structure as VAR_IN_OUT, and are read-only towards the FB.
5. List screens: an array of summary or status structures
   (`astConveyor[n]`), a selection index (`uiSelected`, with the meaning of
   each value documented) and the structure of the selected device
   (`stSelected`).

## Command semantics

| Button type | PLC handling |
| --- | --- |
| Tap (momentary) | Evaluate the rising edge with R_TRIG |
| Hold-to-run (jog) | Level. Accepted only after release (armed). Max continuous time. Both directions together = no motion |
| Toggle (enable) | A request only. The PLC resets the toggle when the request is refused or dropped. No automatic restart |
| Selection (mode) | The PLC writes back the active value, so the screen always shows the real state |
| Numeric entry (setting) | Validated in the PLC. Invalid or 0 = function blocked, `bSettingsValid` shown |

A lost HMI connection must not keep a motion running: hold-to-run commands
are limited by their max time.

## Status content

1. Availability flags per button (`bJogAvailable`, `bStartAvailable`) to
   enable or disable buttons.
2. Active flags for indicators (`bEnableActive`, `bJogTimeout`).
3. Display texts built in the PLC as STRING(n) (`sModeActiveName`).
4. Values with their unit in the name (`rPosition_mm`, `iTorque_pct`).
5. Error id and, when available, error text.

## Safety on the HMI

1. No safety function on the HMI (safe reset, bypass, muting, curtain
   override) without an explicit human decision.
2. A software stop button on the HMI is not an emergency stop. Its label
   and documentation say so.

## Visualization objects

1. Screens are named after their area (`Main`, `VTD`, `Alarms`);
   sub-screens `<Area>_<Purpose>` (`VTD_Settings`).
2. Frames and faceplates: `FP_<Name>`. Shared frames: `Header`, `NavBar`.
3. Before a generated or bulk change of .TcVIS files: Save All, close
   TwinCAT XAE, back up the VISUs folder.

---

# Device communication layers

One communication FB per device profile: `FB_<Vendor>_<Profile>`
(for example `FB_SEW_Drive` for 8 PD, `FB_SEW_VelocityDrive` for 5 PD).

```
FC Inputs ──> Control.<Device>[n].Motor.stProcessInput
                         │
                         ▼
Owner FB ──> FB_<Vendor>_<Profile>(i_stProcessInput, commands)
                         │
                         ├─ q_aProcessOutput ──> Control.<Device>[n].Motor.aProcessOutput ──> FC Outputs
                         └─ q_stStatus, q_bReady, q_bError, q_udiErrorId ──> owner FB, HMI
```

Rules:

1. Input: a raw process-image structure `ST_<Vendor>_ProcessInput<n>`
   (raw words plus working-counter and device state).
2. Outputs: raw process output words (`q_aProcessOutput`) and a decoded
   status structure (`q_stStatus`).
3. The block packs commands, decodes status and supervises communication
   (fieldbus state OP, working counter, application handshake with
   timeout) into `bCommunicationOk`.
4. While communication is not OK, enable and start are forced FALSE.
5. The block never decides motion. The owner FB does.
6. The owner FB calls the block and copies its outputs into
   `Control.<Device>[n]`.
7. Never set functions that bypass protection (brake release without
   enable, output stage inhibit, limit switch deactivation) unless the
   project documents them.
8. Use only process-data words and bits documented for the configured
   device profile.
