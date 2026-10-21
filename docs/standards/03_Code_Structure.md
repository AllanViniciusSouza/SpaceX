# 03 - Code Structure

---

# Header comment

Every POU, DUT and GVL starts with a comment block before its declaration
keyword.

```
// <One line: what this object is.>
// Source: <document number "title">, chapter <n>.
//
// <Responsibility: what it does, and what it does NOT do.>
// <Owner and consumer: "Written by X, read by Y.">
//
// Behavior:
//  - <rule>
//  - <rule>
//
// Safety-related behavior:
//  - <what is forced off when communication or permission is lost>
//  - <what is never set>
FUNCTION_BLOCK FB_<Area>_<Name>
```

Rules:

1. Test-only objects start with `// TEST ONLY - ` and name what replaces
   them in production.
2. Cite the device document by number and chapter for every protocol
   detail.
3. State the responsibility boundary explicitly
   ("This block does NOT decide any motion").
4. Document timing effects ("Drive status is evaluated from the previous
   call, one PLC cycle").
5. Keep the header up to date when the behavior changes.

---

# Declaration layout

Section order:

```
VAR_INPUT
VAR_IN_OUT
VAR_OUTPUT
VAR
VAR CONSTANT
```

1. VAR_INPUT: data first (process image, settings), then commands, then
   parameters with defaults. Blank line between groups.
2. VAR_IN_OUT: HMI command structures that the block writes back (for
   example a toggle reset), and large structures passed by reference.
3. VAR_OUTPUT: data first (process output, status structure), then
   diagnostics (`q_bReady`, `q_bBusy`, `q_bDone`, `q_bError`,
   `q_udiErrorId`, `q_eState`).
4. VAR: inner FB instances, state variables grouped by function with a
   `// Group` comment, then edge instances, then timer instances.
5. VAR CONSTANT last.
6. Inputs that are parameters get a safe default:
   `i_tHandshakeTimeout : TIME := T#1S;`.

Example:

```
FUNCTION_BLOCK FB_SEW_VelocityDrive
VAR_INPUT
    i_stProcessInput : ST_SEW_ProcessInput5;  // Raw PI 1..5 + EtherCAT diagnostics (from FC Inputs)

    i_bEnable : BOOL;                         // PO 1.0 + PO 1.1 enable (FALSE = stop with FCB 14)
    i_bStart : BOOL;                          // PO 1.7 start/stop with fieldbus ramp
    i_bFaultReset : BOOL;                     // PO 1.8, drive resets on the rising edge

    i_tHandshakeTimeout : TIME := T#1S;       // Max time for PI 1.15 to follow PO 1.15
END_VAR
VAR_OUTPUT
    q_aProcessOutput : ARRAY[1..5] OF UINT;   // Raw PO 1..5 (to FC Outputs)
    q_stStatus : ST_SEW_VelocityStatus;       // Decoded PI 1..5

    q_bReady : BOOL;                          // Communication OK, ready, STO inactive, no error
    q_bError : BOOL;                          // Drive error or communication error
    q_udiErrorId : UDINT;                     // ERROR_ID_* or device fault code
END_VAR
VAR
    bHandshakeIn : BOOL;                      // Value sent in PO 1.15
    bHandshakeWaiting : BOOL;
    tonHandshake : TON;
    wControlWord : WORD;
END_VAR
VAR CONSTANT
    ERROR_ID_ETHERCAT : UDINT := 16#FFFF0001; // Drive not in OP or working counter invalid
    ERROR_ID_HANDSHAKE : UDINT := 16#FFFF0002; // Handshake timeout
END_VAR
```

---

# Implementation layout

Split the body into regions:

```
{region "<Name>"}
...
{endregion}
```

Region order follows the data flow of one cycle:

1. Edge detection of commands
2. Supervision and validation (communication, settings)
3. Mode and permissions
4. Function logic, one region per function
5. Inner FB calls
6. Diagnostics
7. Build outputs

Rules:

1. The region name says what the region does and cites the reference:
   `"Enable (PO 1.0 + PO 1.1)"`, `"JOG -/+ (modes 100/101) - hold-to-run"`,
   `"Decode process inputs (PI 1..5)"`.
2. Comments explain why (with document and chapter), not what the line
   does.

---

# Formatting

1. Indentation: 4 spaces, no tabs.
2. Keywords, TRUE and FALSE in capitals.
3. One statement per line. Blank line between logical steps.
4. Lines around 100 characters at most.
5. Long boolean expressions: one condition per line, operator at the start
   of the line, aligned under the first operand.
6. Parentheses around every AND group inside an OR, and around every
   comparison inside a boolean expression.
7. Give a condition a name when it is used more than once or has a meaning
   of its own. Prefer named intermediate BOOLs over long inline
   expressions.

```
bEnableBlocked := bSoftwareStopLatched
                  OR i_bInhibit
                  OR NOT fbDrive.q_stStatus.bCommunicationOk
                  OR fbDrive.q_stStatus.bError
                  OR NOT fbDrive.q_stStatus.bStoInactive;

bEnableRequest := io_stCommand.bEnable AND NOT bEnableBlocked;
```

---

# Latches and command priority

1. Reset and stop conditions are evaluated first; set conditions after,
   in ELSIF:

   ```
   IF NOT bRunAvailable OR rtrigStop.Q THEN
       bRunPositive := FALSE;
       bRunNegative := FALSE;
   ELSIF rtrigRunPositive.Q AND NOT bRunNegative THEN
       bRunPositive := TRUE;
   ELSIF rtrigRunNegative.Q AND NOT bRunPositive THEN
       bRunNegative := TRUE;
   END_IF
   ```

2. No automatic restart. After a stop, a fault or a lost permission, the
   operator must give the command again.
3. Opposite commands pressed together give no motion.
4. A held button must be released before it is accepted (armed logic), so
   a button held during enable or a mode change does not start motion.

---

# Timers and edge detection

1. Use TON, TOF, TP, R_TRIG and F_TRIG. Do not recreate them manually.
2. Declare the instance in VAR. Call it exactly once per cycle,
   unconditionally, never inside an IF or CASE branch.
3. Call the edge instances at the top of the body
   (region "Edge detection").
4. Preset times come from VAR CONSTANT or settings, never from literals in
   the logic.
5. Pulses to a device use TP: `tpFaultReset(IN := rtrigReset.Q, PT := FAULT_RESET_PULSE);`.

---

# Calls

1. FB calls with named parameters, one per line, indented 4 spaces:

   ```
   fbVtdManualControl(
       i_stProcessInput := Control.VTD_Sys[1].Motor.stProcessInput,
       i_bInhibit := fbVtdProcessDataTest.q_bTestWriteActive,
       i_stSettings := GVL_HMI_VTD.stManualSettings,
       io_stCommand := GVL_HMI_VTD.stManualCommand);
   ```

2. Read results from the instance outputs after the call
   (`fbDrive.q_bReady`).
3. Do not write instance inputs outside the call. Do not access internal
   variables of another FB.
4. Functions return a value. Inputs and Outputs return TRUE.

---

# State machines

Use an explicit state machine for every sequence and every positioning
task.

```
{attribute 'qualified_only'}
TYPE E_VTD_TransferState :
(
    Idle,
    WaitPermission,
    Moving,
    PositionReached,
    Fault
);
END_TYPE
```

```
VAR
    eState : E_VTD_TransferState;
    eStateLast : E_VTD_TransferState;
    tonStateTime : TON;
    udiErrorId : UDINT;
    // ... conditions (bStartAllowed, bPermissionOk, bFaultActive), edges, positions
END_VAR
VAR CONSTANT
    STATE_TIMEOUT : TIME := T#10S;                       // Max time in a waiting or moving state
    ERROR_ID_PERMISSION_TIMEOUT : UDINT := 16#FFFF0010;  // Permission not received in time
    ERROR_ID_MOVE_TIMEOUT : UDINT := 16#FFFF0011;        // Target not reached in time
    ERROR_ID_INVALID_STATE : UDINT := 16#FFFF00FF;       // Unknown state value
END_VAR
```

```
{region "State machine"}
// State timer restarts on every state change.
tonStateTime(IN := (eState = eStateLast), PT := STATE_TIMEOUT);
eStateLast := eState;

CASE eState OF
    E_VTD_TransferState.Idle:
        IF rtrigStart.Q AND bStartAllowed THEN
            eState := E_VTD_TransferState.WaitPermission;
        END_IF

    E_VTD_TransferState.WaitPermission:
        IF bPermissionOk THEN
            eState := E_VTD_TransferState.Moving;
        ELSIF tonStateTime.Q THEN
            udiErrorId := ERROR_ID_PERMISSION_TIMEOUT;
            eState := E_VTD_TransferState.Fault;
        END_IF

    E_VTD_TransferState.Moving:
        IF ABS(rActualPosition_mm - rTargetPosition_mm) <= rPositionTolerance_mm THEN
            eState := E_VTD_TransferState.PositionReached;
        ELSIF tonStateTime.Q THEN
            udiErrorId := ERROR_ID_MOVE_TIMEOUT;
            eState := E_VTD_TransferState.Fault;
        END_IF

    E_VTD_TransferState.PositionReached:
        eState := E_VTD_TransferState.Idle;

    E_VTD_TransferState.Fault:
        IF rtrigReset.Q AND NOT bFaultActive THEN
            udiErrorId := 0;
            eState := E_VTD_TransferState.Idle;
        END_IF

ELSE
    udiErrorId := ERROR_ID_INVALID_STATE;
    eState := E_VTD_TransferState.Fault;
END_CASE
{endregion}

{region "Outputs from state"}
bMoveCommand := (eState = E_VTD_TransferState.Moving);
q_bBusy := (eState <> E_VTD_TransferState.Idle) AND (eState <> E_VTD_TransferState.Fault);
q_bError := (eState = E_VTD_TransferState.Fault);
q_eState := eState;
{endregion}
```

Rules:

1. One state variable `eState` of an enum type. No numeric state
   constants.
2. All transitions are inside the CASE. No state change anywhere else.
3. One transition = one IF with a visible condition.
4. Outputs are derived from `eState` after the CASE, not set in scattered
   places.
5. Every state that waits for feedback is supervised by a timeout.
6. A fault state is reachable from any state. It is left only with a reset
   edge when the cause is gone.
7. The ELSE branch of the CASE goes to the fault state.
8. Expose `eState` as an output for HMI and diagnostics.
9. Never compare REAL or LREAL positions for equality. Use
   `ABS(actual - target) <= tolerance`.

---

# Diagnostics and errors

1. Blocks with a function to supervise expose: `q_bReady`, `q_bBusy`,
   `q_bDone`, `q_bError`, `q_udiErrorId` and `q_eState` where they apply.
2. Own error ids are constants `ERROR_ID_<CAUSE>`. Device fault codes are
   passed through unchanged, with their format documented
   (`// fault * 256 + subfault`).
3. Report one error id, by priority, in one IF/ELSIF chain:
   communication -> supervision (handshake, timeout) -> device fault -> 0.
4. Never clear an error automatically. Clear it only with a reset edge
   when the cause is gone.
5. `q_bReady` is TRUE only when communication is OK, the device is ready
   and no error is active.

---

# Responsibility layers

| Layer | Does | Never does |
| --- | --- | --- |
| Communication FB (FB_<Vendor>_<Profile>) | Packs commands into process outputs, decodes process inputs, supervises communication | Decide motion |
| Owner FB (machine function) | Decides motion, owns the axis or station, calls the communication FB | Access IO_* GVLs |
| HMI update FC | Copies FB status to the HMI status structure | Change FB inputs or outputs |
| MAIN | Calls Inputs, owners, HMI update, Outputs; arbitrates writers | Contain device logic |

---

# MAIN cycle

```
// 1. IO inputs -> internal variables
Inputs();

// 2. Logic on internal variables
fbVtd(...);
fbConveyor[1](...);

// 3. HMI status
FC_VTD_HmiUpdateStatus(...);

// 4. Internal variables -> IO outputs
Outputs();
```

1. Inputs() first, Outputs() last.
2. Exactly one writer per output and per process-data block. When two
   sources can write the same output (for example a test block and the
   production block), MAIN selects one explicitly and inhibits the other
   while it is active.
3. Each block is called once per cycle.

---

# Bits, words and conversions

1. Bit access with `.n`. Comment every bit with its documented meaning:

   ```
   wControlWord := 0;
   IF q_stStatus.bCommunicationOk AND i_bEnable THEN
       wControlWord.0 := TRUE;     // PO 1.0 Enable/emergency stop
       wControlWord.1 := TRUE;     // PO 1.1 Enable/application stop
   END_IF
   ```

2. Rebuild control words from 0 every cycle, then set the bits.
3. Use explicit conversion functions (`UINT_TO_INT`, `WORD_TO_BYTE`).
4. Comment whether a conversion keeps the bit pattern (same-size integer,
   signed value) or converts the number.
5. Never assume byte order, signedness or REAL representation. Confirm it
   in the device document first. A DWORD that carries an IEEE-754 pattern
   needs a bit reinterpretation, not a numeric conversion.

---

# Determinism

1. No WHILE or REPEAT loops with a data-dependent end. FOR loops only with
   constant bounds.
2. No waiting inside a cycle. Use state machines and timers.
3. Every block runs in bounded time every cycle.

---

# Comments, TODO and disabled code

1. TODO format: `// TODO: <what is missing> - <what it blocks or what must be confirmed>`.
2. Unfinished code stays commented out with the reason and the conditions
   to enable it. Dependent variables keep their safe default (FALSE / 0).
3. Code from another platform that is kept commented out uses one
   searchable prefix per origin, for example `// SIEMENS-LEGACY:`.
4. Do not delete commented legacy code until the user asks for that
   cleanup.
5. Mark TEST ONLY in the object header, at the instance declaration in
   MAIN, at the call site and in the HMI structures and GVL comments that
   belong to the test.
6. Any bypass for testing is labeled TEST ONLY and never removes a safety
   function, limit or interlock.
