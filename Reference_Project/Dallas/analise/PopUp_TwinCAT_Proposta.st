// ============================================================================
//  PROPOSAL ONLY - NOT APPLIED TO Sys1_Inbound
//  Carousel popup (lift + roller + optional chain) for TwinCAT 3
//
//  Source (TIA V20, Dallas_Production, read 19/10/2026 via tia-portal MCP):
//    FB PConveyor_1_FB (FB15), PConveyor_2_FB (FB20), PConveyor_3_FB (FB17),
//    PConveyor_4_FB (FB27), FC Conveyors_Transfer (FC24),
//    UDTs PopUp_Cnv_Control, PopUp_Cnv_Settings, PopUp_Cnv_Inputs,
//         PopUp_Cnv_Instruction, Cnv_Motor, Cnv_Errors.
//
//  Main changes against Dallas:
//    1. Siemens G120C + SinaSpeed (telegram 1, HW_IO, 1745 rpm, NORM_X/SCALE_X)
//       -> SEW MOVIKIT Velocity 5 PD through FB_SEW_VelocityDrive (existing),
//          wrapped in FB_Cnv_SewMotor (new) and called 3x (roller, chain, lift).
//    2. Four copy-paste FBs with hard-coded neighbours and sensors
//       -> one PopUp_Conveyor_FB; neighbours come from Cnv_Settings.Side_ID
//          and Cnv_Control.Side[] (filled by Conveyors_Transfer).
//    3. Global tags inside the FB ("Main_Safety_RTG1_DB".SAFETY_OK_CAROUSEL,
//       "LighGuard_Cut-Off Path 01", "PopUp Conveyor n - Pallet present x",
//       "Control_DB".PopUp_Cnv[n]) -> FB inputs / DUT fields.
//    4. UINT state numbers -> E_PopUpState (same values, SM_State unchanged for HMI).
//
//  Names follow the user's Control.TcGVL (Pop_Up_Cnv : ARRAY[1..2] OF PopUp_Control_DUT).
//  Existing DUTs reused unchanged: Cnv_Motor_DUT (already has the SEW fields),
//  Cnv_Errors_DUT (WORD). Existing FC reused: Set_Bit_F.
// ============================================================================


// ============================================================================
//  DUTs
// ============================================================================

// ---------------------------------------------------------------- DUTs/SEW/ST_SEW_VelocityScaling
// Scaling and ramps of one MOVIKIT Velocity drive (user units set in MOVISUITE).
// 0 = not configured: the motor does not move (same rule as Buffer_Cnv_Settings_DUT).
// Replaces Dallas Roller/Chain/Lift_G120_Hardware_ID : HW_IO and RefSpeed 1745.0.
TYPE ST_SEW_VelocityScaling :
STRUCT
    rSewSpeedPerUnit : REAL;    // PO 2 setpoint [user units] per 1 unit of Cnv_Motor_DUT.Speed (%)
    uiSewAcceleration : UINT;   // PO 3 [user units]
    uiSewDeceleration : UINT;   // PO 4 [user units]
END_STRUCT
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/E_PopUpState
// Same numbers as the Dallas CASE so SM_State on the HMI keeps its meaning.
{attribute 'qualified_only'}
{attribute 'strict'}
TYPE E_PopUpState :
(
    INIT := 0,          // Dallas 0   Initialization / idle
    STANDBY := 10,      // Dallas 10  Ready to receive an instruction
    INBOUND := 20,      // Dallas 20, 30  Receive a pallet (roller or chain)
    OUTBOUND := 50,     // Dallas 40, 50  Send a pallet, waits for the receiver to run
    LIFT_UP := 60,      // Dallas 60
    LIFT_DOWN := 70,    // Dallas 70
    ERROR := 400,       // Dallas 400
    MANUAL := 500       // Dallas 500 (Manual and Maintenance)
) UINT;
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/PopUp_Inputs_DUT
// Sensors of one popup. Written only by FC Inputs (AGENTS.md: I/O only in Inputs/Outputs).
// Dallas: PopUp_Cnv_Inputs ("Lift Up", "Lift Down") + global "PopUp Conveyor n - Pallet present x".
TYPE PopUp_Inputs_DUT :
STRUCT
    Lift_Up : BOOL;             // Lift at the top = roller transfer level
    Lift_Down : BOOL;           // Lift at the bottom = chain transfer level
    Pallet_Present : BOOL;      // Pallet on this popup (end of an inbound transfer)
END_STRUCT
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/PopUp_Instruction_DUT
// Same members as Dallas PopUp_Cnv_Instruction (WMS / order table / HMI write here).
TYPE PopUp_Instruction_DUT :
STRUCT
    Mode_Change : UINT;             // 0 Disabled, 1 Manual, 2 Semi-Auto, 3 Auto, 5 Maintenance
    Stop : BOOL;
    Enable : BOOL;
    Reset : BOOL;
    Execute : BOOL;                 // Rising edge starts the task (same as Start_Transfer)
    Task_ID : UINT;
    Task_Metadata : STRING;
    Transfer_To_ID : DINT;          // Outbound: ID (XXYYZZ) of the receiving device
    Transfer_From_ID : DINT;        // Inbound: ID (XXYYZZ) of the sending device
    Transfer_in_Progress : BOOL;    // Written by PopUp_Conveyor_FB
    Inbound_Ready : BOOL;           // Written by Conveyors_Transfer
    Transfer_Complete : BOOL;       // Only reset (as Dallas); Done is the completion flag
    Outbound_Ready : BOOL;          // Written by Conveyors_Transfer
    Start_Transfer : BOOL;
    Start_Transfer_Backward : BOOL; // Manual mode only
    Roller_Fwd : BOOL;              // Manual mode
    Roller_Bwd : BOOL;
    Chain_Fwd : BOOL;
    Chain_Bwd : BOOL;
    Lift_Up : BOOL;                 // Auto: move lift up (state 60). Manual: jog up
    Lift_Down : BOOL;
END_STRUCT
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/PopUp_Side_Status_DUT
// Device on one side of the popup. Filled every cycle by Conveyors_Transfer.
// Replaces the hard-coded "Control_DB".PopUp_Cnv[n] / ECnv / Outbound_Cnv reads of Dallas.
TYPE PopUp_Side_Status_DUT :
STRUCT
    In_Position : BOOL;     // Neighbour aligned with this popup (VTD/extractor at the level,
                            // turntable at the angle). TRUE for fixed conveyors.
    Inbound_Ready : BOOL;   // Neighbour can receive a pallet
    Running : BOOL;         // Neighbour transport motor turning (handshake before sending)
    Occupied : BOOL;        // Neighbour detects the pallet (end of an outbound transfer)
END_STRUCT
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/PopUp_Settings_DUT
// Dallas PopUp_Cnv_Settings + boost time (was an FB input) + neighbours + SEW scaling.
TYPE PopUp_Settings_DUT :
STRUCT
    ID : DINT;                      // XXYYZZ
    Has_Chain : BOOL;               // FALSE = roller + lift only (Dallas popup 1 and 4)

    // Neighbour ID on each side, 0 = no neighbour.
    //   1 = roller Forward end   (pallet leaves here when the roller runs Forward)
    //   2 = roller Reverse end
    //   3 = chain Forward end
    //   4 = chain Reverse end
    Side_ID : ARRAY[1..4] OF DINT;

    // Times [s] and speeds [% of the drive range], same units as Dallas.
    Roller_TC_Time : UINT;          // Not used by the Dallas code (kept)
    Roller_Transfer_Time : UINT;    // Transfer watchdog
    Roller_Slow_Speed : UINT;       // Not used by the Dallas code (kept)
    Roller_Full_Speed : UINT;
    Roller_Manual_Speed : UINT;
    Chain_TC_Time : UINT;
    Chain_Transfer_Time : UINT;
    Chain_Slow_Speed : UINT;
    Chain_Full_Speed : UINT;
    Chain_Manual_Speed : UINT;
    Lift_TC_Time : UINT;
    Lift_Transfer_Time : UINT;      // Lift travel watchdog
    Lift_Slow_Speed : UINT;
    Lift_Full_Speed : UINT;
    Lift_Manual_Speed : UINT;

    // Start boost per side [s], 0 = no boost (Dallas FB inputs TimeStartBoost_*; Dallas boosted
    // only popup-to-popup transfers, never to/from the VTD/extractor).
    Side_Boost_Time : ARRAY[1..4] OF UINT;
    Boost_Speed : UINT := 100;      // [%]

    // SEW MOVIKIT Velocity (replaces *_G120_Hardware_ID : HW_IO)
    Roller_Drive : ST_SEW_VelocityScaling;
    Chain_Drive : ST_SEW_VelocityScaling;
    Lift_Drive : ST_SEW_VelocityScaling;
END_STRUCT
END_TYPE


// ---------------------------------------------------------------- DUTs/Carousel/PopUp_Control_DUT
// Dallas PopUp_Cnv_Control. Type name already used in GVLs/Control.TcGVL.
TYPE PopUp_Control_DUT :
STRUCT
    Mode : UINT;
    Error : BOOL;
    Warning : UINT;
    Enabled : BOOL;
    Stopped : BOOL;
    Done : BOOL;
    Running : BOOL;
    Ready_For_Task : BOOL;
    Current_Task_Type : UINT;
    Current_Task_ID : UINT;
    Cnv_Occupied : BOOL;
    SM_State : UINT;                            // E_PopUpState value
    Active_Side : INT;                          // NEW: side of the running transfer, 0 = none
    Inputs : PopUp_Inputs_DUT;
    Side : ARRAY[1..4] OF PopUp_Side_Status_DUT;  // NEW: written by Conveyors_Transfer
    Roller_Motor : Cnv_Motor_DUT;               // existing DUT
    Chain_Motor : Cnv_Motor_DUT;
    Lift_Motor : Cnv_Motor_DUT;
    Instruction : PopUp_Instruction_DUT;
    Cnv_Errors : Cnv_Errors_DUT;                // existing DUT (WORD)
END_STRUCT
END_TYPE


// ============================================================================
//  POUs
// ============================================================================

// ---------------------------------------------------------------- POUs/SEW/FB_Cnv_SewMotor
// One conveyor motor on a SEW MOVIKIT Velocity drive (5 PD).
// Same logic as the region "VFD - SEW MOVIKIT Velocity Drive (5 PD)" of
// Buffer_Conveyor_FB, moved into a block so a popup can use it three times.
// The owner writes io_stMotor.Forward / Reverse / Speed; this block writes the
// status fields and io_stMotor.aProcessOutput. io_stMotor.stProcessInput is
// written by FC Inputs, io_stMotor.aProcessOutput is read by FC Outputs.
//
// Direction: Forward = positive setpoint. Dallas compensated the sign in code per drive
// (popup 2 chain: Forward = negative, popup 3 chain: Forward = positive; Buffer_Conveyor_FB:
// Forward = negative). Here every drive is Forward = positive: set the direction of
// rotation of each drive in MOVISUITE (AGENTS.md), not in the PLC.
FUNCTION_BLOCK FB_Cnv_SewMotor
VAR_INPUT
    i_stScaling : ST_SEW_VelocityScaling;
    i_bSafetyOk : BOOL;         // FALSE removes the enable at once (FCB 14 emergency ramp)
    i_bInhibit : BOOL;          // Owner in error: remove the enable at once
    i_bFaultReset : BOOL;       // PO 1.8 (drive resets on the rising edge)
END_VAR
VAR_IN_OUT
    io_stMotor : Cnv_Motor_DUT;
END_VAR
VAR_OUTPUT
    q_bParamsValid : BOOL;      // Scaling and ramps configured
    q_bTurning : BOOL;          // PI 1.4 motor turning
END_VAR
VAR
    fbDrive : FB_SEW_VelocityDrive;
    rSetpoint : REAL;
    iSetpoint : INT;
    bMoveRequest : BOOL;
    bEnable : BOOL;
END_VAR

q_bParamsValid := i_stScaling.rSewSpeedPerUnit > 0.0
                  AND i_stScaling.uiSewAcceleration > 0
                  AND i_stScaling.uiSewDeceleration > 0;

// SETPOINT (signed, user units)
IF io_stMotor.Forward AND NOT io_stMotor.Reverse THEN
    rSetpoint := io_stMotor.Speed * i_stScaling.rSewSpeedPerUnit;
ELSIF io_stMotor.Reverse AND NOT io_stMotor.Forward THEN
    rSetpoint := -1.0 * io_stMotor.Speed * i_stScaling.rSewSpeedPerUnit;
ELSE
    rSetpoint := 0.0;
END_IF
iSetpoint := REAL_TO_INT(LIMIT(-32767.0, rSetpoint, 32767.0));

// ENABLE / START
bMoveRequest := (io_stMotor.Forward XOR io_stMotor.Reverse) AND iSetpoint <> 0 AND q_bParamsValid;
// Keep the enable until the motor has stopped, so a normal stop (start = 0)
// decelerates with the PO 4 ramp.
bEnable := i_bSafetyOk AND NOT i_bInhibit
           AND (bMoveRequest OR io_stMotor.stStatus.bMotorTurning);

fbDrive(i_stProcessInput := io_stMotor.stProcessInput,
        i_bEnable := bEnable,
        i_bStart := bMoveRequest AND bEnable,
        i_bFaultReset := i_bFaultReset,
        i_iSpeedSetpoint := iSetpoint,
        i_uiAcceleration := i_stScaling.uiSewAcceleration,
        i_uiDeceleration := i_stScaling.uiSewDeceleration);

io_stMotor.aProcessOutput := fbDrive.q_aProcessOutput;
io_stMotor.stStatus := fbDrive.q_stStatus;

// STATUS
// NOTE: Status is now the SEW status word (bit 0 = Ready). In Dallas, Status.%X0 was
// "axis enabled" and other popups read it as "neighbour running". Use stStatus.bMotorTurning.
io_stMotor.Status := fbDrive.q_stStatus.wStatusWord;
io_stMotor.Ready := fbDrive.q_bReady;
io_stMotor.Enabled := fbDrive.q_stStatus.bOutputStageEnabled;
io_stMotor.Lockout := fbDrive.q_stStatus.bCommunicationOk AND NOT fbDrive.q_stStatus.bStoInactive;  // STO active
io_stMotor.Error := fbDrive.q_bError
                    OR ((io_stMotor.Forward OR io_stMotor.Reverse) AND NOT q_bParamsValid);
q_bTurning := fbDrive.q_stStatus.bMotorTurning;

// ACTUAL SPEED, in the units of Speed (unsigned, as Dallas)
IF i_stScaling.rSewSpeedPerUnit > 0.0 THEN
    io_stMotor.Speed_Actual := ABS(INT_TO_REAL(fbDrive.q_stStatus.iActualSpeed)) / i_stScaling.rSewSpeedPerUnit;
ELSE
    io_stMotor.Speed_Actual := 0.0;
END_IF
// PI 4 is signed [0.1 % nominal torque]; Actual_Torque is unsigned [%]
io_stMotor.Actual_Torque := DINT_TO_UINT(ABS(INT_TO_DINT(fbDrive.q_stStatus.iActualTorque_0p1pct)) / 10);
// Actual_Current is not in the 5 PD profile (needs extra process values in MOVISUITE).
END_FUNCTION_BLOCK


// ---------------------------------------------------------------- POUs/Carousel/PopUp_Conveyor_FB
// Popup conveyor of the carousel: lift + roller + optional chain. One block for every popup.
// Lift Up   = roller level: transfers on sides 1/2 (roller axis).
// Lift Down = chain level:  transfers on sides 3/4 (chain axis).
// Inbound: this popup runs first; the sender waits until it sees this popup running.
// Outbound: this popup waits until the receiver runs (Side[n].Running), then runs.
FUNCTION_BLOCK PopUp_Conveyor_FB
VAR_INPUT
    Cnv_Settings : PopUp_Settings_DUT;
    i_bSafetyOk : BOOL;         // Carousel safety OK (Dallas "Main_Safety_RTG1_DB".SAFETY_OK_CAROUSEL)
    i_bLiftPathOk : BOOL;       // Lift path free / light curtain OK (Dallas "LighGuard_Cut-Off Path 01")
    i_bChainPathOk : BOOL;      // Chain path free (Dallas PConveyor_1_FB_1 gated the chain with the same
                                // light guard; wire TRUE only if the chain side has no curtain)
    i_bResetAll : BOOL;         // System_Control.Reset_All
END_VAR
VAR_IN_OUT
    Cnv_Control : PopUp_Control_DUT;
END_VAR
VAR
    eState : E_PopUpState := E_PopUpState.INIT;
    eLastState : E_PopUpState := E_PopUpState.INIT;
    iSide : INT;                // Side of the active transfer (1..4)
    bChainAxis : BOOL;          // Active transfer uses the chain
    bForward : BOOL;            // Direction of the active axis
    bOutboundRunning : BOOL;    // Outbound started (receiver was running)
    bReset : BOOL;
    bDriveInhibit : BOOL;       // Safety or drive error: remove the enables at once
    rTransferSpeed : REAL;
    uiBoostTime : UINT;

    rtExecute : R_TRIG;
    rtStop : R_TRIG;
    rtAuto : R_TRIG;
    tonTransfer : TON;          // Transfer / lift watchdog (error 14:1)
    tonBoost : TON;             // Start boost

    fbRoller : FB_Cnv_SewMotor;
    fbChain : FB_Cnv_SewMotor;
    fbLift : FB_Cnv_SewMotor;
END_VAR

rtExecute(CLK := Cnv_Control.Instruction.Execute);
rtStop(CLK := Cnv_Control.Instruction.Stop);
bReset := Cnv_Control.Instruction.Reset OR i_bResetAll;

Cnv_Control.Enabled := Cnv_Control.Instruction.Enable;

{region "Modes"}
    Cnv_Control.Mode := Cnv_Control.Instruction.Mode_Change;
    IF (Cnv_Control.Mode = 1 OR Cnv_Control.Mode = 5) AND NOT Cnv_Control.Error THEN
        eState := E_PopUpState.MANUAL;
    END_IF
    rtAuto(CLK := Cnv_Control.Mode = 3);
    IF rtAuto.Q THEN
        eState := E_PopUpState.INIT;
    END_IF
{endregion}

{region "Cyclic checks"}
    Cnv_Control.Cnv_Occupied := Cnv_Control.Inputs.Pallet_Present;
    Cnv_Control.Stopped := NOT Cnv_Control.Running;
    Cnv_Control.Ready_For_Task := Cnv_Control.Instruction.Inbound_Ready
                                  OR Cnv_Control.Instruction.Outbound_Ready;
{endregion}

{region "Auto / Semi-auto"}
    CASE eState OF
    E_PopUpState.INIT:
        Cnv_Control.Instruction.Transfer_Complete := FALSE;
        Cnv_Control.Instruction.Transfer_in_Progress := FALSE;
        Cnv_Control.Running := FALSE;
        Cnv_Control.Active_Side := 0;
        bOutboundRunning := FALSE;
        M_StopMotors();
        IF Cnv_Control.Enabled AND (Cnv_Control.Mode = 2 OR Cnv_Control.Mode = 3)
           AND NOT Cnv_Control.Error
        THEN
            eState := E_PopUpState.STANDBY;
        END_IF

    E_PopUpState.STANDBY:
        IF rtExecute.Q OR Cnv_Control.Instruction.Start_Transfer THEN
            IF Cnv_Control.Instruction.Inbound_Ready AND NOT Cnv_Control.Running THEN
                iSide := M_FindSide(Cnv_Control.Instruction.Transfer_From_ID);
                IF iSide = 0 OR NOT M_LiftAtSideLevel(iSide) THEN
                    Cnv_Control.Warning := 1;   // Cannot transfer from that conveyor
                ELSIF NOT Cnv_Control.Side[iSide].In_Position THEN
                    // NEW warning 2: neighbour not in position (e.g. VTD not at the level).
                    // Dallas had Error_Word_3 bit 2 for this, but that branch was unreachable.
                    Cnv_Control.Warning := 2;
                ELSE
                    M_StartTransfer(i_iSide := iSide, i_bOutbound := FALSE);
                    eState := E_PopUpState.INBOUND;
                END_IF

            ELSIF Cnv_Control.Instruction.Outbound_Ready AND NOT Cnv_Control.Running THEN
                iSide := M_FindSide(Cnv_Control.Instruction.Transfer_To_ID);
                IF iSide = 0 OR NOT M_LiftAtSideLevel(iSide) THEN
                    Cnv_Control.Warning := 1;   // Cannot transfer TO that conveyor
                ELSIF NOT Cnv_Control.Side[iSide].In_Position THEN
                    Cnv_Control.Warning := 2;
                ELSE
                    M_StartTransfer(i_iSide := iSide, i_bOutbound := TRUE);
                    eState := E_PopUpState.OUTBOUND;
                END_IF
            ELSE
                Cnv_Control.Warning := 0;       // Dallas: no task can start, start bit is TRUE
            END_IF
        END_IF

        // Lift requests: separate IF as Dallas (also when already in position, so Done
        // still pulses), but only if no transfer started in this cycle (Dallas could
        // overwrite a transfer started in the same cycle).
        IF eState = E_PopUpState.STANDBY THEN
            IF Cnv_Control.Instruction.Lift_Up THEN
                Cnv_Control.Done := FALSE;
                eState := E_PopUpState.LIFT_UP;
            ELSIF Cnv_Control.Instruction.Lift_Down THEN
                Cnv_Control.Done := FALSE;
                eState := E_PopUpState.LIFT_DOWN;
            END_IF
        END_IF

        // NEW: leave standby when disabled or no longer in Auto / Semi-auto
        IF NOT Cnv_Control.Enabled OR NOT (Cnv_Control.Mode = 2 OR Cnv_Control.Mode = 3) THEN
            eState := E_PopUpState.INIT;
        END_IF

    E_PopUpState.INBOUND:
        Cnv_Control.Running := TRUE;
        M_RunTransferAxis();
        // Dallas: own pallet sensor. (Dallas popup 2 from the VTD used "NOT entry sensor".)
        // Dallas behavior kept: a Stop edge also ends the transfer with Done = TRUE.
        IF rtStop.Q OR Cnv_Control.Inputs.Pallet_Present THEN
            M_EndTransfer();
        END_IF

    E_PopUpState.OUTBOUND:
        IF Cnv_Control.Side[iSide].Running THEN
            bOutboundRunning := TRUE;           // receiver is running: start (latched)
        END_IF
        IF bOutboundRunning THEN
            Cnv_Control.Running := TRUE;
            M_RunTransferAxis();
        END_IF
        IF rtStop.Q OR Cnv_Control.Side[iSide].Occupied THEN
            M_EndTransfer();
        END_IF

    E_PopUpState.LIFT_UP:
        Cnv_Control.Running := TRUE;
        Cnv_Control.Lift_Motor.Forward := TRUE;
        Cnv_Control.Lift_Motor.Reverse := FALSE;
        Cnv_Control.Lift_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Lift_Full_Speed);
        IF Cnv_Control.Inputs.Lift_Up THEN
            Cnv_Control.Done := TRUE;
            M_StopMotors();
            eState := E_PopUpState.INIT;
        END_IF

    E_PopUpState.LIFT_DOWN:
        Cnv_Control.Running := TRUE;
        Cnv_Control.Lift_Motor.Forward := FALSE;
        Cnv_Control.Lift_Motor.Reverse := TRUE;
        Cnv_Control.Lift_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Lift_Full_Speed);
        IF Cnv_Control.Inputs.Lift_Down THEN
            Cnv_Control.Done := TRUE;
            M_StopMotors();
            eState := E_PopUpState.INIT;
        END_IF

    E_PopUpState.ERROR:
        Cnv_Control.Running := FALSE;
        Cnv_Control.Active_Side := 0;
        bOutboundRunning := FALSE;
        M_StopMotors();
        Cnv_Control.Instruction.Stop := FALSE;
        Cnv_Control.Instruction.Transfer_in_Progress := FALSE;
        IF bReset THEN
            Cnv_Control.Warning := 0;
            Cnv_Control.Current_Task_ID := 0;
            Cnv_Control.Error := FALSE;
            Cnv_Control.Cnv_Errors.Error_Word_1 := 0;
            Cnv_Control.Cnv_Errors.Error_Word_2 := 0;
            Cnv_Control.Cnv_Errors.Error_Word_3 := 0;
            Cnv_Control.Cnv_Errors.Error_Word_4 := 0;
            eState := E_PopUpState.INIT;
        END_IF

    E_PopUpState.MANUAL:
        M_Manual();
        IF Cnv_Control.Mode <> 1 AND Cnv_Control.Mode <> 5 THEN
            eState := E_PopUpState.INIT;
        END_IF
    END_CASE
{endregion}

{region "Watchdog"}
    // Restarted on every state change. Lift and chain timers only count while their
    // path is OK (Dallas). Counted from state entry, as Dallas popups 2..4.
    CASE eState OF
    E_PopUpState.INBOUND, E_PopUpState.OUTBOUND:
        IF bChainAxis THEN
            tonTransfer.PT := UDINT_TO_TIME(UINT_TO_UDINT(Cnv_Settings.Chain_Transfer_Time) * 1000);
            tonTransfer(IN := eState = eLastState AND i_bChainPathOk);
        ELSE
            tonTransfer.PT := UDINT_TO_TIME(UINT_TO_UDINT(Cnv_Settings.Roller_Transfer_Time) * 1000);
            tonTransfer(IN := eState = eLastState);
        END_IF
    E_PopUpState.LIFT_UP, E_PopUpState.LIFT_DOWN:
        tonTransfer.PT := UDINT_TO_TIME(UINT_TO_UDINT(Cnv_Settings.Lift_Transfer_Time) * 1000);
        tonTransfer(IN := eState = eLastState AND i_bLiftPathOk);
    ELSE
        tonTransfer(IN := FALSE);
    END_CASE
    IF tonTransfer.Q THEN       // 14:1 Transfer timed out
        Set_Bit_F(BIT_Number := 3, Variavel := Cnv_Control.Cnv_Errors.Error_Word_2);
    END_IF
{endregion}

{region "Cyclic error checks"}
    IF NOT i_bSafetyOk THEN     // 11:1
        Set_Bit_F(BIT_Number := 0, Variavel := Cnv_Control.Cnv_Errors.Error_Word_1);
    END_IF
    IF Cnv_Control.Roller_Motor.Error OR Cnv_Control.Lift_Motor.Error
       OR (Cnv_Settings.Has_Chain AND Cnv_Control.Chain_Motor.Error)
    THEN
        Set_Bit_F(BIT_Number := 0, Variavel := Cnv_Control.Cnv_Errors.Error_Word_4);
    END_IF
    IF Cnv_Control.Cnv_Errors.Error_Word_1 <> 0 OR Cnv_Control.Cnv_Errors.Error_Word_2 <> 0
       OR Cnv_Control.Cnv_Errors.Error_Word_3 <> 0 OR Cnv_Control.Cnv_Errors.Error_Word_4 <> 0
    THEN
        Cnv_Control.Error := TRUE;
        eState := E_PopUpState.ERROR;
    END_IF
{endregion}

{region "VFD - SEW MOVIKIT Velocity (replaces SinaSpeed x3)"}
    // Safety (word 1) or drive (word 4) errors remove the enable at once (FCB 14).
    // Other errors (timeout 14:1 ...) stop with the normal ramp: the ERROR state clears
    // Forward/Reverse, as Dallas state 400.
    bDriveInhibit := Cnv_Control.Cnv_Errors.Error_Word_1 <> 0 OR Cnv_Control.Cnv_Errors.Error_Word_4 <> 0;

    fbRoller(i_stScaling := Cnv_Settings.Roller_Drive,
             i_bSafetyOk := i_bSafetyOk,
             i_bInhibit := bDriveInhibit,
             i_bFaultReset := bReset,
             io_stMotor := Cnv_Control.Roller_Motor);

    IF Cnv_Settings.Has_Chain THEN
        // Dallas PConveyor_1_FB_1: chain EnableAxis AND "LighGuard_Cut-Off Path 01"
        fbChain(i_stScaling := Cnv_Settings.Chain_Drive,
                i_bSafetyOk := i_bSafetyOk AND i_bChainPathOk,
                i_bInhibit := bDriveInhibit,
                i_bFaultReset := bReset,
                io_stMotor := Cnv_Control.Chain_Motor);
    ELSE
        Cnv_Control.Chain_Motor.Forward := FALSE;
        Cnv_Control.Chain_Motor.Reverse := FALSE;
    END_IF

    // Lift drive enable also needs the lift path (Dallas: EnableAxis AND "LighGuard_Cut-Off Path 01")
    fbLift(i_stScaling := Cnv_Settings.Lift_Drive,
           i_bSafetyOk := i_bSafetyOk AND i_bLiftPathOk,
           i_bInhibit := bDriveInhibit,
           i_bFaultReset := bReset,
           io_stMotor := Cnv_Control.Lift_Motor);
{endregion}

Cnv_Control.SM_State := TO_UINT(eState);
eLastState := eState;
END_FUNCTION_BLOCK


// ---- METHOD PRIVATE M_FindSide : INT  (side whose neighbour has this ID, 0 = none)
METHOD PRIVATE M_FindSide : INT
VAR_INPUT
    i_diId : DINT;
END_VAR
VAR
    i : INT;
END_VAR
M_FindSide := 0;
IF i_diId = 0 THEN
    RETURN;
END_IF
FOR i := 1 TO 4 DO
    IF Cnv_Settings.Side_ID[i] = i_diId THEN
        M_FindSide := i;
        RETURN;
    END_IF
END_FOR
END_METHOD


// ---- METHOD PRIVATE M_LiftAtSideLevel : BOOL  (lift at the level of that side's axis)
METHOD PRIVATE M_LiftAtSideLevel : BOOL
VAR_INPUT
    i_iSide : INT;
END_VAR
CASE i_iSide OF
1, 2:
    M_LiftAtSideLevel := Cnv_Control.Inputs.Lift_Up AND NOT Cnv_Control.Inputs.Lift_Down;
3, 4:
    M_LiftAtSideLevel := Cnv_Settings.Has_Chain
                         AND Cnv_Control.Inputs.Lift_Down AND NOT Cnv_Control.Inputs.Lift_Up;
ELSE
    M_LiftAtSideLevel := FALSE;
END_CASE
END_METHOD


// ---- METHOD PRIVATE M_StartTransfer
// Inbound from side 1 -> roller Reverse, side 2 -> roller Forward, 3 -> chain Reverse, 4 -> chain Forward.
// Outbound to   side 1 -> roller Forward, side 2 -> roller Reverse, 3 -> chain Forward, 4 -> chain Reverse.
METHOD PRIVATE M_StartTransfer
VAR_INPUT
    i_iSide : INT;
    i_bOutbound : BOOL;
END_VAR
bChainAxis := i_iSide >= 3;
IF i_bOutbound THEN
    bForward := (i_iSide = 1 OR i_iSide = 3);
ELSE
    bForward := (i_iSide = 2 OR i_iSide = 4);
END_IF
IF bChainAxis THEN
    rTransferSpeed := UINT_TO_REAL(Cnv_Settings.Chain_Full_Speed);
ELSE
    rTransferSpeed := UINT_TO_REAL(Cnv_Settings.Roller_Full_Speed);
END_IF
uiBoostTime := Cnv_Settings.Side_Boost_Time[i_iSide];
bOutboundRunning := FALSE;
tonBoost(IN := FALSE);
Cnv_Control.Active_Side := i_iSide;
Cnv_Control.Done := FALSE;
Cnv_Control.Warning := 0;
Cnv_Control.Instruction.Transfer_in_Progress := TRUE;
Cnv_Control.Current_Task_ID := Cnv_Control.Instruction.Task_ID;
END_METHOD


// ---- METHOD PRIVATE M_RunTransferAxis  (Boost_Speed for Side_Boost_Time[side], then full speed)
METHOD PRIVATE M_RunTransferAxis
VAR
    rSpeed : REAL;
END_VAR
tonBoost(IN := TRUE, PT := UDINT_TO_TIME(UINT_TO_UDINT(uiBoostTime) * 1000));
IF uiBoostTime > 0 AND NOT tonBoost.Q THEN
    rSpeed := UINT_TO_REAL(Cnv_Settings.Boost_Speed);
ELSE
    rSpeed := rTransferSpeed;
END_IF
IF bChainAxis THEN
    Cnv_Control.Chain_Motor.Forward := bForward;
    Cnv_Control.Chain_Motor.Reverse := NOT bForward;
    Cnv_Control.Chain_Motor.Speed := rSpeed;
ELSE
    Cnv_Control.Roller_Motor.Forward := bForward;
    Cnv_Control.Roller_Motor.Reverse := NOT bForward;
    Cnv_Control.Roller_Motor.Speed := rSpeed;
END_IF
END_METHOD


// ---- METHOD PRIVATE M_EndTransfer
METHOD PRIVATE M_EndTransfer
Cnv_Control.Done := TRUE;
Cnv_Control.Active_Side := 0;
bOutboundRunning := FALSE;
tonBoost(IN := FALSE);
M_StopMotors();
eState := E_PopUpState.INIT;
END_METHOD


// ---- METHOD PRIVATE M_StopMotors
METHOD PRIVATE M_StopMotors
Cnv_Control.Roller_Motor.Forward := FALSE;
Cnv_Control.Roller_Motor.Reverse := FALSE;
Cnv_Control.Roller_Motor.Speed := 0.0;
Cnv_Control.Chain_Motor.Forward := FALSE;
Cnv_Control.Chain_Motor.Reverse := FALSE;
Cnv_Control.Chain_Motor.Speed := 0.0;
Cnv_Control.Lift_Motor.Forward := FALSE;
Cnv_Control.Lift_Motor.Reverse := FALSE;
Cnv_Control.Lift_Motor.Speed := 0.0;
END_METHOD


// ---- METHOD PRIVATE M_Manual  (Dallas state 500, with the interlocks kept)
//  Roller only at Lift Up, chain only at Lift Down, lift only while roller and chain
//  are off. Changes against Dallas:
//   - each axis is stopped when its interlock is lost (Dallas kept the last command);
//   - roller/chain also blocked while the lift moves, and the lift checks this cycle's
//     roller/chain commands, not only last cycle's "enabled" feedback;
//   - chain mapping as Dallas popup 3 (Chain_Fwd OR Start_Transfer = Forward). Popup 2
//     had it swapped only to offset its inverted chain sign (now set in MOVISUITE);
//   - Running is computed once at the end (Dallas: LIFT overwrote Running of ROLLER).
METHOD PRIVATE M_Manual
VAR
    bLiftBusy : BOOL;
    bTransportBusy : BOOL;
END_VAR

IF NOT Cnv_Control.Enabled THEN
    M_StopMotors();
    Cnv_Control.Running := FALSE;
    RETURN;
END_IF

bLiftBusy := Cnv_Control.Lift_Motor.Enabled
             OR Cnv_Control.Lift_Motor.Forward OR Cnv_Control.Lift_Motor.Reverse;

// ROLLER
IF Cnv_Control.Inputs.Lift_Up AND NOT Cnv_Control.Inputs.Lift_Down AND NOT bLiftBusy
   AND (Cnv_Control.Instruction.Roller_Fwd OR Cnv_Control.Instruction.Start_Transfer)
THEN
    Cnv_Control.Roller_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Roller_Manual_Speed);
    Cnv_Control.Roller_Motor.Forward := TRUE;
    Cnv_Control.Roller_Motor.Reverse := FALSE;
ELSIF Cnv_Control.Inputs.Lift_Up AND NOT Cnv_Control.Inputs.Lift_Down AND NOT bLiftBusy
   AND (Cnv_Control.Instruction.Roller_Bwd OR Cnv_Control.Instruction.Start_Transfer_Backward)
THEN
    Cnv_Control.Roller_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Roller_Manual_Speed);
    Cnv_Control.Roller_Motor.Forward := FALSE;
    Cnv_Control.Roller_Motor.Reverse := TRUE;
ELSE
    Cnv_Control.Roller_Motor.Speed := 0.0;
    Cnv_Control.Roller_Motor.Forward := FALSE;
    Cnv_Control.Roller_Motor.Reverse := FALSE;
END_IF

// CHAIN
IF Cnv_Settings.Has_Chain AND Cnv_Control.Inputs.Lift_Down AND NOT Cnv_Control.Inputs.Lift_Up
   AND NOT bLiftBusy
   AND (Cnv_Control.Instruction.Chain_Fwd OR Cnv_Control.Instruction.Start_Transfer)
THEN
    Cnv_Control.Chain_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Chain_Manual_Speed);
    Cnv_Control.Chain_Motor.Forward := TRUE;
    Cnv_Control.Chain_Motor.Reverse := FALSE;
ELSIF Cnv_Settings.Has_Chain AND Cnv_Control.Inputs.Lift_Down AND NOT Cnv_Control.Inputs.Lift_Up
   AND NOT bLiftBusy
   AND (Cnv_Control.Instruction.Chain_Bwd OR Cnv_Control.Instruction.Start_Transfer_Backward)
THEN
    Cnv_Control.Chain_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Chain_Manual_Speed);
    Cnv_Control.Chain_Motor.Forward := FALSE;
    Cnv_Control.Chain_Motor.Reverse := TRUE;
ELSE
    Cnv_Control.Chain_Motor.Speed := 0.0;
    Cnv_Control.Chain_Motor.Forward := FALSE;
    Cnv_Control.Chain_Motor.Reverse := FALSE;
END_IF

// LIFT (Dallas: NOT SinaSpeed_Roller.AxisEnabled AND NOT SinaSpeed_Chain.AxisEnabled)
bTransportBusy := Cnv_Control.Roller_Motor.Enabled OR Cnv_Control.Chain_Motor.Enabled
                  OR Cnv_Control.Roller_Motor.Forward OR Cnv_Control.Roller_Motor.Reverse
                  OR Cnv_Control.Chain_Motor.Forward OR Cnv_Control.Chain_Motor.Reverse;
IF NOT bTransportBusy AND Cnv_Control.Instruction.Lift_Up AND NOT Cnv_Control.Inputs.Lift_Up THEN
    Cnv_Control.Lift_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Lift_Manual_Speed);
    Cnv_Control.Lift_Motor.Forward := TRUE;
    Cnv_Control.Lift_Motor.Reverse := FALSE;
ELSIF NOT bTransportBusy AND Cnv_Control.Instruction.Lift_Down AND NOT Cnv_Control.Inputs.Lift_Down THEN
    Cnv_Control.Lift_Motor.Speed := UINT_TO_REAL(Cnv_Settings.Lift_Manual_Speed);
    Cnv_Control.Lift_Motor.Forward := FALSE;
    Cnv_Control.Lift_Motor.Reverse := TRUE;
ELSE
    Cnv_Control.Lift_Motor.Speed := 0.0;
    Cnv_Control.Lift_Motor.Forward := FALSE;
    Cnv_Control.Lift_Motor.Reverse := FALSE;
END_IF

Cnv_Control.Running := bTransportBusy
                       OR Cnv_Control.Lift_Motor.Forward OR Cnv_Control.Lift_Motor.Reverse;
END_METHOD


// ============================================================================
//  FC Conveyors_Transfer - popup part (to ADD to the existing POUs/System/Conveyors_Transfer)
//  Dallas FC24 hard-codes the targets per popup (1->2, 2->3/extractor, 3->4,
//  4->outbound/1). Here: Side[] is filled from the neighbours, then the ready
//  flags are generic. Assumes Settings.Pop_Up_Cnv : ARRAY[1..2] OF PopUp_Settings_DUT.
// ============================================================================
// VAR (add to the FC temp section)
//     p : INT;
//     s : INT;
//     bReceiver : BOOL;
// END_VAR

{region "POPUP SIDES (layout specific - CONFIRM with the SpaceX Rev 9 drawing)"}
    // Example: popup 1, side 1 (roller Forward end) = roller conveyor 1.
    // Roller_Control_DUT does not exist yet; field names below assume the same
    // shape as Buffer_Cnv_Control_DUT (Instruction.Inbound_Ready, Motor, Cnv_Occupied).
    // Control.Pop_Up_Cnv[1].Side[1].In_Position   := TRUE;
    // Control.Pop_Up_Cnv[1].Side[1].Inbound_Ready := Control.Roller_Cnv[1].Instruction.Inbound_Ready;
    // Control.Pop_Up_Cnv[1].Side[1].Running       := Control.Roller_Cnv[1].Motor.stStatus.bMotorTurning;
    // Control.Pop_Up_Cnv[1].Side[1].Occupied      := Control.Roller_Cnv[1].Cnv_Occupied;
    //
    // Popup to popup (roller axis): the neighbour popup must be at the same level
    // (Dallas FC24: PopUp_Cnv[1] outbound only if popup 1 AND popup 2 "Lift Up").
    // Control.Pop_Up_Cnv[1].Side[2].In_Position   := Control.Pop_Up_Cnv[2].Inputs.Lift_Up;
    // Control.Pop_Up_Cnv[1].Side[2].Inbound_Ready := Control.Pop_Up_Cnv[2].Instruction.Inbound_Ready;
    // Control.Pop_Up_Cnv[1].Side[2].Running       := Control.Pop_Up_Cnv[2].Roller_Motor.stStatus.bMotorTurning;
    // Control.Pop_Up_Cnv[1].Side[2].Occupied      := Control.Pop_Up_Cnv[2].Cnv_Occupied;
    //
    // Next to the VTD/extractor (Dallas: VTD_Control.Current_Level = 0):
    // Control.Pop_Up_Cnv[n].Side[3].In_Position   := Control.VTD_Sys.<current level> = <carousel level>;
    //
    // In_Position is only checked when the transfer starts. The VTD must not leave
    // while the popup next to it transfers: OR the popup into the existing VTD
    // interlock, as Dallas FC24 region "TRANSFER IN PROGRESS FOR VTD":
    // "Cnv_TIP_For_VTD" := ... OR (<VTD at carousel level> AND Control.Pop_Up_Cnv[n].Instruction.Transfer_in_Progress);
{endregion}

{region "POPUP READY TO RECEIVE / READY TO SEND"}
    FOR p := 1 TO 2 DO
        Control.Pop_Up_Cnv[p].Instruction.Inbound_Ready :=
            NOT Control.Pop_Up_Cnv[p].Running
            AND NOT Control.Pop_Up_Cnv[p].Cnv_Occupied
            AND NOT Control.Pop_Up_Cnv[p].Instruction.Outbound_Ready
            AND (Control.Pop_Up_Cnv[p].Mode = 2 OR Control.Pop_Up_Cnv[p].Mode = 3);

        // A neighbour that can receive, on a side whose axis matches the lift position
        // (Dallas: popup 1 needs Lift Up, popup 2 Lift Down, popup 4 either).
        bReceiver := FALSE;
        FOR s := 1 TO 4 DO
            IF Settings.Pop_Up_Cnv[p].Side_ID[s] <> 0
               AND Control.Pop_Up_Cnv[p].Side[s].In_Position
               AND Control.Pop_Up_Cnv[p].Side[s].Inbound_Ready
               AND ((s <= 2 AND Control.Pop_Up_Cnv[p].Inputs.Lift_Up)
                    OR (s >= 3 AND Settings.Pop_Up_Cnv[p].Has_Chain AND Control.Pop_Up_Cnv[p].Inputs.Lift_Down))
            THEN
                bReceiver := TRUE;
            END_IF
        END_FOR

        Control.Pop_Up_Cnv[p].Instruction.Outbound_Ready :=
            bReceiver
            AND NOT Control.Pop_Up_Cnv[p].Instruction.Transfer_in_Progress
            AND Control.Pop_Up_Cnv[p].Cnv_Occupied
            AND (Control.Pop_Up_Cnv[p].Mode = 2 OR Control.Pop_Up_Cnv[p].Mode = 3);
    END_FOR
{endregion}


// ============================================================================
//  Call example (MAIN or a carousel program), after Inputs() and before Outputs()
// ============================================================================
// VAR  fbPopUp : ARRAY[1..2] OF PopUp_Conveyor_FB;  END_VAR
//
// FOR i := 1 TO 2 DO
//     fbPopUp[i](Cnv_Settings := Settings.Pop_Up_Cnv[i],
//                i_bSafetyOk := <carousel safety OK from TwinSAFE / IO_OTHERS>,
//                i_bLiftPathOk := <carousel light curtains OK (EP1957)>,
//                i_bChainPathOk := <chain side path OK>,
//                i_bResetAll := System_Control.Reset_All,
//                Cnv_Control := Control.Pop_Up_Cnv[i]);
// END_FOR
//
// Inputs():  Control.Pop_Up_Cnv[i].Inputs.*, *.Roller/Chain/Lift_Motor.stProcessInput  <- IO_*
// Outputs(): IO_* <- Control.Pop_Up_Cnv[i].Roller/Chain/Lift_Motor.aProcessOutput
// (the carousel MOVIMOT drives are not in SpaceX.tsproj yet)
