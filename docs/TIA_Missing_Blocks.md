# Missing TIA Routines: TwinCAT Migration Status

## Scope and placement

The corrected `Reference_Project/Main_Safety_RTG1.pdf` contains 27 pages.
The SCL inventory contains 36 distinct functions/function blocks. Eight
already had target objects before this batch; 28 were missing.

This batch adds six reference functions to the PLC compilation list, plus
two internal helpers and one test function. The remaining 22 reference
routines have complete declaration/body **review drafts**, not empty stubs,
under `Sys1_Inbound/MigrationReview`. They are registered as MSBuild `None`
items, **not `Compile` items**. They are file assets, not operational PLC
blocks. Open the files as text for review; do not mass-import them as code.

`TIA_POU_Migration_Status.csv` accounts for every reference routine, its
target, source file and source SHA-256. Existing target POUs were preserved;
their presence does not imply that their migration is complete.

## PLC functions added

| Function | Contract |
| --- | --- |
| RemovePlusSign | Remove one leading `+`; preserve the rest of the string |
| FindBoolField | Read an exact `true`/`false` scalar; expose `Valid` |
| FindIntField | Read an INT with checked range and `Valid` |
| FindINTFieldFragmented | Search complete fields in either overlapping window; checked INT range |
| FindDINTFieldFragmented | Search complete fields in either window; checked DINT range |
| ByteArrayToString | Six bounded ASCII windows at offsets 0, 100, 200, 300, 400 and 500; expose `Truncated` |

`FC_TIAScalarToken` and `FC_TIAParseDINT` support these functions.
All strings have explicit capacities. The parsers support restricted flat
ASCII payload fields, not general JSON. A scalar needs a trailing comma or
closing brace. Missing, malformed, out-of-range and incomplete numeric fields
return the source sentinel `-9999`, with `Valid=FALSE`. A legitimate `-9999`
returns `Valid=TRUE`; consumers must check validity before unsigned casts.
Leading zeroes, decimal fractions, exponents and leading plus signs are rejected.
The boolean parser no longer searches subsequent fields for the word `true`.

The fragmented helpers deliberately reject a field split across both inputs
without a complete copy. The source transport produces overlapping windows;
blind concatenation can duplicate bytes. Arbitrary transport fragmentation
requires a separate message reassembly layer. Verify real payloads before
connecting the staged MQTT parser.

`ByteArrayToString` retains the named input `Lenght` and six overlapping
outputs. It skips zero bytes and removes adjacent CR/LF pairs within each
window. It reports invalid input length, discarded payload beyond byte 763,
or any window exceeding 254 output characters. This is an ASCII compatibility
adapter, not a UTF-8 decoder. Unlike the source, it does not silently overflow
or use unbounded replacement loops. CR/NUL/LF is not treated as an adjacent
CR/LF pair.

## Review drafts and blockers

The staging tool removes S7 attributes, local `#` prefixes, regions and
metadata, normalizes quoted identifiers, and replaces timer type names.
It preserves the complete executable body for review. Original comments
remain in the reference SCL; generated commentary is English. This is lexical
preparation only: named arguments, timer calls, CHAR/STRING capacities, global
symbols, array bounds, DUT layouts and platform calls still require review.

| Drafts | Required reconciliation |
| --- | --- |
| EConveyor_FB | SinaSpeed, G120 hardware identifiers, NORM_X/SCALE_X, confirmed SEW data and units |
| Conveyor_HMI_FB, VTD_HMI_FB, Screens | Screen DBs, panel tags and five-system selection versus target arrays `[1..2]`; `Feed_VTD_HMI_FC` implementation is absent |
| Feed_Steptable_FC, CNV_Order_FC, VTD_Order_FC | Global OrderNo/time, CHAR-to-BYTE conventions, location encoding, existing OrderTable_DUT |
| Auto_Test, Auto_Test_1, FC_Orders, FC_Orders_2, OT_Charge_Commands, OT_Charge_Commands_1 | Test order generation, global HMI symbols, table bounds and explicit enable policy |
| Order_Table_FB, OPC_Control_FB | Control_DB/Settings_DB/System_DB/screen structures, DTL, watchdog settings, order handshakes |
| MQTT_Handler_FB, ParseShuttle_Status | LMQTT/LStream transport, missing status DUT, field validity, signed/unsigned conversion and complete message boundaries |
| Errors_Warings | Actual hardware diagnostics, Profinet status references, MQTT diagnostics and destination alarm words |
| GateAccessControl_FB, GateAccess_Station_FB, ModeManager_FB, Safety_Stops_FB | Separate safety and machine-protection review; no executable integration |

`tools/stage_tia_pous.py` can refresh the status inventory. It never replaces
an existing POU or promotes a draft to compilation. Existing drafts are not
overwritten; compare their recorded source hashes after a new export.
Do not copy source settings, addresses or five-system defaults into this
two-system target without checking the actual installation.

## Corrected safety PDF findings

The document identifies `Main_Safety_RTG1 [FB123]`, STEP 7 Safety V20 Update 2.
Text extraction identified the networks; page 26 was also rendered and
visually checked. No safety wiring was reconstructed from flattened text.

| Networks / pages | Observed purpose |
| --- | --- |
| 1 / 1–2 | Main_Panel FB16, cabinet emergency stop and gate/lock feedback aggregation |
| 2–3 / 2–3 | HMI_SAFETY_FC FC43, two HMI emergency-stop/commissioning interfaces |
| 4–8 / 3–17 | Five Remote_Panel FB17 instances; overtravel, chain slack, guards, STO, stopper power and hoist brake interfaces |
| 9 / 18–21 | Level-panel emergency-stop aggregation |
| 10 / 22–25 | F_Lock_FB FB24 instances and lock reset/feedback interfaces |
| 11 / 26 | Safety_OK is an AND of Remote_Panel_DB_1, _2 and _3 only |
| 12–14 / 26–27 | Bypass-assignment calls, global acknowledgement and HMI reset |

The absence of panels 4 and 5 from network 11 needs a design explanation;
it is not evidence that they should be silently added to the expression.
Main_Panel, HMI_SAFETY_FC, F_Lock_FB and the bypass-assignment implementations
are not supplied as SCL in this export set. Remote_Panel is available as a
PDF, not an editable safety implementation. These dependencies cannot be
recreated as certified safety functions by converting this calling diagram.

The SCL gate-access reference separately contains disabled fault-latching
assignments and `GateFault := GateFault_Latch := FALSE`. ModeManager_FB uses
temporary edge memory and contains bypass/gate-release behavior. These are
review findings, not approved behavior for the target machine. The four
related drafts are isolated in `MigrationReview/SafetyReview` and retain
the source behavior for inspection; no safety fixes were silently applied.

`Main_Safety_RTG1` was therefore not created as an ordinary ST FB.
Repository `AGENTS.md`, section Safety, requires analysis and human
verification of safety-related changes. Design and validate the actual
TwinSAFE implementation separately, using the installed safety hardware.

## Validation and integration

XML, project item references, duplicate symbols, reference coverage and
non-compilation of review files are checked by `tools/validate_tia_migration.py`.
`FC_TestTIAParsing` contains 20 assertions covering valid/invalid fields,
signed limits, truncation, overlapping windows and byte conversion. Its DWORD
result is zero when all checks pass; bits 0–19 identify failed assertions.
It is not connected to a task and has not been executed in TwinCAT.

No TwinCAT build or runtime success is claimed. The incomplete charger
handling in Inputs still prevents claiming project readiness.
Buffer_Conveyor_FB was converted to MOVIKIT Velocity on 2026-10-15
(see TIA_Migration.md).
No MAIN calls, I/O mapping, drive PDOs, hardware configuration or safety
project files were changed in this batch. Promote a draft only after its
dependencies are reconciled and it builds and passes isolated tests.

String indexing follows the [Beckhoff STRING documentation](https://infosys.beckhoff.com/content/1033/tc3_plc_intro/2529410443.html).
