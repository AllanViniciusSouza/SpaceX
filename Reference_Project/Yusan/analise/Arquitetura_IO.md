# Yusan (20/10) – hardware, topologia, I/O e comunicação

Fontes: `list_devices` do MCP, `../tags/_all_tags.csv` (52 tabelas, 2625 tags), `../db/Control_DB.txt`, `../scl/*`. Endereços = endereços TIA (não valem para o SpaceX).

## Hardware (projeto TIA)
- `Main_System`: S7-1500 **R/H**, 2× CPU 6ES7 518-4JP00-0AB0 (PLC_1/PLC_2). Marble: 2× 6ES7 518-4JT10-0AB0.
- `S7-1200 station_2` / `PLC_HMI`: 6ES7 212-1AF40-0XB0 (Marble: 1214FC). Blocos inconsistentes – não exportados.
- HMI, HMI_1 (WinCC Comfort/Advanced), Tablet 6AV7880-4 (IPC MD34A).
- Rede: 15 SCALANCE XC-200, 1 S-600, 10 W766-1 (WLAN).
- Drives G120 por telegrama (`ControlWord/MainSetpoint/StatusWord/ActualSpeed/ActualCurrent`) – só nas tags. 74 drives: sistemas 1–3 com 18 cada (VTD, CVTD, C{S}101–108, C{S}201–208), sistemas 4–5 com 10 cada (VTD, CVTD, C{S}101–108).

## Topologia
| | Sistemas 1–3 | Sistemas 4–5 |
|---|---|---|
| Níveis | 8 (`Cnv_Level[1..8]`) | 8 |
| Transportadores por nível | Cnv1 = lado 1 (`C{S}1LL`), Cnv2 = lado 2 (`C{S}2LL`) | Só Cnv1 (`C{S}1LL`) |
| Nível 1 | Cnv1 = infeed Logistex (J13x0), Cnv2 = outfeed | – |
| Light guards / gates / travas | CX101 + CX201, Gate 1/2, Lock 2n-1 / 2n | Gate 1, Lock 9 / 10 |
| VTD | `VTD_FB` + `EConveyor_FB` (CVTD) | Idem + detecção de shuttle (`Shuttle_Loaded`) |

`Control_DB`: `ECnv_Sys/LCnv_Sys/VTD_Sys/WCS_OPC_Control/VTDBarcode_Station[1..5]`, `Shuttles_Position[1..23]`, `Pallet_ID_Received[1..3]`, `Gate_Station[1..12]`.
Travas: RP1 → Lock 1/2, RP2 → 3/4, RP3 → 5/6, RP4 → 9, RP5 → 10, Main Panel → 7/8/11/12 (acesso lateral por nível).

## I/O por tabela
| Tabela | Conteúdo |
|---|---|
| `IO_ET200_n` (203 / 127) | Por transportador: SENSOR CNV LEFT/RIGHT, LEFT/RIGHT (PALLET DETECT 1/2), SAFETY PIN1 UP/DOWN, SHUTTLE IN POSITION 1/2. Carro do VTD: CVTDn LEFT, LEFT PD1, CENTER, RIGHT PD1, RIGHT, **OVERHANG LEFT/RIGHT**; docking pins extended/retracted 1/2, level detect 1/2, ultimate slowdown/creep. E-STOP Ln e KEY REMOTE/LOCAL Ln (CH1/CH2) por nível |
| `IO_Remote_Panel_n` (108 / 71) | F-I/O: overtravel CH1/CH2, chain slack 1–4 CH1/CH2, E-stop/reset do armário, light guards C{S}101/C{S}201 CH1/CH2, gate sensors 1/2 CH1/CH2. Saídas: STO VTD, STO CONVEYOR VTD, STO CNV VFD (níveis 1-3/4-6/7-8 × lado 1/2), Power Enable Safety Stopper (mesmos grupos), VTU HOIST BRAKE SAFETY ENABLE 1/2 + EDM, EDM dos stoppers, stopper rotate por transportador, docking pins, stack lights SCA, disjuntores, push to enter/exit VTD zone |
| `IO_VFDs_n` | Palavras G120 de cada drive |
| `IO_Encoders_n` | AE SICK AFx60 (control/status words, position 1/2, speed) + LE (status, `LE_X_Unsafe_Position`, speed, warnings) – igual ao Marble |
| `IO_Turck_n` | Light bars front/rear (bytes de cor, intensidade, animação) |
| `IO_Main Panel` | Stack light, feedback de alimentação dos remote/switch/charger panels, PSU 24 V/48 V OK, E-stop do armário principal CH1/CH2 + reset, sinais do PLC_HMI (HMI 1/2 Estop, Profinet_Error, RESET PLC HMI CH1/CH2) |
| `IO_Charger Panels` | 8 painéis × 3 carregadores: Contactor ON, MCB healthy, comando do contator |
| `Lock_1..12` | Estop CH1/CH2, Closed CH1/CH2, Solenoid Enable, Lamps (byte), Reset_Input1..4, Switches (byte), Lock/Guard Position (padrão Euchner MGB2 – inferência) |
| `CNV_HMI(_IO)`, `VTD_HMI(_IO)`, `Screens`, `PopUp_Screens` | Memórias da HMI (%M) |
| `Errors`, `Warnings`, `System_Control_Tags`, `Device_Control_Tags` | Palavras de erro (%MW, inclui `Error_Word_Overhang` %MW848), `Global_Estop`, `Reset_All`, `HMI_1_Local_Mode`, `MQTT/OPC/TCPIP_Enable` |

## Logistex (OPC UA) – `LGX_SM_FC` + `Handshake_Infeed_FC`/`Handshake_Outfeed_FC`
- DBs: `DB_Receive_Data_From_Logistex` (J1310/J1320/J1330 `Conv_Infeed`/`Conv_Oufeed`, `CNV_STATUS[]`) e `DB_Send_Data_To_Logistex` (`VTD_J13x0_INFEED/OUTFEED`, `VTD_STATUS[1..6]`, `PLC_STATUS`, `CONV_SPEED`).
- **Infeed** (Cnv1, nível 1): LGX `ReadyToSend` + SM em auto + `Inbound_Ready` + nenhum acesso pedido nos gates do sistema → `SPMReadyToReceive`; fotocélula de parada → `SPMTransferingOccupied` (pallet recebido) e retira o ready; LGX retira `ReadyToSend` sem transferência → retira o ready; `SPMTransferingInProgress := Cnv1.Running`.
- **Outfeed** (Cnv2, nível 1): auto ∧ ocupado ∧ `Outbound_Ready` → `SPMReadyToSend`; esvaziou → retira; `TransferingInProgress := Cnv2.Running`; `Occupied := Cnv_Occupied`; `Pallet_ID[23] := 'U'/'E'` conforme `Pallet_Type` 1/3 (UK/EURO).
- `Fault_Handshake := FALSE` (placeholder – **sem watchdog** de handshake).
- Status para LGX: modo, alarme, ready, pallet ID recebido (`VTD_Status_Update_FC`); light guards e gates (`Remote_Panel_DB_n`); pedido de acesso (`GateAccess_Station_FB_DB_n.CurrentState <> AUTO_RUNNING`); velocidade dos transportadores; `Hardbit := Clock_1Hz`.
- De LGX: `LGX_ReadyToReceive_n` (outfeed em transferência ∧ sem erro), `LGX_Secure_Access_n` (`CNV_STATUS[7]`). O muting das cortinas (`Bypass_FC`) usa `Starting_Pallet_n`, `MR_I/O_n` (atraso 1,5 s) e `Material_Selection` (UK/EURO) a partir dos dados LGX.

## Outras comunicações (iguais ao Marble)
MQTT LMQTT (shuttles), TCP LCom (`Shuttle_TCP_Comms`), heartbeat, SICK CLV6xx (leitor) e AFx60.
