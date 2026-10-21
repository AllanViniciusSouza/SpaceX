# TIA Portal V20 to TwinCAT 3 Migration

## Reference snapshot and scope

The initial inventory contains 20 SCL exports with 116 distinct top-level
objects: 47 types, 33 DBs, 20 functions and 16 function blocks. Repeated
objects have identical source text. `TIA_Reference_Inventory.csv` records
their source files and SHA-256 hashes. Run `tools/inventory_tia_exports.py`
again after adding exports. This inventory is not proof that all project
dependencies have been exported.

`MAIN.pdf` contains 41 pages of LAD for the reference CPU 1518HF-4 PN.
`Remote_Panel.pdf` contains 44 pages, including STEP 7 Safety logic,
emergency stops, overtravel, chain slack, muting and bypass interfaces.
`Main_Safety_RTG1.pdf` has been re-exported and now contains 27 readable pages.
The follow-up analysis and missing-block status are in `TIA_Missing_Blocks.md`.
PDF text was used to identify calls, not to reconstruct LAD wiring.

The target is the existing `Sys1_Inbound` PLC project. It already contains
related DUTs, GVLs and partial POU conversions. Reference sources remain
unchanged. No additional PLC instance, hardware links or task calls were added.

## Implemented first batch

| Reference | TwinCAT object | Adaptation |
| --- | --- | --- |
| Set_Bit_F | Existing Set_Bit_F | Preserve BIT_Number/Variavel callers; add Bit_Value default TRUE; reject bit indices above 15; define BOOL success result |
| ID_Decode_F | Existing ID_Decode_F | Explicit DINT-to-INT conversion; validate decimal XXYYZZ range; define BOOL success result |
| Stack_Lights_FB | Existing Stack_Lights_FB | Explicit flash input replaces Siemens clock tag; keep Orange and add Yellow alias |
| FindStringField | New FindStringField | Tc2_Standard string operations; bounded scans; whitespace handling; remove source's 10/20-character search windows |
| Barcode_Station_FB | New Barcode_Station_FB | Reuse Barcode_Station_DUT; TON/R_TRIG; E_BarcodeState; explicit reset and request outputs |

`Barcode_Station_DUT` strings are explicitly sized to 254 characters to
match the source's default Siemens STRING capacity. This changes its memory
layout. Regenerate and verify any HMI/ADS consumers before integration.
All new project comments are English. Existing names are retained where
changing them would break callers.

## Intentional behavior changes

- Set_Bit_F returns FALSE for bit indices outside 0..15 without modifying
  the word. Bit_Value=FALSE remains a no-op, as in the exported source;
  it does not clear the bit.
- ID_Decode_F accepts 0..999999. Invalid input clears all three fields and
  returns FALSE. Callers should consume the result when accepting external IDs.
- Stack lights use fault priority. An unconnected flash input defaults to
  TRUE, producing steady red during a fault. Supply a 0.5 Hz square wave
  for flashing. No PLC clock generator or output mapping was added.
- Barcode reads snapshot the existing gate number on Start to avoid
  accepting the preceding result. A new nonempty gate number and nonempty
  Code are required for Valid. Missing fields cannot reuse an old barcode.
- Auto_Stop_Lector is a one-cycle request; it is not a device acknowledgement.
  Done means the local read attempt completed. The scanner transport must
  consume the stop request. Counter wraps explicitly at 65535.
- Reset aborts the read, clears Done/Valid and requests stop if active.
  The TON is invoked once per cyclic FB call and reset outside Reading.
- FindStringField supports plain quoted fields in a complete flat SICK
  payload up to 254 characters. It rejects escaped/control characters in
  values. It is not a full JSON validator and must not replace a general
  MQTT parser. Validate with real scanner payloads before deployment.

## Migration boundaries and next dependencies

| Area | Required work before integration |
| --- | --- |
| VTD / conveyors | Buffer conveyors converted to MOVIKIT Velocity (FB_SEW_VelocityDrive) and the VTD drive region to MOVIKIT Positioning (FB_SEW_Drive); the VTD state machine, the extractor conveyor (EConveyor_FB draft) and the I/O regions remain |
| Position feedback | Reconcile source encoder assumptions with the actual DL50/SEW process data; establish units and validity |
| Orders / transfer / OPC | Reconcile Control_DB, Settings_DB, System_DB and screen structures with the existing GVLs and array bounds |
| HMI | Adapt Conveyor_HMI_FB, VTD_HMI_FB and Screens without transferring reference machine addresses or settings blindly |
| MQTT | Replace Siemens LMQTT/LStream dependencies with an agreed Beckhoff implementation and verify payload contracts |
| Safety / access modes | Review the safety design separately; do not translate ESTOP1, muting, bypass or gate-release logic into ordinary PLC ST |
| MAIN | Reconstruct call order and instance wiring after interfaces are validated; the target MAIN remains unchanged |

The reference MAIN additionally calls INPUTS, Auto_Test/Auto_Test_1,
Bypass_FC, Local_Mode_FC, SICK_AFx60 and LMQTT_Client. Their implementation
and required tag definitions must be checked against subsequent exports.
The source ModeManager_FB stores edge memory in VAR_TEMP and includes gate
release/bypass behavior; do not copy it mechanically.

## Validation status

The first batch passed XML parsing, project-reference checks, symbol checks
and source-level interface review. `FC_TestTIAFoundation` provides runnable
utility checks in ST; it has not been executed on a TwinCAT runtime.
No TwinCAT build success is claimed.

Build blocker status (updated 2026-10-15): the charger line in Inputs is
commented out until the byte order, the REAL representation and the
Charger_Level bounds (ARRAY[2..6] versus Charger_Level[1]) are confirmed;
DWORD_REAL has no active body. Buffer_Conveyor_FB and Light_Bars_FB no longer
contain active Siemens code (see the section below). No TwinCAT build success
is claimed.

## Conveyor drive conversion to MOVIKIT Velocity (2026-10-15)

Buffer and roller conveyors use SEW MOVIKIT Velocity Drive with the 5 PD
basic profile (SEW manual 33959862, chapters 4.2 and 9). The VTD and the
turntable use MOVIKIT Positioning Drive (see AGENTS.md).

| Object | Change |
| --- | --- |
| FB_SEW_VelocityDrive (new) | Communication layer: MOVIKIT handshake PO 1.15/PI 1.15, EtherCAT supervision, PO 1..5 / PI 1..5 |
| ST_SEW_ProcessInput5, ST_SEW_VelocityStatus (new) | Raw PI image and decoded status |
| Cnv_Motor_DUT | New fields stProcessInput, aProcessOutput, stStatus |
| Buffer_Cnv_Settings_DUT | New fields rSewSpeedPerUnit, uiSewAcceleration, uiSewDeceleration (0 = not configured, no motion) |
| Cnv_Errors_DUT | Error words UINT -> WORD, required by the VAR_IN_OUT WORD of Set_Bit_F |
| Buffer_Conveyor_FB | VFD region uses FB_SEW_VelocityDrive; the SinaSpeed/SCALE_X/NORM_X region and the HMI reset from Siemens screen DBs are commented as SIEMENS-LEGACY; {REGION} syntax converted; Transfer_Complete := FALSE; NOT Cnv_Control.Error; Errors.Errors_Profinet_3 qualified |
| Light_Bars_FB | "SinaSpeed_VTD_DB_1".EnableAxis replaced by the new input i_bDriveEnabled; original lines kept as SIEMENS-LEGACY |

Behavior kept from the legacy code: the state machine still commands
Motor.Forward/Reverse/Speed, and Forward produces a negative speed setpoint
(verify on the first test; correct the direction in MOVISUITE if needed).
The drive enable is kept until the motor stops, so a normal stop uses the
PO 4 ramp; Safety_OK or a conveyor error removes it (FCB 14 emergency stop
ramp). A move requested with unconfigured SEW scaling sets Motor.Error.

Open points:

- No buffer or roller conveyor drive exists yet in SpaceX.tsproj. When the
  drives are added, add one region per conveyor in Inputs/Outputs
  (Control.LCnv_Sys[n].Cnv_Level[l].Cnv1/Cnv2.Motor). Hardware links remain a
  human task.
- C1001/T1301 use an 8 PD ESI module; a MOVIKIT Velocity drive uses only
  PD 1..5. Confirm the module selection against the MOVISUITE configuration.
- Actual_Current is not part of the 5 PD profile and is not written.
- Time_SlowDown_Ramp is never assigned (the Siemens source used the global
  tags Time_1_Start_Buffers and similar), so the slow-down stages are skipped.
- HMI_Reset stays FALSE until a conveyor HMI GVL exists.
- Array indices taken from the decoded ID (VTD, Level) are not range-checked
  before use.
- The VFD_* fields of Buffer_Cnv_Inputs_DUT (G120 telegram) are no longer used.

Before calling the barcode FB cyclically, verify: a fresh valid result,
missing Code after a previous success, unchanged gate number for 15 seconds,
start during a read, reset during a read, a 100-character barcode, and
delivery of the one-cycle stop request. Timeout must complete with
Done=TRUE, Valid=FALSE and an empty Barcode. Perform these checks in an
isolated PLC test configuration before connecting hardware.

Timer reference: [Beckhoff TON](https://infosys.beckhoff.com/content/1033/tcplclib_tc2_standard/74406539.html).
