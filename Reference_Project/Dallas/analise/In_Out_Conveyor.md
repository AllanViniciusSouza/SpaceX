# Dallas InConveyor_FB / OutConveyor_FB – análise para o SpaceX (19/10/2026)

Fontes: `scl/InConveyor_FB.scl` (FB 9, instância `Inbound_Cnv_FB_DB`), `scl/OutConveyor_FB.scl` (FB 16, `Outbound_Cnv_FB_DB`),
UDTs em `udts/PLC_data_types.scl`, valores em `db/Settings_DB.txt`. Chamados no OB Main, network 5 "Carousel Conveyors".

## Função
- **InConveyor** (drive G_3 "Roller Inbound"): estação de entrada por empilhadeira. Entrega o pallet ao **popup 1** (rolo).
- **OutConveyor** (drive G_5 "Roller Outbound"): estação de saída por empilhadeira. Recebe do **popup 4**.
- 1 motor cada (UDT `Cnv_Motor`, SinaSpeed, RefSpeed 1745 rpm, velocidade em %, **Forward = setpoint negativo**).

## InConveyor – estados
| Estado | O que faz |
|---|---|
| 0 | Init: para o motor; vai a 10 se Enabled, modo 2/3 e sem erro |
| 10 | Borda de Execute → motor Full_Speed e vai direto a 20 **com o motor ligado** (comentário "Without barcode"). Start_Transfer com sensor traseiro ocupado e dianteiro livre → 15 |
| 15 | Avança até o sensor dianteiro, para o motor → 20 |
| 20 | Leitura de código de barras: espera `InBarcode_Station.Valid` ou "Debug_Barcode" ou 1 s → 30 |
| 30 | Espera o **popup 1 rodar** (`PopUp_Cnv[1].Roller_Motor.Status.%X0`) → motor Full_Speed → 40 |
| 40 | Roda até "PopUp Conveyor 2 - Pallet present 3" (sensor do popup 1) ou Stop → Done, 0. Watchdog Transfer_Time (erro 14:1) |
| 400 / 500 | Erro (reset limpa as words) / Manual (Backward só se NOT "Pallet Detect 1") |

Cíclico: `Cnv_Occupied := NOT back OR NOT front` (sensores NF). `Automatic_Start` = pulso de 3 s quando há pallet e nenhuma
empilhadeira por `No_Forklift_Detect_Timer` s (5 s) – só é escrito pelo PLC; deve ser lido pelo WMS/OPC UA.

## OutConveyor – estados
| Estado | O que faz |
|---|---|
| 0 | Init |
| 10 | Execute/Start_Transfer → motor Full_Speed → 20 (o receptor liga primeiro; o popup 4 espera este motor) |
| 20 | Roda até "Outbound Conveyor" ocupar (sensor NF) ou Stop → Done. Watchdog Transfer_Time |
| 400 / 500 | Erro / Manual (Forward só se NOT Cnv_Occupied) |

Cíclico: `Instruction.Empty` = pulso de 3 s quando vazio e sem empilhadeira por 5 s (para o WMS).

## Valores do Settings_DB
| | ID | Transfer_Time | Full_Speed | Manual_Speed | No_Forklift_Detect_Timer |
|---|---|---|---|---|---|
| Inbound | 130001 | 30 s | 60 % | 60 % | 5 s |
| Outbound | 140001 | 25 s | 60 % | 60 % | 5 s |

Popups (`PopUp_Cnv_Settings[1..4]`): ID 150001/160001/170001/180001; roller full 60 %; chain full 60/70/70/60 %;
lift full 100/100/80/100 %; transfer time roller 30/30/25/25 s, chain 50/500/40/50 s, lift 7/15/15/15 s.
Boost por transferência: `TimeStartBoost_P1ToP2` 8 s, `P2ToP3` 20 s, `P3ToP4` 8 s.

## Problemas encontrados no Dallas
1. InConveyor: `Timer_Transfer` corre em 15 e não é chamado em 20/30; ao voltar em 40 o TON continua do tempo antigo → timeout falso possível. Reiniciar o timer a cada mudança de estado.
2. InConveyor: caminho por Execute deixa o motor ligado durante a leitura de barcode e a espera do popup.
3. Nomes de sensores trocados: "PopUp Conveyor 2 - Pallet present 3" é usado como sensor do popup 1.
4. Handshake por `Roller_Motor.Status.%X0` (AxisEnabled Siemens) – no SpaceX usar `stStatus.bMotorTurning` do SEW.
5. `Lockout` e `Error` do SinaSpeed escrevem no mesmo `Motor.Error`.

## Porte para o SpaceX (TwinCAT, SEW)
- `Control.Roller_Cnv : ARRAY[1..5] OF Roller_Control_DUT` (já declarado, tipo não existe): base sugerida =
  `Inbound_Cnv_Control_UDT` + `Outbound_Cnv_Control` unificados (Inputs: Pallet_Detect_1/2, Fork_Lift_Detect; Instruction: Automatic_Start, Empty).
- Um FB genérico de rolo com 1 `FB_Cnv_SewMotor` (ver `analise/PopUp_TwinCAT_Proposta.st`), papel entrada/saída/passagem por settings,
  e o mesmo handshake de vizinho (`Side` status) do popup.
- Confirmar no Rev 9 quais dos 5 rolos do SpaceX são estações de empilhadeira (inbound/outbound) e quais são de passagem.
