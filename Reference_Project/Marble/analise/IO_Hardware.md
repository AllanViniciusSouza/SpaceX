# Marble_Engineering – hardware e I/O (referência para SpaceX)

Fonte: MCP `tia-portal` (somente leitura) em 19/10/2026 + tag tables em `../tags/` + `../scl/INPUTS.scl` / `../scl/OUTPUTS.scl`.
IPs e endereços de módulos não são retornados pelo MCP (`get_io_mapping` vazio).

## Dispositivos (16)
| Dispositivo | Tipo / código | Observação |
|---|---|---|
| Main_system | S7-1500 **R/H** (`Device.S71500/HR`), PLC_1 + PLC_2 = 6ES7 518-4JT10-0AB0 (1518HF-4 PN) | Todo o programa (≈280 blocos) |
| S7-1200 station_2 / PLC_HMI | 6ES7 214-1AF40-0XB0 (1214FC, F-CPU) | Main e Main_Safety_RTG1 vazios; interface com o 1500 é física (F-DI/F-DQ no Remote Panel 2) |
| HMI_1, HMI_2 | WinCC Comfort/Advanced (não Unified) | MCP não lê telas (só Unified) |
| Tablet | 6AV7880-4xxxx (IPC.MD34A) | Painel móvel / tablet |
| SINAMICS G_1 | G115D (6SL3500-0XE50-7FAx) | Único drive listado como dispositivo de topo; os G120 dos transportadores/VTD aparecem só pelas tags (provavelmente GSD) |
| SCALANCE | 6× XC-200 (6GK5 216-4BS00), 1× S-600 (6GK5 636-2GS00), 4× W766-1 (6GK5 766-1GE00) | Rede + Wi-Fi (shuttles/tablet) |

Pacotes: STEP 7 Prof/Safety V20, Startdrive V20 SP1 (G110M/G120/G120C/G120D/G120P/G115D), WinCC Basic/Comfort/Advanced V20, WinCC Unified Basic V20.

## Tag tables (Main_system, 28 exportadas; IO_PLC_HMI e Device_Control_Tags vazias)
Todas as tabelas de I/O existem em par **_1 / _2** (sistema 1 / sistema 2).

| Tabela | Conteúdo |
|---|---|
| IO_Remote_Panel_1/_2 (70/76) | F-DI/F-DQ: E-STOP (CABINET) CH1/2, RESET (CABINET), OVERTRAVEL (no ET200), Chain Slack 1..4 CH1/2, LIGHT GUARD(S) 1/2 CH1/2, SAFETY_GATE_1..4 CH1/2, E-STOP L1..L6 CH1/2, KEY REMOTE/LOCAL L1..L6 CH1/2, STO VTD CH1/CH2, BRAKE SUPPLY SAFETY CONTACTOR 1/2, VTU HOIST BRAKE SAFETY ENABLE EDM FEEDBACK; padrão: VTD UPPER/LOWER LIMIT, UPPER/LOWER ULTIMATE SLOWDOWN, UPPER ULTIMATE CREEP, PUSH TO ENTER/EXIT VTD ZONE, disjuntores (C11xx…, CVTD, VTD, PSU 24 V, ventilação), STACK LIGHTS R/O/G, RESET LAMP. Só o _2 tem `PLC_HMI - HMI 1/2 Estop`, `PLC_HMI - Profinet_Error_HMI 1/2` e `RESET 1/2 PLC HMI` |
| IO_ET200_1/_2 (29) | VTDn LEVEL DETECT 1/2, DOCKING PINS 1/2 EXTEND/RETRACT + EXTENDED/RETRACTED 1/2, OVERTRAVEL UPPER/LOWER CH1/CH2, stoppers C1102..C1106 (MOTOR, RAISED, LOWERED) |
| IO_VFDs_1/_2 (73) | Por drive (VTDn, CVTDn = transportador do extrator, C1102..C1106, C1202..C1206): ControlWord, StatusWord, ActualSpeed, ActualCurrent, ActualTorque, `Cxxxx_Inputs` (DI do drive no telegrama: bit0 = sensor Forward, bit1 = sensor Backward). VTD também tem AccFactor e MainSetpoint (CVTD) |
| IO_Encoders_1/_2 (11) | AE (SICK AFx60 PROFINET, perfil encoder: G1_STW/G1_ZSW, XIST1/2): AE_Control_Word_1/2, AE_Status_1/2, AE_Position_1/2 (DInt), AE_Speed. LE (fita Data Matrix; os warnings citam "non-PXV content" → provável Pepperl+Fuchs PXV, a confirmar): LE_Status, LE_X_Unsafe_Position (DInt, /10 = mm), LE_Speed, LE_Warnings |
| IO_Turck_1/_2 (20) | 2 light bars Turck por sistema: Color1/2, Intensity1/2, Animation, Speed, Pulse_Pattern, Direction, Bounce_Style, Percent_Width (BYTE) |
| Lock_1/_2/_3 (14) | Lock_n_Closed_CH1/2, Lock_n_Estop_CH1/2, Lock_n_Reset_Input1..4, Solenoid Enable_n, Lamps_n, Switches_n, Guard/Lock Position_n, Lock Reset_n (padrão de Euchner MGB2 PROFIsafe – inferência). Lock_1/_2 = sistema 1, Lock_3 = sistema 2 |
| IO_Charger Panel_L2..L6 (10) | Entradas: Output Voltage/Current, Set Voltage/Current Feedback (REAL), Charging Start (BOOL). Saídas: Set Voltage/Current Output (REAL), Start/Stop Charging, Confirm Voltage & Current Setting |
| Errors (58) / Warnings (2) | Errors_Profinet_1..11, Linear Encoder Device Errors/Warnings 1..5, Sick Lector error codes, Estop_Error_Word_1..6, Erros_Word_OPC_1..5, Errors_Word_Gates_1/2, Shuttles_1/2, LightGuard_1, Logistex, IND360 (restos de 5 sistemas/balança) |
| System_Control_Tags | Reset_All %M510.2, MQTT_Enable %M11.7, OPC_Enable %M11.6 |
| Default tag table | System/Clock memory (MB1159/MB1160), L1..L6_OK, L1..L6_Estop, System_1/2_Busy, LE_Bypass(1/2), Reset_Comissioning, OrderNo %MW158, Clear_OT_VTD/Buffers(1/2) |
| CNV_HMI(_IO), VTD_HMI(_IO), Screens, PopUp_Screens | Tags %M da HMI (sufixo `(1)` = segundo painel/seleção), base do `CNV_HMI`/`CNV_HMI_IO` do SpaceX |

## INPUTS (FC25) / OUTPUTS (FC5)
- INPUTS: `REGION SYSTEM n` → EXTRACTOR CONVEYOR, BUFFER CONVEYORS (LEVEL 2..6 × Cnv1/Cnv2), VTD, ABSOLUTE ENCODER, LINEAR ENCODER, SICK BARCODE LECTORS, VFD HARDWARE ID; depois CHARGER PANELS (→ `Control_DB.Charger_Level[2..6]`) e LEVEL KEYS (→ `HMI_DB.Rem_Loc_Keys[sys].Level[1..6]`).
- Nomenclatura: `C{S}{n}{LL}` (S = sistema, n = 1 Cnv1 / 2 Cnv2, LL = nível) → `Control_DB.LCnv_Sys[S].Cnv_Level[LL].Cnv{n}`; `CVTDn` → `ECnv_Sys[n]`; `VTDn` → `VTD_Sys[n]`.
- VTD: corrente = `(ActualCurrent/10)/72.5`; LE = `LE_X_Unsafe_Position / 10` (mm); AE_Position_1 = `(SHR(raw,2) − 31381317) × 0.0015318237304688 + 48062` (relação mecânica + offset, só para delta de encoders).
- OUTPUTS: por Remote Panel: STOPPER MOTOR := `Sf_Cxxxx_FB_DB.T_Run.Q XOR Force…`, DOCKING PINS := `VTD_Sys[n].Outputs.LPx_* XOR Force…`, STACK LIGHTS, RESET LAMP pisca com `NOT Remote_Panel_DB_n.Safety_OK`, `VTDn_ControlWord.%X7 := Instruction.Reset`, AccFactor, AE control words.
- Padrão "XOR Force" (DB `Force`) permite forçar cada saída pelo painel/HMI – no SpaceX tratar como TEST ONLY.

## Diferenças de hardware em relação ao SpaceX
| Item | Marble | SpaceX Inbound |
|---|---|---|
| CPU | S7-1500 H (1518HF) + S7-1200 F | TwinCAT 3 + EL6910 (TwinSAFE) |
| Sistemas por PLC | 2 VTDs (arrays [1..2]) | `Control.TcGVL` hoje: 1 VTD, `LCnv[1..6]`, carrossel (turntable, 2 pop-ups, 5 rolos, chain) |
| Drives | SINAMICS G120/G115D (SinaSpeed, telegrama 20) | SEW MOVI-C (MOVIKIT Positioning/Velocity) |
| Posição VTD | LE (fita Data Matrix) + AE SICK AFx60 | DL50 no MOVIPRO, posição via PI 7/8 |
| Buffers | 2 transportadores por nível (Cnv1+Cnv2), níveis 2..6 | 1 por nível (`LCnv[1..6]`) – confirmar |
| Sensores de transportador | DI do drive no telegrama (bit0/1) | DI do MOVIMOT via PI 5 ou EPP (em aberto) |
| Stoppers | rotativos, 1 motor + raised/lowered (ET200) | a definir |
| Carregadores | painéis L2..L6 (REAL V/I + start/stop) | `Charger_Level[2..6]`, S7-200 SMART via PROFINET (EL6633) |
