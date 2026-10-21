# Marble_Engineering – arquivo de referência (somente leitura)

Exportado em 19/10/2026 pelo MCP `tia-portal` (TIA Portal V20) a partir de
`C:\ParkplusDev\Marble_Engineering\Marble_Engineering.ap20` (autor allan.vinicius, modificado 15/10/2026).
Nada foi alterado no projeto TIA. Projeto de referência – **não compila em TwinCAT**.

**Por que esta referência:** é a versão de **2 sistemas** do mesmo código-base do Yusan (base da migração SpaceX).
`Control_DB` tem o mesmo layout que o SpaceX herdou (`ECnv_Sys/LCnv_Sys/VTD_Sys[1..2]`, `Charger_Level[2..6]`,
`Gate_Station`, `VTDBarcode_Station`, `VTD_Order Table`, `Buffer_Order Table`) e traz blocos que faltavam
(`Feed_VTD_HMI_FC`, `Feed_ECNV`, `CNV_Selector`, `HMI_SAFETY_FC`, `F_Lock_FB`, `Bypass assignments`, `Remote_Panel` em XML).

## Pastas
| Pasta | Conteúdo |
|---|---|
| `xml/` | Export SimaticML original de cada bloco (fonte fiel; reimportável no TIA) – 252 blocos |
| `scl/` | Blocos SCL (FB/FC/OB) convertidos para texto legível – 73 |
| `db/`  | DBs globais e de instância: interface + valores iniciais (`caminho : tipo := valor`) – 169 |
| `lad/` | Blocos LAD/FBD/F-LAD/F-FBD: interface + por network título, chamadas e operandos (lógica completa só no `xml/`) – 10 |
| `udts/PLC_data_types.scl` | Layout de 52 UDTs extraído das interfaces (sem comentários de membros; os SCL do Yusan em `Reference_Project/*.scl` trazem os UDTs comentados) |
| `tags/` | 28 tag tables (SimaticML) |
| `PLC_HMI_1200/` | S7-1200 "PLC_HMI": Main, Main_Safety_RTG1 (vazios) e DB |
| `analise/` | `IO_Hardware.md`, `Maquina.md`, `Pedidos_HMI_Comunicacao.md`, `Seguranca.md` |

Conversor: `tools/tia_export_to_text.py` (`python3 -I tools/tia_export_to_text.py Reference_Project/Marble`).

## Não exportado (Openness recusou)
| Bloco | Motivo |
|---|---|
| `Main` (OB1, LAD) | Inconsistente – compilar o projeto no TIA (Ctrl+B) e exportar de novo. Ordem de chamada provável: ver `Reference_Project/MAIN.pdf` (Yusan) |
| `HMI` (OB123, SCL) | Export recusado |
| `Errors_Warings` (FC26) | Inconsistente (a versão Yusan está em `Reference_Project/Errors_Warings.scl`) |
| `OPC_Control_FB_DB_1/_2` | Inconsistentes |
| `ProDiagOB`, `Default_SupervisionFB` | ProDiag |
| `FOB_RTG1` (1500 e 1200) | F-OB gerado pelo Safety |

## Limitações
- ~~O conversor perdia constantes locais~~ – corrigido em 20/10 e o Marble foi reconvertido (constantes aparecem pelo nome, ex. `#AUTO_RUNNING`).
- Versão mais nova do mesmo código: `../Yusan/` (20/10) – ver `../Yusan/analise/Comparativo_Marble_SpaceX.md`.
- Hardware: o MCP não retorna IPs nem endereços de módulos; os G120 dos transportadores não aparecem como dispositivos (só pelas tags).
- HMI_1/HMI_2 são WinCC Comfort/Advanced – o MCP só lê telas Unified.

## Índice de blocos
| Bloco | Tipo | Nº | Linguagem | Autor | Arquivo |
|---|---|---|---|---|---|
| PullOrPlugOfModules | OB | 83 | LAD |  | `lad/PullOrPlugOfModules.txt` |
| RackOrStationFailure | OB | 86 | LAD |  | `lad/RackOrStationFailure.txt` |
| Auto_Test | FB | 16 | SCL |  | `scl/Auto_Test.scl` |
| Barcode_Station_FB | FB | 33 | SCL |  | `scl/Barcode_Station_FB.scl` |
| Buffer_Conveyor_FB | FB | 5 | SCL | Mertin Coetzee | `scl/Buffer_Conveyor_FB.scl` |
| Conveyor_HMI_FB | FB | 20 | SCL |  | `scl/Conveyor_HMI_FB.scl` |
| Conveyor_HMI_FB_1 | FB | 13 | SCL |  | `scl/Conveyor_HMI_FB_1.scl` |
| EConveyor_FB | FB | 12 | SCL | Mertin Coetzee | `scl/EConveyor_FB.scl` |
| F_Lock_FB | FB | 24 | F_FBD |  | `lad/F_Lock_FB.txt` |
| FB_HeartBeat | FB | 25 | SCL |  | `scl/FB_HeartBeat.scl` |
| FB_SICK_AFx60_PN | FB | 30 | SCL | SICKAG | `scl/FB_SICK_AFx60_PN.scl` |
| GateAccess_Station_FB | FB | 26 | SCL |  | `scl/GateAccess_Station_FB.scl` |
| GateAccessControl_FB | FB | 23 | SCL |  | `scl/GateAccessControl_FB.scl` |
| LCom_Communication_FB | FB | 30300 | SCL | APC_ERLF | `scl/LCom_Communication_FB.scl` |
| Light_Bars | FB | 6 | SCL |  | `scl/Light_Bars.scl` |
| LMQTT_Client | FB | 11 | SCL | Siemens Industry Online Support | `scl/LMQTT_Client.scl` |
| Main_Safety_RTG1 | FB | 1 | F_FBD |  | `lad/Main_Safety_RTG1.txt` |
| ModeManager_FB | FB | 8 | SCL |  | `scl/ModeManager_FB.scl` |
| MQTT_Handler_FB | FB | 2 | SCL |  | `scl/MQTT_Handler_FB.scl` |
| OPC_Control_FB | FB | 9 | SCL |  | `scl/OPC_Control_FB.scl` |
| Order_Table_Buffers_FB | FB | 31 | SCL |  | `scl/Order_Table_Buffers_FB.scl` |
| Order_Table_VTD_FB | FB | 32 | SCL |  | `scl/Order_Table_VTD_FB.scl` |
| Remote_Panel | FB | 17 | F_LAD |  | `lad/Remote_Panel.txt` |
| Safety_Stops_FB | FB | 7 | SCL |  | `scl/Safety_Stops_FB.scl` |
| Shuttle_TCP_Comms | FB | 22 | SCL |  | `scl/Shuttle_TCP_Comms.scl` |
| SICK Safe Entry Exit HW PLC V02 | FB | 1000 | F_FBD | 2/29SD | `lad/SICK Safe Entry Exit HW PLC V02.txt` |
| SICK_CCOMM_PNDP | FB | 10 | SCL | SICKAG | `scl/SICK_CCOMM_PNDP.scl` |
| SICK_Lector_CLV6xx_PNDP | FB | 72 | SCL | SICKAG | `scl/SICK_Lector_CLV6xx_PNDP.scl` |
| SICK_Lector_Control_FB | FB | 19 | SCL |  | `scl/SICK_Lector_Control_FB.scl` |
| Stack_Lights_FB | FB | 21 | SCL |  | `scl/Stack_Lights_FB.scl` |
| VTD_FB | FB | 18 | SCL |  | `scl/VTD_FB.scl` |
| VTD_HMI_FB | FB | 14 | SCL |  | `scl/VTD_HMI_FB.scl` |
| VTD_HMI_FB_1 | FB | 15 | SCL |  | `scl/VTD_HMI_FB_1.scl` |
| Bypass assignments_1 | FC | 35 | F_LAD |  | `lad/Bypass assignments_1.txt` |
| Bypass assignments_2 | FC | 36 | F_LAD |  | `lad/Bypass assignments_2.txt` |
| Bypass_FC | FC | 62 | SCL |  | `scl/Bypass_FC.scl` |
| ByteArrayToString | FC | 15 | SCL |  | `scl/ByteArrayToString.scl` |
| ByteArrayToString_1 | FC | 23 | SCL |  | `scl/ByteArrayToString_1.scl` |
| CharsArrayToString | FC | 27 | SCL |  | `scl/CharsArrayToString.scl` |
| CNV_Charge_Settings_FC | FC | 42 | SCL |  | `scl/CNV_Charge_Settings_FC.scl` |
| CNV_Charge_Settings_FC_1 | FC | 59 | SCL |  | `scl/CNV_Charge_Settings_FC_1.scl` |
| CNV_Order_FC | FC | 46 | SCL |  | `scl/CNV_Order_FC.scl` |
| CNV_Selector | FC | 8 | SCL |  | `scl/CNV_Selector.scl` |
| CNV_Selector_1 | FC | 60 | SCL |  | `scl/CNV_Selector_1.scl` |
| Conveyors_Transfer | FC | 24 | SCL |  | `scl/Conveyors_Transfer.scl` |
| FC_CLOCK | FC | 55 | LAD |  | `lad/FC_CLOCK.txt` |
| FC_Orders | FC | 96 | SCL |  | `scl/FC_Orders.scl` |
| FC_Orders_1 | FC | 97 | SCL |  | `scl/FC_Orders_1.scl` |
| Feed_BCNV_Cnv1(1) | FC | 54 | SCL |  | `scl/Feed_BCNV_Cnv1(1).scl` |
| Feed_BCNV_Cnv1(1)_1 | FC | 56 | SCL |  | `scl/Feed_BCNV_Cnv1(1)_1.scl` |
| Feed_BCNV_Cnv2 | FC | 28 | SCL |  | `scl/Feed_BCNV_Cnv2.scl` |
| Feed_BCNV_Cnv2_1 | FC | 30 | SCL |  | `scl/Feed_BCNV_Cnv2_1.scl` |
| Feed_ECNV | FC | 1 | SCL |  | `scl/Feed_ECNV.scl` |
| Feed_ECNV_1 | FC | 53 | SCL |  | `scl/Feed_ECNV_1.scl` |
| Feed_Steptable_FC | FC | 44 | SCL |  | `scl/Feed_Steptable_FC.scl` |
| Feed_VTD_HMI_FC | FC | 33 | SCL |  | `scl/Feed_VTD_HMI_FC.scl` |
| Feed_VTD_HMI_FC_1 | FC | 57 | SCL |  | `scl/Feed_VTD_HMI_FC_1.scl` |
| FindBoolField | FC | 17 | SCL |  | `scl/FindBoolField.scl` |
| FindDINTFieldFragmented | FC | 20 | SCL |  | `scl/FindDINTFieldFragmented.scl` |
| FindIntField | FC | 18 | SCL |  | `scl/FindIntField.scl` |
| FindINTFieldFragmented | FC | 22 | SCL |  | `scl/FindINTFieldFragmented.scl` |
| FindStringField | FC | 19 | SCL |  | `scl/FindStringField.scl` |
| FindSTRINGFieldFragmented | FC | 21 | SCL |  | `scl/FindSTRINGFieldFragmented.scl` |
| HMI_SAFETY_FC | FC | 43 | F_FBD |  | `lad/HMI_SAFETY_FC.txt` |
| ID_Decode_F | FC | 3 | SCL |  | `scl/ID_Decode_F.scl` |
| INPUTS | FC | 25 | SCL |  | `scl/INPUTS.scl` |
| IsIPAddress | FC | 4 | SCL |  | `scl/IsIPAddress.scl` |
| LMQTT_ConvertToUtf8 | FC | 6 | SCL | SIEMENS | `scl/LMQTT_ConvertToUtf8.scl` |
| OT_Charge_Commands | FC | 52 | SCL |  | `scl/OT_Charge_Commands.scl` |
| OUTPUTS | FC | 5 | SCL |  | `scl/OUTPUTS.scl` |
| ParseShuttle_Status | FC | 16 | SCL |  | `scl/ParseShuttle_Status.scl` |
| PopUp_Screens | FC | 9 | SCL |  | `scl/PopUp_Screens.scl` |
| PopUp_Screens_2 | FC | 63 | SCL |  | `scl/PopUp_Screens_2.scl` |
| RemovePlusSign | FC | 14 | SCL |  | `scl/RemovePlusSign.scl` |
| Screens | FC | 12 | SCL |  | `scl/Screens.scl` |
| Screens_2 | FC | 61 | SCL |  | `scl/Screens_2.scl` |
| Set_Bit_F | FC | 7 | SCL |  | `scl/Set_Bit_F.scl` |
| Settings_Limits_FC | FC | 65 | SCL |  | `scl/Settings_Limits_FC.scl` |
| SICK_GetValue | FC | 10 | SCL | SICKAG | `scl/SICK_GetValue.scl` |
| SICK_SetValue | FC | 11 | SCL | SICKAG | `scl/SICK_SetValue.scl` |
| VTD_Charge_Settings | FC | 41 | SCL |  | `scl/VTD_Charge_Settings.scl` |
| VTD_Charge_Settings_1 | FC | 58 | SCL |  | `scl/VTD_Charge_Settings_1.scl` |
| VTD_Order_FC | FC | 45 | SCL |  | `scl/VTD_Order_FC.scl` |
| Bypass | GlobalDB | 9 | DB |  | `db/Bypass.txt` |
| Bypass_Safe | GlobalDB | 39 | F_DB |  | `db/Bypass_Safe.txt` |
| CNV_HMI | GlobalDB | 40 | DB |  | `db/CNV_HMI.txt` |
| Control_DB | GlobalDB | 69 | DB |  | `db/Control_DB.txt` |
| Force | GlobalDB | 12 | DB |  | `db/Force.txt` |
| HMI_DB | GlobalDB | 21 | DB |  | `db/HMI_DB.txt` |
| HMI_OrderTable | GlobalDB | 110 | DB |  | `db/HMI_OrderTable.txt` |
| HMI_OrderTable_1 | GlobalDB | 137 | DB |  | `db/HMI_OrderTable_1.txt` |
| OrderTable_HMI | GlobalDB | 96 | DB |  | `db/OrderTable_HMI.txt` |
| OrderTable_HMI_1 | GlobalDB | 99 | DB |  | `db/OrderTable_HMI_1.txt` |
| PopUp_Screens_1 | GlobalDB | 51 | DB |  | `db/PopUp_Screens_1.txt` |
| PopUps_DB | GlobalDB | 38 | DB |  | `db/PopUps_DB.txt` |
| PopUps_DB_1 | GlobalDB | 20 | DB |  | `db/PopUps_DB_1.txt` |
| Screen_DB | GlobalDB | 23 | DB |  | `db/Screen_DB.txt` |
| Screen_DB_1 | GlobalDB | 54 | DB |  | `db/Screen_DB_1.txt` |
| Settings_DB | GlobalDB | 71 | DB |  | `db/Settings_DB.txt` |
| Shuttle_MQTT_DB | GlobalDB | 75 | DB |  | `db/Shuttle_MQTT_DB.txt` |
| SICK_AFx60_Data_DB | GlobalDB | 120 | DB |  | `db/SICK_AFx60_Data_DB.txt` |
| SICK_Lector_DB_1 | GlobalDB | 46 | DB |  | `db/SICK_Lector_DB_1.txt` |
| SICK_Lector_DB_2 | GlobalDB | 309 | DB |  | `db/SICK_Lector_DB_2.txt` |
| TCP_IP_Shuttle_DB_1 | GlobalDB | 391 | DB |  | `db/TCP_IP_Shuttle_DB_1.txt` |
| TCP_IP_Shuttle_DB_10 | GlobalDB | 384 | DB |  | `db/TCP_IP_Shuttle_DB_10.txt` |
| TCP_IP_Shuttle_DB_2 | GlobalDB | 305 | DB |  | `db/TCP_IP_Shuttle_DB_2.txt` |
| TCP_IP_Shuttle_DB_3 | GlobalDB | 388 | DB |  | `db/TCP_IP_Shuttle_DB_3.txt` |
| TCP_IP_Shuttle_DB_4 | GlobalDB | 375 | DB |  | `db/TCP_IP_Shuttle_DB_4.txt` |
| TCP_IP_Shuttle_DB_5 | GlobalDB | 376 | DB |  | `db/TCP_IP_Shuttle_DB_5.txt` |
| TCP_IP_Shuttle_DB_6 | GlobalDB | 377 | DB |  | `db/TCP_IP_Shuttle_DB_6.txt` |
| TCP_IP_Shuttle_DB_7 | GlobalDB | 374 | DB |  | `db/TCP_IP_Shuttle_DB_7.txt` |
| TCP_IP_Shuttle_DB_8 | GlobalDB | 380 | DB |  | `db/TCP_IP_Shuttle_DB_8.txt` |
| TCP_IP_Shuttle_DB_9 | GlobalDB | 383 | DB |  | `db/TCP_IP_Shuttle_DB_9.txt` |
| Time | GlobalDB | 135 | DB |  | `db/Time.txt` |
| VTD_HMI | GlobalDB | 57 | DB |  | `db/VTD_HMI.txt` |
| Auto_Test_1_DB | InstanceDB | 4 | DB |  | `db/Auto_Test_1_DB.txt` |
| Auto_Test_2_DB | InstanceDB | 118 | DB |  | `db/Auto_Test_2_DB.txt` |
| Auto_Test_DB | InstanceDB | 24 | DB |  | `db/Auto_Test_DB.txt` |
| Barcode_FB_DB_1 | InstanceDB | 144 | DB |  | `db/Barcode_FB_DB_1.txt` |
| Barcode_FB_DB_2 | InstanceDB | 331 | DB |  | `db/Barcode_FB_DB_2.txt` |
| C1102_FB_DB | InstanceDB | 123 | DB | Mertin Coetzee | `db/C1102_FB_DB.txt` |
| C1103_FB_DB | InstanceDB | 109 | DB | Mertin Coetzee | `db/C1103_FB_DB.txt` |
| C1104_FB_DB | InstanceDB | 111 | DB | Mertin Coetzee | `db/C1104_FB_DB.txt` |
| C1105_FB_DB | InstanceDB | 105 | DB | Mertin Coetzee | `db/C1105_FB_DB.txt` |
| C1106_FB_DB | InstanceDB | 113 | DB | Mertin Coetzee | `db/C1106_FB_DB.txt` |
| C1202_FB_DB | InstanceDB | 106 | DB | Mertin Coetzee | `db/C1202_FB_DB.txt` |
| C1203_FB_DB | InstanceDB | 116 | DB | Mertin Coetzee | `db/C1203_FB_DB.txt` |
| C1204_FB_DB | InstanceDB | 107 | DB | Mertin Coetzee | `db/C1204_FB_DB.txt` |
| C1205_FB_DB | InstanceDB | 114 | DB | Mertin Coetzee | `db/C1205_FB_DB.txt` |
| C1206_FB_DB | InstanceDB | 26 | DB | Mertin Coetzee | `db/C1206_FB_DB.txt` |
| C2102_FB_DB | InstanceDB | 146 | DB | Mertin Coetzee | `db/C2102_FB_DB.txt` |
| C2103_FB_DB | InstanceDB | 103 | DB | Mertin Coetzee | `db/C2103_FB_DB.txt` |
| C2104_FB_DB | InstanceDB | 101 | DB | Mertin Coetzee | `db/C2104_FB_DB.txt` |
| C2105_FB_DB | InstanceDB | 77 | DB | Mertin Coetzee | `db/C2105_FB_DB.txt` |
| C2106_FB_DB | InstanceDB | 148 | DB | Mertin Coetzee | `db/C2106_FB_DB.txt` |
| C2202_FB_DB | InstanceDB | 72 | DB | Mertin Coetzee | `db/C2202_FB_DB.txt` |
| C2203_FB_DB | InstanceDB | 70 | DB | Mertin Coetzee | `db/C2203_FB_DB.txt` |
| C2204_FB_DB | InstanceDB | 27 | DB | Mertin Coetzee | `db/C2204_FB_DB.txt` |
| C2205_FB_DB | InstanceDB | 149 | DB | Mertin Coetzee | `db/C2205_FB_DB.txt` |
| C2206_FB_DB | InstanceDB | 147 | DB | Mertin Coetzee | `db/C2206_FB_DB.txt` |
| Conveyor_HMI_FB_1_DB | InstanceDB | 15 | DB |  | `db/Conveyor_HMI_FB_1_DB.txt` |
| Conveyor_HMI_FB_2_DB | InstanceDB | 50 | DB |  | `db/Conveyor_HMI_FB_2_DB.txt` |
| Conveyor_HMI_FB_DB | InstanceDB | 73 | DB |  | `db/Conveyor_HMI_FB_DB.txt` |
| Default_SupervisionDB | InstanceDB | 2 | DB |  | `db/Default_SupervisionDB.txt` |
| ECnv_FB_DB_1 | InstanceDB | 14 | DB | Mertin Coetzee | `db/ECnv_FB_DB_1.txt` |
| ECnv_FB_DB_2 | InstanceDB | 13 | DB | Mertin Coetzee | `db/ECnv_FB_DB_2.txt` |
| F_Lock_FB_DB_1 | InstanceDB | 411 | F_DB |  | `db/F_Lock_FB_DB_1.txt` |
| F_Lock_FB_DB_2 | InstanceDB | 412 | F_DB |  | `db/F_Lock_FB_DB_2.txt` |
| F_Lock_FB_DB_3 | InstanceDB | 416 | F_DB |  | `db/F_Lock_FB_DB_3.txt` |
| FB_HeartBeat_DB | InstanceDB | 136 | DB |  | `db/FB_HeartBeat_DB.txt` |
| GateAccess_Station_FB_DB_1 | InstanceDB | 425 | DB |  | `db/GateAccess_Station_FB_DB_1.txt` |
| GateAccess_Station_FB_DB_2 | InstanceDB | 426 | DB |  | `db/GateAccess_Station_FB_DB_2.txt` |
| GateAccess_Station_FB_DB_3 | InstanceDB | 427 | DB |  | `db/GateAccess_Station_FB_DB_3.txt` |
| LCom_Comm_Shuttle_FB_DB_1 | InstanceDB | 65 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_1.txt` |
| LCom_Comm_Shuttle_FB_DB_10 | InstanceDB | 359 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_10.txt` |
| LCom_Comm_Shuttle_FB_DB_11 | InstanceDB | 358 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_11.txt` |
| LCom_Comm_Shuttle_FB_DB_12 | InstanceDB | 371 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_12.txt` |
| LCom_Comm_Shuttle_FB_DB_13 | InstanceDB | 356 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_13.txt` |
| LCom_Comm_Shuttle_FB_DB_14 | InstanceDB | 354 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_14.txt` |
| LCom_Comm_Shuttle_FB_DB_15 | InstanceDB | 373 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_15.txt` |
| LCom_Comm_Shuttle_FB_DB_16 | InstanceDB | 351 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_16.txt` |
| LCom_Comm_Shuttle_FB_DB_17 | InstanceDB | 352 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_17.txt` |
| LCom_Comm_Shuttle_FB_DB_18 | InstanceDB | 353 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_18.txt` |
| LCom_Comm_Shuttle_FB_DB_19 | InstanceDB | 368 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_19.txt` |
| LCom_Comm_Shuttle_FB_DB_2 | InstanceDB | 370 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_2.txt` |
| LCom_Comm_Shuttle_FB_DB_20 | InstanceDB | 372 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_20.txt` |
| LCom_Comm_Shuttle_FB_DB_21 | InstanceDB | 369 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_21.txt` |
| LCom_Comm_Shuttle_FB_DB_22 | InstanceDB | 365 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_22.txt` |
| LCom_Comm_Shuttle_FB_DB_23 | InstanceDB | 366 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_23.txt` |
| LCom_Comm_Shuttle_FB_DB_24 | InstanceDB | 355 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_24.txt` |
| LCom_Comm_Shuttle_FB_DB_3 | InstanceDB | 357 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_3.txt` |
| LCom_Comm_Shuttle_FB_DB_4 | InstanceDB | 367 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_4.txt` |
| LCom_Comm_Shuttle_FB_DB_5 | InstanceDB | 364 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_5.txt` |
| LCom_Comm_Shuttle_FB_DB_6 | InstanceDB | 363 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_6.txt` |
| LCom_Comm_Shuttle_FB_DB_7 | InstanceDB | 362 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_7.txt` |
| LCom_Comm_Shuttle_FB_DB_8 | InstanceDB | 361 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_8.txt` |
| LCom_Comm_Shuttle_FB_DB_9 | InstanceDB | 360 | DB | APC_ERLF | `db/LCom_Comm_Shuttle_FB_DB_9.txt` |
| Light_Bars_DB_1 | InstanceDB | 235 | DB |  | `db/Light_Bars_DB_1.txt` |
| Light_Bars_DB_2 | InstanceDB | 41 | DB |  | `db/Light_Bars_DB_2.txt` |
| LMQTT_Client_DB | InstanceDB | 158 | DB | Siemens Industry Online Support | `db/LMQTT_Client_DB.txt` |
| LMQTT_Client_fb | InstanceDB | 42 | DB | Siemens Industry Online Support | `db/LMQTT_Client_fb.txt` |
| LMQTT_DB | InstanceDB | 43 | DB |  | `db/LMQTT_DB.txt` |
| Main_Safety_RTG1_DB | InstanceDB | 1 | F_DB |  | `db/Main_Safety_RTG1_DB.txt` |
| MQTT_Handler_FB_DB | InstanceDB | 44 | DB |  | `db/MQTT_Handler_FB_DB.txt` |
| Order_Table_Buffers_FB_DB_1 | InstanceDB | 18 | DB |  | `db/Order_Table_Buffers_FB_DB_1.txt` |
| Order_Table_Buffers_FB_DB_2 | InstanceDB | 19 | DB |  | `db/Order_Table_Buffers_FB_DB_2.txt` |
| Order_Table_VTD_FB_DB_1 | InstanceDB | 6 | DB |  | `db/Order_Table_VTD_FB_DB_1.txt` |
| Order_Table_VTD_FB_DB_2 | InstanceDB | 11 | DB |  | `db/Order_Table_VTD_FB_DB_2.txt` |
| Remote_Panel_DB_1 | InstanceDB | 8 | F_DB |  | `db/Remote_Panel_DB_1.txt` |
| Remote_Panel_DB_2 | InstanceDB | 10 | F_DB |  | `db/Remote_Panel_DB_2.txt` |
| Sf_C1102_FB_DB | InstanceDB | 253 | DB |  | `db/Sf_C1102_FB_DB.txt` |
| Sf_C1103_FB_DB | InstanceDB | 250 | DB |  | `db/Sf_C1103_FB_DB.txt` |
| Sf_C1104_FB_DB | InstanceDB | 249 | DB |  | `db/Sf_C1104_FB_DB.txt` |
| Sf_C1105_FB_DB | InstanceDB | 245 | DB |  | `db/Sf_C1105_FB_DB.txt` |
| Sf_C1106_FB_DB | InstanceDB | 246 | DB |  | `db/Sf_C1106_FB_DB.txt` |
| Sf_C1202_FB_DB | InstanceDB | 251 | DB |  | `db/Sf_C1202_FB_DB.txt` |
| Sf_C1203_FB_DB | InstanceDB | 55 | DB |  | `db/Sf_C1203_FB_DB.txt` |
| Sf_C1204_FB_DB | InstanceDB | 244 | DB |  | `db/Sf_C1204_FB_DB.txt` |
| Sf_C1205_FB_DB | InstanceDB | 254 | DB |  | `db/Sf_C1205_FB_DB.txt` |
| Sf_C1206_FB_DB | InstanceDB | 255 | DB |  | `db/Sf_C1206_FB_DB.txt` |
| Sf_C2102_FB_DB | InstanceDB | 303 | DB |  | `db/Sf_C2102_FB_DB.txt` |
| Sf_C2103_FB_DB | InstanceDB | 259 | DB |  | `db/Sf_C2103_FB_DB.txt` |
| Sf_C2104_FB_DB | InstanceDB | 304 | DB |  | `db/Sf_C2104_FB_DB.txt` |
| Sf_C2105_FB_DB | InstanceDB | 284 | DB |  | `db/Sf_C2105_FB_DB.txt` |
| Sf_C2106_FB_DB | InstanceDB | 286 | DB |  | `db/Sf_C2106_FB_DB.txt` |
| Sf_C2202_FB_DB | InstanceDB | 295 | DB |  | `db/Sf_C2202_FB_DB.txt` |
| Sf_C2203_FB_DB | InstanceDB | 285 | DB |  | `db/Sf_C2203_FB_DB.txt` |
| Sf_C2204_FB_DB | InstanceDB | 288 | DB |  | `db/Sf_C2204_FB_DB.txt` |
| Sf_C2205_FB_DB | InstanceDB | 299 | DB |  | `db/Sf_C2205_FB_DB.txt` |
| Sf_C2206_FB_DB | InstanceDB | 283 | DB |  | `db/Sf_C2206_FB_DB.txt` |
| Shuttle_TCP_Comms_FB_DB_1 | InstanceDB | 64 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_1.txt` |
| Shuttle_TCP_Comms_FB_DB_10 | InstanceDB | 344 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_10.txt` |
| Shuttle_TCP_Comms_FB_DB_11 | InstanceDB | 345 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_11.txt` |
| Shuttle_TCP_Comms_FB_DB_12 | InstanceDB | 346 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_12.txt` |
| Shuttle_TCP_Comms_FB_DB_13 | InstanceDB | 347 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_13.txt` |
| Shuttle_TCP_Comms_FB_DB_14 | InstanceDB | 348 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_14.txt` |
| Shuttle_TCP_Comms_FB_DB_15 | InstanceDB | 336 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_15.txt` |
| Shuttle_TCP_Comms_FB_DB_16 | InstanceDB | 180 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_16.txt` |
| Shuttle_TCP_Comms_FB_DB_17 | InstanceDB | 350 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_17.txt` |
| Shuttle_TCP_Comms_FB_DB_18 | InstanceDB | 184 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_18.txt` |
| Shuttle_TCP_Comms_FB_DB_19 | InstanceDB | 66 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_19.txt` |
| Shuttle_TCP_Comms_FB_DB_2 | InstanceDB | 340 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_2.txt` |
| Shuttle_TCP_Comms_FB_DB_20 | InstanceDB | 141 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_20.txt` |
| Shuttle_TCP_Comms_FB_DB_21 | InstanceDB | 76 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_21.txt` |
| Shuttle_TCP_Comms_FB_DB_22 | InstanceDB | 79 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_22.txt` |
| Shuttle_TCP_Comms_FB_DB_23 | InstanceDB | 132 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_23.txt` |
| Shuttle_TCP_Comms_FB_DB_24 | InstanceDB | 67 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_24.txt` |
| Shuttle_TCP_Comms_FB_DB_3 | InstanceDB | 339 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_3.txt` |
| Shuttle_TCP_Comms_FB_DB_4 | InstanceDB | 343 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_4.txt` |
| Shuttle_TCP_Comms_FB_DB_5 | InstanceDB | 342 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_5.txt` |
| Shuttle_TCP_Comms_FB_DB_6 | InstanceDB | 337 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_6.txt` |
| Shuttle_TCP_Comms_FB_DB_7 | InstanceDB | 338 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_7.txt` |
| Shuttle_TCP_Comms_FB_DB_8 | InstanceDB | 341 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_8.txt` |
| Shuttle_TCP_Comms_FB_DB_9 | InstanceDB | 349 | DB |  | `db/Shuttle_TCP_Comms_FB_DB_9.txt` |
| SICK_AFx60_DB_1 | InstanceDB | 121 | DB |  | `db/SICK_AFx60_DB_1.txt` |
| SICK_AFx60_DB_2 | InstanceDB | 319 | DB |  | `db/SICK_AFx60_DB_2.txt` |
| SICK_Lector_Control_DB_1 | InstanceDB | 47 | DB |  | `db/SICK_Lector_Control_DB_1.txt` |
| SICK_Lector_Control_DB_2 | InstanceDB | 63 | DB |  | `db/SICK_Lector_Control_DB_2.txt` |
| SICK_Lector_FB_DB_1 | InstanceDB | 45 | DB | SICKAG | `db/SICK_Lector_FB_DB_1.txt` |
| SICK_Lector_FB_DB_2 | InstanceDB | 306 | DB | SICKAG | `db/SICK_Lector_FB_DB_2.txt` |
| Stack_Lights_DB_1 | InstanceDB | 62 | DB |  | `db/Stack_Lights_DB_1.txt` |
| Stack_Lights_DB_2 | InstanceDB | 313 | DB |  | `db/Stack_Lights_DB_2.txt` |
| System_Buffers_DB_1 | InstanceDB | 129 | DB |  | `db/System_Buffers_DB_1.txt` |
| System_Buffers_DB_2 | InstanceDB | 130 | DB |  | `db/System_Buffers_DB_2.txt` |
| System_VTD_DB_1 | InstanceDB | 128 | DB |  | `db/System_VTD_DB_1.txt` |
| System_VTD_DB_2 | InstanceDB | 322 | DB |  | `db/System_VTD_DB_2.txt` |
| VTD_FB_DB_1 | InstanceDB | 164 | DB |  | `db/VTD_FB_DB_1.txt` |
| VTD_FB_DB_2 | InstanceDB | 168 | DB |  | `db/VTD_FB_DB_2.txt` |
| VTD_HMI_FB_1_DB | InstanceDB | 7 | DB |  | `db/VTD_HMI_FB_1_DB.txt` |
| VTD_HMI_FB_2_DB | InstanceDB | 49 | DB |  | `db/VTD_HMI_FB_2_DB.txt` |
| VTD_HMI_FB_DB | InstanceDB | 22 | DB |  | `db/VTD_HMI_FB_DB.txt` |
| Watchdog_Settings | InstanceDB | 134 | DB |  | `db/Watchdog_Settings.txt` |
