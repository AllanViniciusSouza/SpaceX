# TwinSafeGroup1 Assembly Plan

## Status and scope

Updated on 2026-10-08 after authorized offline edits in TwinCAT XAE.
`TwinSafeGroup1.sal` and its diagram now contain two `safeEstop` blocks in
`Network1`, eleven physical input bindings and two internal results.
All five input pairs use NC evaluation and **500 ms discrepancy time**, as
specified by the user. Reset remains one input. This is an incomplete offline
draft, not a validated or commissioned safety application.

Saving and Verify Safety Project reported two errors: `Emergency_And_Overtravel_OK`
and `Curtain_Carousel_OK` are never used. No physical output was connected to
remove these errors. XAE also reported that the target's saved AMS Net ID does
not match the referenced I/O tree item; the process-image update was declined.
Resolve the target identity before generating hardware links. No download or
activation was performed.

### Implemented input stage

| Block / input pair | Alias input source | Discrepancy |
| --- | --- | --- |
| EStop_Panel_HMI / 1–2 | EL1918 FSIN Module 1.Input / 2.Input | 500 ms |
| EStop_Panel_HMI / 3–4 | EL1918 FSIN Module 3.Input / 4.Input | 500 ms |
| EStop_Panel_HMI / 5–6 | EP1918 FSIN Module 1.Channel 1.Input / Channel 2.Input | 500 ms |
| EStop_Panel_HMI / 7–8 | EP1918 FSIN Module 2.Channel 1.Input / Channel 2.Input | 500 ms |
| Curtain_Carousel / 1–2 | EP1957 FSIN Module 1.Channel 1.Input / Channel 2.Input | 500 ms |

`Safety_Reset_Request` comes from EL1918 FSIN Module 5.Input and feeds both
Restart ports. The first block currently combines emergencies and overtravel;
its instance name is retained from the editor. Its result is
`Emergency_And_Overtravel_OK`; the curtain result is `Curtain_Carousel_OK`.
This grouping does not establish the final stop-zone matrix.
Unused curtain pairs remain deactivated. EDM ports and delayed outputs are
unconnected. The default 100 ms Delay Time remains unused and is **not** an
approved stopping delay. `safeInputsAfterDiscError` remains false and requires
review of the intended discrepancy-fault recovery behavior.

The user confirmed that physical FSoE addresses have not yet been assigned.
Current aliases therefore cannot establish verified safety communication.

## Existing project findings

- `TargetSystemConfig.xml` selects EL6910, `F-PLC (EL6910)`, address 1.
  The `.splcproj` also contains a legacy `TargetSystem=EL6900` property;
  check the effective Target System page in XAE rather than changing XML.
- Six FSoE aliases resolve by ObjectId to matching modules in `SpaceX.tsproj`.
  Their Connection IDs are distinct (6–11). All have saved SafeAddress 0,
  watchdog 100 ms and ComErrAck unset. These are configuration observations,
  not approved response-time or acknowledgement settings.
- The VTD alias resolves to MOVIPRO **Module 2, FSoE Safety IO 48 bit**.
  Its 16-PD standard motion interface is a separate module.
- Saved `Mappings` contains the VTD FSoE input/output links. Equivalent
  generated links for the other five aliases were not found in that section;
  they use automatic linking, which still needs verification after the
  safety configuration is completed. This is not proof of a wrong ObjectId.
- `Run.In` is linked through `IO_OTHERS.Run`; `ErrorAcknowledgement.In`
  through `IO_OTHERS.ErrorAcknowledgement`. No ST assignments to these
  qualified variables were found. Their declaration does not generate
  a Run command or acknowledgement pulse.
- MapState/MapDiag are disabled on all six safety aliases. Group diagnostic
  outputs are unassigned. Include diagnostic mapping in the integration design.

`Alias_Devices.csv` contains exact saved addresses, IDs and physical module
paths. `Alias_Process_Data.csv` lists telegram entries including protocol
data. Use only the appropriate safety application channels in FB logic;
CMD, CRC, connection ID and padding entries are not sensor signals.

## Proposed address worksheet — NOT applied

| Device | Saved address | Proposed reservation | Confirmation |
| --- | --- | --- | --- |
| EL6910 logic | 1 | 1 | Read actual device address |
| EL1918 local safety inputs | 0 | 2 | Confirm DIP switches and drawing |
| EP1918-0002 overtravel inputs | 0 | 3 | Confirm physical device setting |
| EP1957-0022 curtain I/O | 0 | 4 | Confirm physical device setting |
| Euchner MBM-EC-S1-MLI-3B | 0 | 5 | Confirm device configuration |
| EL2912 local safety outputs | 0 | 6 | Confirm DIP switches and drawing |
| SEW VTD safety option | 0 | 7 | Confirm MOVISUITE safety configuration |

These are reservations for review, not values to download automatically.
Check uniqueness and compatibility across the actual safety installation,
including other controllers, before adoption. Connection ID and SafeAddress
are different properties and do not need identical numbers. Keep a record
of configured address, physically read address and verified device identity.
Do not copy SDSIDs into the address fields.

## Inputs established from the electrical drawing

Source: `INBOUND VTD ELECTRICAL DRAWING_9_17_26.pdf`, revision D. PDF page
numbers below are 1-based and differ from the printed sheet numbers.
Pages 99, 101, 126, 128, 129 and 164 were visually inspected.

| Device/channel | Drawing signal | Proposed safety variable | Evidence |
| --- | --- | --- | --- |
| EL1918 input 1 | 29ES1 door E-stop contact 1 | EStop_Panel_CH1 | Sheet 29.0 / PDF 99 |
| EL1918 input 2 | 29ES1 door E-stop contact 2 | EStop_Panel_CH2 | Sheet 29.0 / PDF 99 |
| EL1918 input 3 | 29ES2 HMI E-stop contact 1 | EStop_HMI_CH1 | Sheet 29.0 / PDF 99 |
| EL1918 input 4 | 29ES2 HMI E-stop contact 2 | EStop_HMI_CH2 | Sheet 29.0 / PDF 99 |
| EL1918 input 5 | 29PB1 door reset, NO | Safety_Reset_Request | Sheet 29.0 / PDF 99 |
| EL1918 input 6 | 26CR7 PLC bypass relay contact | Bypass_Request_1 | Sheet 29.0 / PDF 99 |
| EL1918 input 7 | 29SPB1 enabling switch contact arrangement | HMI_EnableSwitch | Sheet 29.0 / PDF 99 |
| EL1918 input 8 | 26CR8 PLC bypass relay contact | Bypass_Request_2 | Sheet 29.0 / PDF 99 |
| EP1918 connector In1/2 | 43SC1 upper overtravel, NC | Overtravel_Upper_* | Sheet 43.1 / PDF 126 |
| EP1918 connector In3/4 | 43SC2 lower overtravel, NC | Overtravel_Lower_* | Sheet 43.1 / PDF 126 |
| EP1957 connector In1/2 | 43LC1 receiver OSSD1/OSSD2, pins 2/4 | Curtain_Carousel_OSSD* | Sheets 43.3–43.4 / PDF 128–129 |
| EP1957 connector In3/4 | 43LC2 sender power, pins 1/3 | No safety input assigned | Sheet 43.4 / PDF 129 |

For EL1918, select `FSIN Module n.Input` in the alias. The adjacent
`Module Fault` signal is diagnostic, not the second contact of the device.
For EP1918/EP1957, channels are grouped differently in the alias: select
the documented `FSIN Module n.Channel m.Input` after pin-level verification.

The overtravel drawing identifies connectors but does not establish that
both inputs on each connector have independent wired NC contacts. The user
specified dual-channel evaluation for this draft; confirm sensor model and
pinout against the installed wiring before commissioning.
The enabling switch is shown as two contacts in series on one input; do
not describe this as two independent safety channels.

PLC-generated bypass relay contacts do not become independent safe mode
authorization merely by being read through a safety input. Their intended
purpose, operating mode restrictions and fault response remain unresolved.
No bypass or muting path is included in the proposed initial logic.

## Remaining architecture and assembly guidance

The sections below describe the intended final separation of functions.
The implemented draft above currently uses one network and combines the
emergency and overtravel pairs in one block. Output integration is pending.

Create and name networks in the TwinSAFE graphical editor. Start with
internal results and leave physical outputs unlinked until the complete
stop/restart design is reviewed. Do not edit safety CRCs manually.

### 01_EmergencyStops

Insert an ESTOP block named `EStop_Panel_HMI`.

| ESTOP port | Source |
| --- | --- |
| EStopIn1 | EL1918 FSIN Module 1.Input |
| EStopIn2 | EL1918 FSIN Module 2.Input |
| EStopIn3 | EL1918 FSIN Module 3.Input |
| EStopIn4 | EL1918 FSIN Module 4.Input |
| Restart | EL1918 FSIN Module 5.Input, 29PB1 |
| EStopOut | Internal `EmergencyStop_OK` result only at this stage |

Configure input pairs 1/2 and 3/4 for the verified NC contact arrangement
and dual-channel evaluation. Determine discrepancy times from device
characteristics and the safety response-time assessment; do not invent them.
Unused input ports must be explicitly configured as unused, not wired to TRUE
to hide a missing protection. Do not use a default delay as a validated stop time.

`Restart` rearms the ESTOP function after restored conditions and an operator
action. It is distinct from the group's `ErrAck`, which acknowledges faults.
Resetting safety must not itself start motion. Do not use constant TRUE or
an automatically repeating PLC pulse as the restart command.

### 02_Overtravel

Evaluate upper and lower limit devices independently using the verified
contact configuration. Use latched restart behavior where required by the
machine design. Do not pair the upper switch with the lower switch as if
they were redundant contacts of one device. Define a controlled recovery
procedure separately; do not automatically bypass a tripped end limit.

### 03_CarouselLightCurtain

Evaluate the receiver OSSD1/OSSD2 as a pair, with the appropriate TwinSAFE
protective-device function and restart interlock. Verify the EP1957 input
parameters for a powered OSSD device; dry-contact test-pulse settings cannot
be copied blindly. The sender connector has no OSSD outputs to evaluate.
No muting sequence is specified by the reviewed wiring.

### 04_GuardLock

The Euchner alias exposes generic 16 input and 16 output bits. Resolve these
against the **installed MGB2/MBM module configuration** before assigning
door-closed, guard-locked, emergency-stop or unlock functions. The bus-module
model alone does not establish a per-bit application map. Define unlock
conditions from validated safe standstill/hazard conditions, not ordinary
PLC speed feedback or a fixed arbitrary delay.

### 05_StopZonesAndDriveSafety

Keep separate reviewed demands for the two wired output areas:

| Output | Controlled relay/area |
| --- | --- |
| EL2912 FSOUT Module 1.Output | 30SCR1, STO #1, carousel conveyor sections 1–3 |
| EL2912 FSOUT Module 2.Output | 30SCR2, STO #2, VTD static/mobile extractor and buffer conveyors |

These are **two areas**, not automatically redundant STO channels of one
drive. Sheet 52.0 / PDF 164 shows each relay switching its area's supply
pair. The stop demand matrix must establish how each E-stop, guard, curtain
and limit affects both areas and adjacent machines.

The reviewed sheets do not show a complete relay EDM feedback path. They
also label the relay as 788-384 on sheet 30.0 and 857-304 on sheet 52.0;
confirm the installed part and feedback contacts. Do not synthesize EDM=TRUE
or disable required feedback merely to make verification pass.

SEW FSoE currently exposes only `Output_01..48` and `Input_01..48`. Obtain
the active MOVISAFE option, approved safe telegram assignment, polarity,
parameter CRC, acknowledgement behavior and stop/brake strategy from SEW.
Do not assume Output_01 is STO. For this vertical axis, torque removal alone
does not establish load holding or a validated safe stop; stopping and brake
coordination must be resolved before enabling the output stage.

### 06_GroupDiagnostics

Retain the existing RunStop and ErrAck links. Plan separate diagnostics for
ComErr, FbErr, OutErr, OtherErr and InRun, plus per-device state/diagnostics
where needed. A standard PLC request is not a safe permission. Group Run
must not replace the ESTOP restart sequence or be used to bypass a trip.
Review module-error and communication-error acknowledgement paths explicitly.

## Completion checks

Before output links or a download: verify device identity/address, input
pinouts and polarity, discrepancy and watchdog timing, the stop-zone matrix,
SEW/Euchner telegram definitions, relay feedback and the VTD brake strategy.
Calculate the complete safety response time; the current 100 ms watchdog
is not a validated stop-time budget.

Then use XAE's Verify Safety Project and Verify Complete Safety Project,
resolve the reported issues, and perform documented channel and functional
tests. Tests must include each E-stop/contact, held reset, interrupted
communication, power restoration, each guard/curtain/limit, feedback faults
and prevention of unintended restart. No build, online identity check or
functional safety validation has been performed. Offline XAE verification
was invoked after the input-stage edit and remains unsuccessful as described
in the status section.

The Siemens Main_Safety_RTG1 reference is architectural context only. It
includes five remote panels and a Safety_OK aggregation of only panels 1–3;
it is not the wiring specification for this installation.

## Manufacturer references

- [Beckhoff EL6910 operating instructions](https://download.beckhoff.com/download/document/automation/twinsafe/el6910_en.pdf): target, alias configuration and group interfaces.
- [Beckhoff TwinSAFE Logic FB documentation](https://download.beckhoff.com/download/document/automation/twinsafe/twinsafe-logic-fb_en.pdf), ESTOP section: paired inputs, restart and feedback behavior.
- [Beckhoff EL1918 operating instructions](https://download.beckhoff.com/download/document/automation/twinsafe/el1918_en.pdf): input parameter interpretation.

These references support configuration concepts; they do not certify this
machine's proposed application.
