# 01 - Naming and Variables

Applies to new objects and to new variables or fields added to existing
objects. Existing and legacy names stay as they are.

---

# Object names

| Object | Pattern | Example |
| --- | --- | --- |
| FUNCTION_BLOCK | FB_<Area>_<Name> | FB_SEW_Drive, FB_VTD_ManualControl |
| FUNCTION | FC_<Area>_<Name> | FC_SEW_MovikitModeName |
| STRUCT | ST_<Area>_<Name> | ST_SEW_ProcessInput8, ST_HMI_VtdStatus |
| ENUM | E_<Area>_<Name> | E_SEW_MovikitMode |
| GVL | GVL_<Area> | GVL_HMI_VTD |
| GVL with physical I/O | IO_<Group> | IO_VFDs, IO_Cards |
| PROGRAM | MAIN | MAIN |

Rules:

1. `<Area>` is the folder area of the object (see 02_Folder_Organization.md):
   a vendor / device layer (SEW), a machine function (VTD, Conveyor, Gate),
   HMI or System.
2. `<Area>` is written in capitals when it is an acronym (SEW, VTD, HMI).
   Inside `<Name>`, acronyms are written as words in PascalCase
   (ST_HMI_VtdStatus, FC_VTD_PdHmiUpdateStatus).
3. `<Name>` is PascalCase English:
   - data types and FBs: a noun or role (ProcessInput8, ManualSettings,
     VelocityDrive, ManualControl);
   - functions that return a value: the value (MovikitModeName);
   - functions that act: the action (PdHmiUpdateStatus).
4. Fixed framework names, without prefix: MAIN, Inputs, Outputs, Control.
5. One PROGRAM per task (MAIN). Everything else is an FB or an FC.
6. Test functions: FC_Test<Subject>. Test-only FBs keep a normal name and
   are marked TEST ONLY in their header.

HMI structures:

| Purpose | Pattern | Example |
| --- | --- | --- |
| Commands of a device screen | ST_HMI_<Device>Command | ST_HMI_ConveyorCommand |
| Status of a device screen | ST_HMI_<Device>Status | ST_HMI_VtdStatus |
| Summary for overview screens | ST_HMI_<Device>Summary | ST_HMI_GateSummary |
| Special screen of an area | ST_<Area>_<Screen>Hmi<Command/Status> | ST_VTD_ManualHmiCommand |
| Editable settings | ST_<Area>_<Screen>Settings | ST_VTD_ManualSettings |

---

# Variable names

Format:

```
[interface prefix][type prefix]<Name>[_unit]
```

Examples: `i_bEnable`, `q_stStatus`, `io_stCommand`, `rPosition_mm`,
`iTorque_0p1pct`.

## Interface prefixes

| Declaration section | Prefix |
| --- | --- |
| VAR_INPUT | i_ |
| VAR_OUTPUT | q_ |
| VAR_IN_OUT | io_ |
| VAR, VAR_TEMP, VAR_GLOBAL, STRUCT fields | none |
| VAR CONSTANT | none (UPPER_SNAKE_CASE, see below) |

## Type prefixes

| Type | Prefix | Example |
| --- | --- | --- |
| BOOL | b | bReady |
| BYTE | by | byFaultCode |
| WORD | w | wControlWord |
| DWORD | dw | dwRawValue |
| INT | i | iSpeedSetpoint |
| UINT | ui | uiAcceleration |
| DINT | di | diTargetPosition |
| UDINT | udi | udiErrorId |
| REAL | r | rPosition_mm |
| LREAL | lr | lrPosition_mm |
| STRING(n) | s | sModeActiveName |
| TIME | t | tJogMaxTime |
| ENUM | e | eModeActive, eState |
| ARRAY | a | aProcessOutput |
| STRUCT | st | stStatus |
| FB instance | fb | fbDrive |
| TON / TOF / TP | ton / tof / tp | tonHandshake, tpFaultReset |
| R_TRIG / F_TRIG | rtrig / ftrig | rtrigStart |

Rules:

1. Arrays: `a`, optionally followed by the element prefix when it helps
   reading (`abLevelReached`, `astConveyor`).
2. Array bounds follow the real numbering of the device or document:
   process data PO 1..8 -> `ARRAY[1..8]`, devices 1..6 -> `ARRAY[1..6]`.
   Index 0 only when it has a documented meaning (for example 0 = none).
3. STRING always with explicit length: `STRING(40)`.
4. Do not invent new prefixes. For a type not listed here, follow the
   closest existing pattern in the project or ask.

## Name body

1. PascalCase English words. No meaningless names: no `x`, `tmp1`, `aux`,
   `flag`, `data`, `var1`.
2. Abbreviations only when established in the domain or in the device
   manual (PO, PI, PD, HMI, ID, STO, FCB).
3. Loop counters are named after what they count: `iDevice`, `iChannel`.
4. Intermediate value of one calculation: suffix `Temp` (`diSpeedTemp`).
5. Raw, unscaled device value: suffix `Raw` (`iActualSpeedRaw`,
   `diActualPositionRaw`).

## BOOL names

A BOOL name states the fact that is TRUE.

- Good: `bReady`, `bMotorTurning`, `bSettingsValid`, `bJogButtonsReleased`.
- Avoid negated names: no `bNotReady`, `bNoError`.
- When the source signal has inverted logic, name it after its TRUE meaning
  and document it: `bWcStateError : BOOL; // TRUE = data invalid`.

Suffix vocabulary for BOOL state. Use these words with exactly this meaning:

| Suffix | Meaning | Example |
| --- | --- | --- |
| Request | Wanted by the operator or caller, not granted yet | bEnableRequest |
| Active | Really applied or sent now | bEnableActive, bJogPositiveActive |
| Latched | Held until an explicit reset | bSoftwareStopLatched, bStartLatched |
| Allowed | Conditions permit the action | bModeChangeAllowed |
| Available | Command or button can be used now (HMI) | bRunAvailable |
| Blocked | At least one condition forbids the action | bEnableBlocked |
| Armed | Prepared, waiting for its trigger | bJogArmed |
| Valid | Data or settings checked and usable | bSettingsValid |
| Ok | Supervision passed | bCommunicationOk, bEtherCatOk |
| Error | Fault present | bHandshakeError |
| Timeout | Time limit exceeded | bJogTimeout |
| Reached | Target reached | bSpeedReached, bPositionReached |

HMI command fields use the button name: `bStart`, `bStop`, `bReset`,
`bJogForward`, `bModeManual`.

---

# Units

1. Every physical value carries its unit as a suffix:

   | Suffix | Unit |
   | --- | --- |
   | _mm | millimeter |
   | _mm_s | mm/s |
   | _mm_s2 | mm/s² |
   | _A | ampere |
   | _pct | percent |
   | _0p1pct | 0.1 % per bit (`p` = decimal point) |

2. TIME variables have no unit suffix.
3. Device-internal units that are not confirmed yet: suffix `Raw` or a
   comment `// user units`. Convert to engineering units only after the
   scaling is confirmed.
4. Never mix mm, m, encoder counts and drive units without an explicit,
   named conversion.

---

# Constants

1. Declare in `VAR CONSTANT`, name in UPPER_SNAKE_CASE, no type prefix,
   one comment per constant.

   ```
   VAR CONSTANT
       FAULT_RESET_PULSE : TIME := T#500MS;       // PO 1.8 high time
       DISABLE_STOP_TIMEOUT : TIME := T#5S;       // Max time to stop with ramp before enable is removed
       ERROR_ID_ETHERCAT : UDINT := 16#FFFF0001;  // Drive not in OP or working counter invalid
       ERROR_ID_HANDSHAKE : UDINT := 16#FFFF0002; // Application handshake timeout
   END_VAR
   ```

2. Error ids of a block: `ERROR_ID_<CAUSE>`.
3. No magic numbers in logic. Times, limits, error ids and masks are named
   constants or settings. A literal from a device document (bit number,
   state value) is allowed only with a comment that cites its meaning.

---

# Enumerations

```
// MOVIKIT operating modes (PO 6 setpoint / PI 6 actual).
// Source: SEW manual 33959862, chapter 8.1 "Operating modes".
{attribute 'qualified_only'}
TYPE E_SEW_MovikitMode :
(
    DefaultMode := 0,              // Enabling or disabling the axes
    JogSpeedControlled := 101,     // FCB 05
    Speed := 200,                  // FCB 05
    PositioningAbsolute := 400     // FCB 09
) UINT;
END_TYPE
```

1. Always `{attribute 'qualified_only'}`; always access as
   `E_SEW_MovikitMode.Speed`.
2. Values in PascalCase without prefix.
3. When the values map to an external protocol, give explicit values and an
   explicit base type (`) UINT;`) and comment each value with its source.
4. State enums: see 03_Code_Structure.md.

---

# Structures

1. Fields follow the variable rules, without interface prefix.
2. Group related fields with a blank line and a `// Group` comment.
3. Defaults must be safe. A setting of 0 means "not configured" and must
   block the function that uses it.

```
// Settings of the manual test screen (TEST ONLY). Kept PERSISTENT.
// 0 = not configured: no motion is accepted until all values are > 0.
TYPE ST_VTD_ManualSettings :
STRUCT
    iMaxSpeed : INT;             // Speed at 100 %, PO 2 user units (> 0)
    uiAcceleration : UINT;       // PO 3 user units (> 0)
    uiDeceleration : UINT;       // PO 4 user units (> 0)
    tJogMaxTime : TIME := T#30S; // Max continuous jog
END_STRUCT
END_TYPE
```

---

# Declaration comments

1. One declaration per line.
2. Inline `//` comment on every variable whose meaning, unit, value range,
   source mapping, direction or TRUE meaning is not obvious from its name.
3. Typical content: `// PO 2, signed, user units`,
   `// PI 1, 16#7002:01 - Status word`, `// PLC -> HMI, written by MAIN`,
   `// TRUE = data invalid`, `// 0 = between levels`.
4. Align the comments of one declaration block in the same column.

---

# Legacy objects

1. Keep the names, interfaces and field names of legacy objects (for
   example objects converted from another platform).
2. New fields and variables added to a legacy object follow these rules.
