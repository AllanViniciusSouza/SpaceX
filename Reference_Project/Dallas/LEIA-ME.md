# Dallas_Production – arquivo de referência (somente leitura)

Exportado em 19/10/2026 pelo MCP `tia-portal` (TIA Portal V20 Update 6) a partir de
`C:\Users\allan.vinicius\Documents\Automation\Dallas_Production\Dallas_Production.ap20`.
Nada foi alterado no projeto TIA. Projeto de referência – **não compila em TwinCAT**.

## Pastas
| Pasta | Conteúdo |
|---|---|
| `xml/` | Export SimaticML original de cada bloco (fonte fiel; reimportável no TIA) |
| `scl/` | Blocos SCL (FB/FC/OB) convertidos para texto SCL legível |
| `db/`  | DBs globais e de instância: interface + **valores iniciais** (`caminho : tipo := valor`) |
| `lad/` | Blocos LAD/FBD/F-LAD/F-FBD: interface + por network: título, chamadas e operandos (lógica completa só no `xml/`) |
| `udts/PLC_data_types.scl` | Layout dos PLC data types (UDTs) extraído das interfaces dos blocos |
| `tags/` | Tag tables exportadas (SimaticML) |
| `analise/` | Análises e propostas de porte para o SpaceX (TwinCAT) |

## Limitações
- `FOB_RTG1` (OB 123, F-OB gerado pelo Safety) não pode ser exportado pelo Openness.
- UDTs: o MCP não exporta PLC data types diretamente; o layout vem das interfaces dos blocos,
  **sem os comentários dos membros**.
- Blocos LAD/FBD: o resumo em `lad/` lista chamadas e operandos, não a lógica dos contatos.
- Hardware: 28 dispositivos (1 S7-1500 CPU 6ES7 517-3FQ10-0AB0, 3 SCALANCE, 4 W766-1, 19 SINAMICS G120C/G120S, 1 HMI).
  IPs/endereços de I/O não foram retornados pelo MCP.

## Hardware (drives SINAMICS)
| Nome no TIA | Função |
|---|---|
| G_1 / G_2 / G_23 / G_4 | Lift PopUp1 / 2 / 3 / 4 |
| G_7 / G_6 / G_12 / G_9 | Roller PopUp1 / 2 / 3 / 4 |
| G_16 / G_8 / G_11 | Chain1 / Chain2 / Chain3 |
| G_3 / G_5 | Roller Inbound / Roller Outbound |
| G_10 / G_13 / G_14 | Buffer Level1 / 2 / 3 |
| G_19 (G120S) / G_15 | VTD / VTD Conveyor |
| G_18 | Drive_18 (sem função) |

## OB Main (ordem de chamada)
1 Communication (OPC UA, MQTT) · 2 INPUTS · 3 HMI (VTD_HMI_FB, Conveyor_HMI_FB, PopUp_Screens, Screens, FC_Orders) ·
4 Errors · **5 Carousel Conveyors** (InConveyor_FB, OutConveyor_FB, PConveyor_1..4_FB, PickConveyor_FB) ·
6 VTD / Extractor (VTD_FB, EConveyor_FB) · 7 Level conveyors (Buffer_Conveyor_FB ×3) · 8 Safety stoppers ·
9 Encoders · 10 Conveyors_Transfer · 11 Light bars · 12 Barcode … (ver `lad/Main.txt`)

## Índice de blocos
| Bloco | Tipo | Nº | Linguagem | Autor | Arquivo |
|---|---|---|---|---|---|
| Main | OB | 1 | LAD |  | `lad/Main.txt` |
| PullOrPlugOfModules | OB | 83 | LAD |  | `lad/PullOrPlugOfModules.txt` |
| RackOrStationFailure | OB | 86 | LAD |  | `lad/RackOrStationFailure.txt` |
| Barcode_Station_FB | FB | 33 | SCL |  | `scl/Barcode_Station_FB.scl` |
| Buffer_Conveyor_FB | FB | 5 | SCL | Mertin Coetzee | `scl/Buffer_Conveyor_FB.scl` |
| Conveyor_HMI_FB | FB | 13 | SCL |  | `scl/Conveyor_HMI_FB.scl` |
| EConveyor_FB | FB | 12 | SCL | Mertin Coetzee | `scl/EConveyor_FB.scl` |
| FB_HeartBeat | FB | 25 | SCL |  | `scl/FB_HeartBeat.scl` |
| FB_SICK_AFx60_PN | FB | 30 | SCL | SICKAG | `scl/FB_SICK_AFx60_PN.scl` |
| InConveyor_FB | FB | 9 | SCL | Mertin Coetzee | `scl/InConveyor_FB.scl` |
| LCom_Communication | FB | 30300 | SCL | APC_ERLF | `scl/LCom_Communication.scl` |
| Light_Bars | FB | 6 | SCL |  | `scl/Light_Bars.scl` |
| LMQTT_Client | FB | 11 | SCL | Siemens Industry Online Support | `scl/LMQTT_Client.scl` |
| Main_Safety_RTG1 | FB | 1 | F_FBD |  | `lad/Main_Safety_RTG1.txt` |
| MQTT_Handler_FB | FB | 2 | SCL |  | `scl/MQTT_Handler_FB.scl` |
| OPC_UA_Control_FB | FB | 8 | SCL |  | `scl/OPC_UA_Control_FB.scl` |
| OPC_UA_Control_FB_1 | FB | 26 | SCL |  | `scl/OPC_UA_Control_FB_1.scl` |
| Order_Table_FB_Carousel | FB | 32 | SCL |  | `scl/Order_Table_FB_Carousel.scl` |
| Order_Table_FB_Carousel_1 | FB | 34 | SCL |  | `scl/Order_Table_FB_Carousel_1.scl` |
| Order_Table_FB_VTD | FB | 31 | SCL |  | `scl/Order_Table_FB_VTD.scl` |
| OutConveyor_FB | FB | 16 | SCL | Mertin Coetzee | `scl/OutConveyor_FB.scl` |
| PConveyor_1_FB | FB | 15 | SCL | Mertin Coetzee | `scl/PConveyor_1_FB.scl` |
| PConveyor_1_FB_1 | FB | 36 | SCL | Mertin Coetzee | `scl/PConveyor_1_FB_1.scl` |
| PConveyor_2_FB | FB | 20 | SCL | Mertin Coetzee | `scl/PConveyor_2_FB.scl` |
| PConveyor_3_FB | FB | 17 | SCL | Mertin Coetzee | `scl/PConveyor_3_FB.scl` |
| PConveyor_4_FB | FB | 27 | SCL | Mertin Coetzee | `scl/PConveyor_4_FB.scl` |
| PickConveyor_FB | FB | 35 | SCL | Mertin Coetzee | `scl/PickConveyor_FB.scl` |
| Safety_Stops_FB | FB | 7 | SCL |  | `scl/Safety_Stops_FB.scl` |
| SAI_Cyclic_CheckAlive | FB | 28 | LAD |  | `lad/SAI_Cyclic_CheckAlive.txt` |
| SAI_Cyclic_WeightProc | FB | 29 | LAD |  | `lad/SAI_Cyclic_WeightProc.txt` |
| SAI_IND360Base_AlibiRead | FB | 4 | LAD |  | `lad/SAI_IND360Base_AlibiRead.txt` |
| SAI_IND_CalFree | FB | 53 | LAD |  | `lad/SAI_IND_CalFree.txt` |
| SAI_IND_ReadAdjustSettings | FB | 50 | LAD |  | `lad/SAI_IND_ReadAdjustSettings.txt` |
| SAI_IND_SpanAdjust | FB | 55 | LAD |  | `lad/SAI_IND_SpanAdjust.txt` |
| SAI_IND_WriteAdjustSettings | FB | 51 | LAD |  | `lad/SAI_IND_WriteAdjustSettings.txt` |
| SAI_IND_WriteDigitalOutputs | FB | 3 | LAD |  | `lad/SAI_IND_WriteDigitalOutputs.txt` |
| SAI_IND_ZeroAdjust | FB | 52 | LAD |  | `lad/SAI_IND_ZeroAdjust.txt` |
| Shuttle_TCP_Comms_Shuttle1 | FB | 22 | SCL |  | `scl/Shuttle_TCP_Comms_Shuttle1.scl` |
| Shuttle_TCP_Comms_Shuttle2 | FB | 23 | SCL |  | `scl/Shuttle_TCP_Comms_Shuttle2.scl` |
| Shuttle_TCP_Comms_Shuttle3 | FB | 24 | SCL |  | `scl/Shuttle_TCP_Comms_Shuttle3.scl` |
| SICK_Barcode_FB | FB | 19 | SCL |  | `scl/SICK_Barcode_FB.scl` |
| SICK_CCOMM_PNDP | FB | 10 | SCL | SICKAG | `scl/SICK_CCOMM_PNDP.scl` |
| SICK_Lector_CLV6xx_PNDP | FB | 72 | SCL | SICKAG | `scl/SICK_Lector_CLV6xx_PNDP.scl` |
| Stack_Lights | FB | 21 | SCL |  | `scl/Stack_Lights.scl` |
| VTD_FB | FB | 18 | SCL |  | `scl/VTD_FB.scl` |
| VTD_HMI_FB | FB | 14 | SCL |  | `scl/VTD_HMI_FB.scl` |
| ByteArrayToString | FC | 15 | SCL |  | `scl/ByteArrayToString.scl` |
| ByteArrayToString_1 | FC | 23 | SCL |  | `scl/ByteArrayToString_1.scl` |
| CharsArrayToString | FC | 27 | SCL |  | `scl/CharsArrayToString.scl` |
| Conveyors_Transfer | FC | 24 | SCL |  | `scl/Conveyors_Transfer.scl` |
| Encoders | FC | 8 | SCL |  | `scl/Encoders.scl` |
| Errors | FC | 26 | SCL |  | `scl/Errors.scl` |
| FC_CLOCK | FC | 55 | LAD |  | `lad/FC_CLOCK.txt` |
| FC_Orders | FC | 96 | SCL |  | `scl/FC_Orders.scl` |
| FindBoolField | FC | 17 | SCL |  | `scl/FindBoolField.scl` |
| FindDINTFieldFragmented | FC | 20 | SCL |  | `scl/FindDINTFieldFragmented.scl` |
| FindIntField | FC | 18 | SCL |  | `scl/FindIntField.scl` |
| FindINTFieldFragmented | FC | 22 | SCL |  | `scl/FindINTFieldFragmented.scl` |
| FindStringField | FC | 19 | SCL |  | `scl/FindStringField.scl` |
| FindSTRINGFieldFragmented | FC | 21 | SCL |  | `scl/FindSTRINGFieldFragmented.scl` |
| GeneralErros_HMII | FC | 13 | SCL |  | `scl/GeneralErros_HMII.scl` |
| ID_Decode_F | FC | 3 | SCL |  | `scl/ID_Decode_F.scl` |
| INPUTS | FC | 25 | SCL |  | `scl/INPUTS.scl` |
| IsIPAddress | FC | 4 | SCL |  | `scl/IsIPAddress.scl` |
| LMQTT_ConvertToUtf8 | FC | 6 | SCL | SIEMENS | `scl/LMQTT_ConvertToUtf8.scl` |
| Mode_Change_F | FC | 2 | SCL |  | `scl/Mode_Change_F.scl` |
| MT_ACT_Application | FC | 30 | LAD |  | `lad/MT_ACT_Application.txt` |
| OUTPUTS | FC | 5 | SCL |  | `scl/OUTPUTS.scl` |
| ParseShuttle_Status | FC | 16 | SCL |  | `scl/ParseShuttle_Status.scl` |
| PopUp_Screens | FC | 9 | SCL |  | `scl/PopUp_Screens.scl` |
| Profile Station FC | FC | 32 | SCL |  | `scl/Profile Station FC.scl` |
| REMOTE PANEL | FC | 1 | F_LAD |  | `lad/REMOTE PANEL.txt` |
| RemovePlusSign | FC | 14 | SCL |  | `scl/RemovePlusSign.scl` |
| SAI_Copy | FC | 29 | LAD |  | `lad/SAI_Copy.txt` |
| Screens | FC | 12 | SCL |  | `scl/Screens.scl` |
| Set_Bit_F | FC | 7 | SCL |  | `scl/Set_Bit_F.scl` |
| SICK_GetValue | FC | 10 | SCL | SICKAG | `scl/SICK_GetValue.scl` |
| SICK_SetValue | FC | 11 | SCL | SICKAG | `scl/SICK_SetValue.scl` |
| Weighing Station FC | FC | 31 | SCL |  | `scl/Weighing Station FC.scl` |
| Control_DB | GlobalDB | 69 | DB |  | `db/Control_DB.txt` |
| DB_SICK_AFx60_Data | GlobalDB | 120 | DB |  | `db/DB_SICK_AFx60_Data.txt` |
| HMI_DB | GlobalDB | 21 | DB |  | `db/HMI_DB.txt` |
| HMI_OrderTable | GlobalDB | 110 | DB |  | `db/HMI_OrderTable.txt` |
| HMI_Systems | GlobalDB | 137 | DB |  | `db/HMI_Systems.txt` |
| PopUps_DB | GlobalDB | 20 | DB |  | `db/PopUps_DB.txt` |
| SAI_Buffer | GlobalDB | 600 | DB |  | `db/SAI_Buffer.txt` |
| SAI_IND_AlibiData | GlobalDB | 106 | DB |  | `db/SAI_IND_AlibiData.txt` |
| Screen_DB | GlobalDB | 23 | DB |  | `db/Screen_DB.txt` |
| Settings_DB | GlobalDB | 71 | DB |  | `db/Settings_DB.txt` |
| Shuttle_MQTT_DB | GlobalDB | 75 | DB |  | `db/Shuttle_MQTT_DB.txt` |
| SICK_Lector | GlobalDB | 46 | DB |  | `db/SICK_Lector.txt` |
| TCP_IP_DB_Estop_Shuttle1 | GlobalDB | 166 | DB |  | `db/TCP_IP_DB_Estop_Shuttle1.txt` |
| TCP_IP_DB_Estop_Shuttle2 | GlobalDB | 180 | DB |  | `db/TCP_IP_DB_Estop_Shuttle2.txt` |
| TCP_IP_DB_Estop_Shuttle3 | GlobalDB | 184 | DB |  | `db/TCP_IP_DB_Estop_Shuttle3.txt` |
| Time | GlobalDB | 135 | DB |  | `db/Time.txt` |
| Barcode_Inbound_FB_DB | InstanceDB | 115 | DB |  | `db/Barcode_Inbound_FB_DB.txt` |
| Barcode_Outbound_FB_DB | InstanceDB | 142 | DB |  | `db/Barcode_Outbound_FB_DB.txt` |
| Barcode_VTD_FB_DB | InstanceDB | 144 | DB |  | `db/Barcode_VTD_FB_DB.txt` |
| Cnv_L1_FB_DB | InstanceDB | 26 | DB | Mertin Coetzee | `db/Cnv_L1_FB_DB.txt` |
| Cnv_L2_FB_DB | InstanceDB | 27 | DB | Mertin Coetzee | `db/Cnv_L2_FB_DB.txt` |
| Cnv_L3_FB_DB | InstanceDB | 28 | DB | Mertin Coetzee | `db/Cnv_L3_FB_DB.txt` |
| Conveyor_HMI_FB_DB | InstanceDB | 73 | DB |  | `db/Conveyor_HMI_FB_DB.txt` |
| ECnv_FB_DB | InstanceDB | 16 | DB | Mertin Coetzee | `db/ECnv_FB_DB.txt` |
| FB_HeartBeat_DB | InstanceDB | 136 | DB |  | `db/FB_HeartBeat_DB.txt` |
| IDB_SICK_AFx60 | InstanceDB | 121 | DB |  | `db/IDB_SICK_AFx60.txt` |
| Inbound_Cnv_FB_DB | InstanceDB | 30 | DB | Mertin Coetzee | `db/Inbound_Cnv_FB_DB.txt` |
| LCom_Communication_Shuttle1_DB | InstanceDB | 65 | DB | APC_ERLF | `db/LCom_Communication_Shuttle1_DB.txt` |
| LCom_Communication_Shuttle2_DB | InstanceDB | 67 | DB | APC_ERLF | `db/LCom_Communication_Shuttle2_DB.txt` |
| LCom_Communication_Shuttle3_DB | InstanceDB | 79 | DB | APC_ERLF | `db/LCom_Communication_Shuttle3_DB.txt` |
| Light_Bars_DB | InstanceDB | 41 | DB |  | `db/Light_Bars_DB.txt` |
| LMQTT_Client_DB | InstanceDB | 18 | DB | Siemens Industry Online Support | `db/LMQTT_Client_DB.txt` |
| LMQTT_Client_fb | InstanceDB | 42 | DB | Siemens Industry Online Support | `db/LMQTT_Client_fb.txt` |
| LMQTT_DB | InstanceDB | 43 | DB |  | `db/LMQTT_DB.txt` |
| Main_Safety_RTG1_DB | InstanceDB | 1 | F_DB |  | `db/Main_Safety_RTG1_DB.txt` |
| MB_Device_Status | InstanceDB | 119 | DB |  | `db/MB_Device_Status.txt` |
| MQTT_Handler_FB_DB | InstanceDB | 44 | DB |  | `db/MQTT_Handler_FB_DB.txt` |
| OPC_UA_Control_FB_DB | InstanceDB | 17 | DB |  | `db/OPC_UA_Control_FB_DB.txt` |
| Order_Table_FB_Carousel_DB | InstanceDB | 138 | DB |  | `db/Order_Table_FB_Carousel_DB.txt` |
| Order_Table_FB_VTD_DB | InstanceDB | 139 | DB |  | `db/Order_Table_FB_VTD_DB.txt` |
| Outbound_Cnv_FB_DB | InstanceDB | 6 | DB | Mertin Coetzee | `db/Outbound_Cnv_FB_DB.txt` |
| PConveyor_1_FB_DB | InstanceDB | 13 | DB | Mertin Coetzee | `db/PConveyor_1_FB_DB.txt` |
| PConveyor_2_FB_DB | InstanceDB | 83 | DB | Mertin Coetzee | `db/PConveyor_2_FB_DB.txt` |
| PConveyor_3_FB_DB | InstanceDB | 88 | DB | Mertin Coetzee | `db/PConveyor_3_FB_DB.txt` |
| PConveyor_4_FB_DB | InstanceDB | 89 | DB | Mertin Coetzee | `db/PConveyor_4_FB_DB.txt` |
| PickConveyor_FB_DB | InstanceDB | 151 | DB | Mertin Coetzee | `db/PickConveyor_FB_DB.txt` |
| Profile_Station_DB | InstanceDB | 130 | DB |  | `db/Profile_Station_DB.txt` |
| SAI_Cyclic_CheckAlive_DB | InstanceDB | 12 | DB |  | `db/SAI_Cyclic_CheckAlive_DB.txt` |
| SAI_Cyclic_WeightProc_DB | InstanceDB | 29 | DB |  | `db/SAI_Cyclic_WeightProc_DB.txt` |
| SAI_IND_AlibiRead_DB | InstanceDB | 107 | DB |  | `db/SAI_IND_AlibiRead_DB.txt` |
| SAI_IND_CalFree_DB | InstanceDB | 112 | DB |  | `db/SAI_IND_CalFree_DB.txt` |
| SAI_IND_ReadAdjustSettings_DB | InstanceDB | 108 | DB |  | `db/SAI_IND_ReadAdjustSettings_DB.txt` |
| SAI_IND_SpanAdjust_DB | InstanceDB | 113 | DB |  | `db/SAI_IND_SpanAdjust_DB.txt` |
| SAI_IND_WriteAdjustSettings_DB | InstanceDB | 109 | DB |  | `db/SAI_IND_WriteAdjustSettings_DB.txt` |
| SAI_IND_ZeroAdjust_DB | InstanceDB | 111 | DB |  | `db/SAI_IND_ZeroAdjust_DB.txt` |
| SB_Alarm | InstanceDB | 118 | DB |  | `db/SB_Alarm.txt` |
| SB_RedAlarm | InstanceDB | 117 | DB |  | `db/SB_RedAlarm.txt` |
| Sf_L1_FB_DB | InstanceDB | 55 | DB |  | `db/Sf_L1_FB_DB.txt` |
| Sf_L2_FB_DB | InstanceDB | 56 | DB |  | `db/Sf_L2_FB_DB.txt` |
| Sf_L3_FB_DB | InstanceDB | 68 | DB |  | `db/Sf_L3_FB_DB.txt` |
| SICK_Barcode_DB | InstanceDB | 47 | DB |  | `db/SICK_Barcode_DB.txt` |
| SICK_Lector_DB | InstanceDB | 45 | DB | SICKAG | `db/SICK_Lector_DB.txt` |
| Stack_Lights_DB | InstanceDB | 62 | DB |  | `db/Stack_Lights_DB.txt` |
| System_DB | InstanceDB | 74 | DB |  | `db/System_DB.txt` |
| System_DB_Carousel | InstanceDB | 122 | DB |  | `db/System_DB_Carousel.txt` |
| System_DB_VTD | InstanceDB | 128 | DB |  | `db/System_DB_VTD.txt` |
| System_Unit_1 | InstanceDB | 131 | DB |  | `db/System_Unit_1.txt` |
| System_Unit_2 | InstanceDB | 132 | DB |  | `db/System_Unit_2.txt` |
| TCP_Comms_Shuttle1_DB | InstanceDB | 64 | DB |  | `db/TCP_Comms_Shuttle1_DB.txt` |
| TCP_Comms_Shuttle2_DB | InstanceDB | 66 | DB |  | `db/TCP_Comms_Shuttle2_DB.txt` |
| TCP_Comms_Shuttle3_DB | InstanceDB | 76 | DB |  | `db/TCP_Comms_Shuttle3_DB.txt` |
| VTD_FB_DB | InstanceDB | 25 | DB |  | `db/VTD_FB_DB.txt` |
| VTD_HMI_FB_DB | InstanceDB | 22 | DB |  | `db/VTD_HMI_FB_DB.txt` |
| Watchdog_Settings | InstanceDB | 134 | DB |  | `db/Watchdog_Settings.txt` |
| Weigh_Station_DB | InstanceDB | 129 | DB |  | `db/Weigh_Station_DB.txt` |

Total: FB 43, FC 33, GlobalDB 16, InstanceDB 59, OB 3 = 154 blocos exportados (+ FOB_RTG1 não exportável).
