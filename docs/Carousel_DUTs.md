# Carousel data types (Sys1_Inbound, 21/10/2026, motor groups added the same day)

Types referenced by `GVLs/Control.TcGVL` and `GVLs/Settings.TcGVL` for the carousel.
Folder `DUTs/Carousel` (+ `DUTs/SEW/ST_SEW_VelocityScaling`), registered in `Sys1_Inbound.plcproj`.
Field names follow the existing conveyor DUTs (ECnv_Control_DUT, Buffer_Cnv_Control_DUT) so that FBs and the HMI
can treat all conveyors alike. Sources: existing conveyor DUTs and Dallas_Production
(`Reference_Project/Dallas/udts/PLC_data_types.scl`: PopUp_Cnv_*, Inbound/Outbound_Cnv_*).
No FB uses them yet. No TwinCAT build was run.

| GVL variable | Control type | Settings type | Drive |
|---|---|---|---|
| Pop_Up_Cnv[1..2] | PopUp_Control_DUT | PopUp_Settings_DUT | Motors.Lift + Motors.Transfer (Cnv_Motor_DUT), MOVIKIT Velocity 5 PD, one at a time |
| Roller_Cnv[1..5] | Roller_Control_DUT | Roller_Settings_DUT | Cnv_Motor_DUT, MOVIKIT Velocity 5 PD |
| Chain_Cnv | Chain_Control_DUT | Chain_Settings_DUT | Cnv_Motor_DUT, MOVIKIT Velocity 5 PD |
| TBCnv | TBCnv_Control_DUT | TBCnv_Settings_DUT | Cnv_Motor_DUT, MOVIKIT Velocity 5 PD, interlocked with Turn_Table |
| Turn_Table | Turn_Table_Control_DUT | Turn_Table_Settings_DUT | Turn_Table_Motor_DUT, MOVIKIT Positioning 8 PD, interlocked with TBCnv |

Sub-types: PopUp_Inputs_DUT, PopUp_Instruction_DUT, PopUp_Side_Status_DUT, PopUp_Motors_DUT, PopUp_Motor_Settings_DUT,
E_Carousel_PopUpMotor, Roller_Inputs_DUT,
Roller_Instruction_DUT, Turn_Table_Inputs_DUT, Turn_Table_Instruction_DUT, Turn_Table_Motor_DUT, ST_SEW_VelocityScaling.
In DUTs/Conveyors (generic): Cnv_Motor_Settings_DUT (settings of one motor, mirror of Cnv_Motor_DUT), Cnv_Interlock_DUT.
Reused: Cnv_Motor_DUT, Cnv_Errors_DUT, Cnv_Instruction_DUT, Cnv_Inputs_DUT, ST_SEW_ProcessInput8, ST_SEW_MovikitStatus.

## Motor groups (motors that must not run at the same time)

Rule: Control and Settings use the same group and member names (`Control.X.Motor(s)` <-> `Settings.X.Motor(s)`).

- Inside one device: `Pop_Up_Cnv[n].Motors.Lift` / `.Transfer`. The popup FB uses one
  `FB_Conveyor_MotorInterlock` instance (motor 1 = Lift, 2 = Transfer = `E_Carousel_PopUpMotor`) and shows
  `Active_Motor` / `Motor_Changeover`. Changeover time: `Settings.Pop_Up_Cnv[n].Changeover_Time` [ms].
- Between two devices: `Turn_Table` and `TBCnv` stay separate devices, each with `Interlock : Cnv_Interlock_DUT`.
  One `FB_Conveyor_MotorInterlock` instance (planned in MAIN, before both device FBs) maps
  `Interlock.Run_Request` / `Interlock.Motor_Stopped` -> `Interlock.Run_Allowed`.
  Changeover time: `Settings.Turn_Table.Changeover_Time` [ms].
- `FB_Conveyor_MotorInterlock` (POUs/Conveyors): up to 4 motors; a motor is granted only when all motors are
  stopped for the changeover time; lowest index wins; 0 = not configured blocks everything; functional
  interlock, NOT a safety function.
- Position permissives stay in the device FBs: transfer only at Lift_Up, TBCnv only when the turntable is
  In_Position, rotation only with the pallet fully on the table or the table empty.


Notes:
- Popup sides: 1/2 = transfer Forward/Reverse end (Lift_Up), 3/4 = Lift_Down level (pallet moved by the neighbour, e.g. Chain_Cnv). `Settings.Side_ID[n]` = neighbour ID,
  `Control.Side[n]` = neighbour status, written by Conveyors_Transfer. See `Reference_Project/Dallas/analise/PopUp_TwinCAT_Proposta.st`.
- SEW scaling: `ST_SEW_VelocityScaling` (rSewSpeedPerUnit, uiSewAcceleration, uiSewDeceleration), same meaning as in
  Buffer_Cnv_Settings_DUT. 0 = not configured, the motor does not move.
- Sensors: TRUE = condition present; NC sensors are inverted in FC Inputs.

Open points:
- Popup = lift + transfer (user, 21/10). To confirm: Lift_Down = chain level (pallet on Chain_Cnv).
- Chain_Cnv x popup lifts: the chain must not run while a popup lift moves. Same FB if one lift at a time is
  acceptable, otherwise a dedicated rule (open).
- Which rollers are forklift stations (`Fork_Lift_Detect`, `Automatic_Start`, `Empty`, `No_Forklift_Detect_Timer`).
- Turntable: number of stations (`Position[1..4]`), encoder format and status bits of the EPP5001
  (`Turn_Table_Inputs_DUT` keeps raw values), process-data words for the external position (AGENTS.md "Turntable").
- Sensor list per conveyor (EPP1008 has 8 DI per roller; only forward/backward sensors are modelled).
- `Settings.LCnv : ARRAY[1..6] OF Cnv_VTD_Settings_DUT` holds 2 conveyors x levels 2..6 per element, while
  `Control.LCnv[1..6]` is one Buffer_Cnv_Control_DUT per level; `Settings.VTD` / `Settings.ECnv` are still `[1..2]`.
