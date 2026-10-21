# Marble – pedidos/WMS, HMI e comunicações

Análise estática de `../scl` e `../db` (19/10/2026), comparada com `Reference_Project/*.scl` (Yusan) e com `TwinCAT Project1/Sys1_Inbound`.

## 0. Limites do material
- O conversor perdeu referências a constantes locais: em `scl/Order_Table_VTD_FB.scl`, `scl/Order_Table_Buffers_FB.scl` e `scl/Auto_Test.scl` aparecem `Status := ;`, `Device = `, `Device := ,`. Valores ('Queued', 'Running', 'Completed', 'Error', 'Canceled', 'Paused', 'Error\Cancel', 'VTD', 'Pallet In Out', 'Shuttle In Out', 'Level N') recuperam-se por analogia com `Reference_Project/Order_Table_FB.scl` (Yusan), mesmo esqueleto. O XML em `../xml/` tem os valores completos.
- Fora do export: OB Main (LAD), `OPC_Control_FB_DB_1/_2`, interface do servidor OPC UA e os blocos que escrevem `"Time"`, `"OrderNo"` e `HMI_Box_Connected_x`. A ligação `OPC_UA_State_*` ← `OPC_Control_FB.State_*` é inferida pelas faixas de valores (100..120, 70..90, 400, Main=10).

## 1. Fluxo de pedidos
Origem – todas as fontes escrevem em `System.StepTable[0..20]` e levantam `System.OrderSent`:
- WMS/PC via OPC UA (Yusan comenta "Step Table sent by PC", "Order Sent by PC").
- `Auto_Test` (`Auto_Test_1_DB`, `Auto_Test_2_DB`, uma por sistema) → `VTD_Order_FC`/`CNV_Order_FC` → `Feed_Steptable_FC` (OrderNo = StepNo = Task_ID = `"OrderNo"+1`; nenhum bloco exportado incrementa `"OrderNo"` %MW158).
- HMI `FC_Orders`: PlaceOrder_PB grava StepTable[1] com OrderNo = -1, mas o `OrderSent` está comentado e a contagem começa em StepTable[0] (vazio) → na prática não funciona.

Tabelas – 4 instâncias de `System_UDT`: `System_VTD_DB_1/2`, `System_Buffers_DB_1/2`:
- `OrderTable[0..99]` e `StepTable[0..20]` de `OrderTable_UDT` {OrderNo, StepNo, PlaceTime S[20], Device, Sequence, Status S[12], CompleteTime, ErrorID, OPC_Control}.
- `OPC_Control` = `WMS_OPC_UA`: Task_ID, Task_Metadata S[250], Task_Type, Source/Destination_Location (DInt XXYYZZ), Task_Data_Available, SM_State, Movement_Ready, Movement_Request_Complete(_Ack), Shuttle_ID/Loaded, Pallet_Type e Pallet_Alignment (CHAR), Pallet_Weight.

Inserção: conta as n linhas válidas, desloca a tabela n posições (o que passa de 99 se perde), copia invertido (StepTable[0] → OrderTable[n]); `CurrentOrder += n` e corrige ponteiros por dispositivo. [1] = mais recente; `CurrentOrder` desce até 1 (FIFO). Índice 0 = "sem pedido", mas recebe escritas.

Despacho: `Device` derivado de `Task_Type` só em OrderTable[1] – VTD FB: 1 → VTD; 2/3 → Shuttle In Out; 4/5 → Pallet In Out. Buffers FB: 12..16 → Level 2..6. Com [1] Queued e dispositivo livre, copia OPC_Control para a mailbox `"Control_DB"."VTD_Order Table"[Id]` ou `"Buffer_Order Table"[Id]`, liga `Task_Data_Available` e arma o watchdog (`Watchdog_Settings`, minutos ×60000).

`OPC_Control_FB` é o **executor interno**, não um cliente WMS:
- State_VTD: 10 → 20 (`ID_Decode_F`) → 30..45 move-to-floor (espera SM_State=100, 500 ms, Complete, Ack) | 70..90 shuttle (Interlock_Request → Ready_To_Interlock → Interlock_Complete → Ack) | 100..120 palete extrator↔CNV1 (Start_Transfer, espera os dois Done). Todos terminam em 250 (reset) → 0; 400 = erro.
- Buffers: State_Main 20 roteia por Task_Type 12..16 para State_L2..L6 (100 = CNV1→CNV2, 101 = inverso) → 110 → 115 → 118 (`Movement_Completed.Level_x := TRUE`) → 120 (espera reset) → 250.

Fecho: o Order_Table detecta por R_TRIG `Movement_Request_Complete`, `VTD.Shuttle_Interlock.Interlock_Complete` ou `Movement_Completed.Level_x`; marca Completed + CompleteTime; com `OPC_Control.Movement_Request_Complete_Ack` da linha zera mailbox e ponteiro. `OrderTable_HMI."Manual order"` simula o Ack. Nenhum bloco exportado escreve TRUE em `Control_DB.*Order Table.Movement_Request_Complete_Ack` (presumivelmente WMS ou OB Main – não confirmável). Só o L2 tem Ack; L3..L6 fecham sozinhos.

Pause/Cancel/Resume: Pause (ou saída de Auto): Queued → Paused, Running → Canceled. Cancel: Queued/Paused → Canceled, Error → Error\Cancel. Resume: Paused/Error → Queued. NextOrder volta a 1 à meia-noite (DTL).

Yusan → Marble: Yusan tinha um único `Order_Table_FB` com 16 transportadores (11..82) e mailbox `Control_DB.WCS_OPC_Control[1..5]`; estados VTD/Shuttle/CNV mutuamente exclusivos, sem Ack. Marble separa VTD (com extrator/CNV1) de Buffers (CNV1↔CNV2 por nível) com duas mailboxes; níveis em paralelo; Ack acrescentado. O Marble removeu `Task_Data_Available := 0` do despacho – no move-to-floor ninguém zera o flag depois de concluir → **possível reexecução; verificar**. `CNV_Order_FC` mudou a semântica Tower/Transfer (Yusan: torres em lados opostos; Marble: CNV1 e CNV2 em série). `Feed_Steptable_FC` perdeu Pallet_Type e Pallet_Alignment.

## 2. Feed_*, CNV_Selector, *_Charge_Settings, Settings_Limits_FC
Não são conceitos novos: o Yusan já chama `Feed_VTD_HMI_FC`, `Feed_ECNV` e `CNV_Selector` (`Reference_Project/VTD_HMI_FB.scl`, `Conveyor_HMI_FB.scl`), mas esses blocos não tinham sido exportados – por isso faltavam no SpaceX (docs/TIA_Missing_Blocks.md). **O Marble os fornece.**
- `Feed_VTD_HMI_FC`: espelha ~45 status de `Control_DB.VTD_Sys[n]` nos tags %M da HMI; se não houver `System_Busy` nem Charge, escreve a Instruction (Reset, Mode_Change, Enable, Stop retido). `Move_To_Level` só com Mode=2 (one-shot); Up/Down/DP/Teach só com Mode<>3; também palavras de controle do AE e comandos BCD.
- `Feed_ECNV`, `Feed_BCNV_Cnv1(1)`, `Feed_BCNV_Cnv2`: o mesmo para extrator e buffers (Fwd/Bwd, Start_Transfer, Transfer_To/From_ID conforme `In_Out`, stoppers).
- `CNV_Selector`: a partir de sistema, nível e CNV1/2 selecionados calcula `CNV_ID_HMI(1)` e `CNV_ID_HMI` (IDs do Settings_DB).
- `VTD_Charge_Settings` / `CNV_Charge_Settings_FC`: copiam Settings_DB → `PopUps_DB` (buffer de edição). `PopUp_Screens` devolve todo ciclo e chama `Settings_Limits_FC` (velocidades, Acc 60..100, Dock ≤10, Chain_Slack ≤5000).
- As versões `_1` servem **vários painéis HMI**, não o sistema 2: recebem `HMI_No` (1..5; índice em `Screen_DB_1`, `PopUps_DB_1`, `VTD_HMI`, `CNV_HMI`), `HMI_Box`/`Zone` (posto do painel portátil: 11..16 / 21..26 = sistema/nível; `MOD 10` = nível) e `Sys_No`. Parecem inacabadas: `CNV_Selector_1` nunca escreve as saídas `ID`/`ID(1)` (escreve os globais) → o `CASE #ID` de `Conveyor_HMI_FB_1` nunca coincide.

## 3. HMI
- Telas: a HMI escreve `HMI_DB.ScreenNo_Main` (1 = VTD, 2 = CNV) ou `ScreenNo[HMI_No]`; o Feed só roda com a tela aberta.
- Charge-on-select: ao mudar a seleção, `VTD_HMI_FB`/`Conveyor_HMI_FB` copiam durante 500 ms a Instruction atual para os tags de comando (evita salto de comando).
- Seleção de sistema: `VTD_System_Selected_HMI`, `CNV_System_Selected`, `Settings_System_Selected`, `Main_OrderTable_Selected` (1/2 = VTD, 3/4 = Buffers). `Screens` só trata os casos 1..3.
- Tabela de pedidos (`FC_Orders`): janela de 9 linhas (`StartRow` 0..90), `State` 1..7 para cores; botões place/pause/resume/cancel/cancel-this, popup de erro, visibilidades do Auto_Test em `OrderTable_HMI`.
- Automático: `Automatic_Button_*` põe todos os dispositivos em Mode 3 com Enable; `All_In_Automatic_*` indica se ficaram todos em auto.
- Shuttles: `Screen_DB.Shuttle` ← `Shuttle_MQTT_DB[Shuttle_Select]`, E-stop por nível (`Shuttle_Level_EStop` ↔ `Lx_Estop`).
- Local/remoto: `HMI_Box_Connected_1..5` com `"KEY REMOTE/LOCAL Lx"` gera `System_Busy`, que bloqueia o painel principal. `VTD_HMI_FB_1` força `Mode_Change := 1` (Manual) todo ciclo; `Feed_ECNV_1` só comanda com o VTD no nível do posto; `Feed_VTD_HMI_FC_1` limita o jog à faixa `Levels_LE` desse nível.

SpaceX hoje: `GVL_HMI_System` só status e `bResetAll` (`FC_SystemHmiUpdateStatus` TODO); `GVL_HMI_VTD` telas TEST ONLY do `FB_VTD_ManualControl`; `CNV_HMI`/`CNV_HMI_IO` cópia achatada dos tags %M do Marble, sem lógica. Falta no SpaceX: Feed (status + portão de comandos por modo), charge-on-select, buffer de settings com limites, tabela de pedidos, Auto_Test, botão Automático e arbitragem local/remoto.

## 4. Comunicações
- OPC UA/WMS: não há bloco cliente; o WMS lê/escreve DBs – `System_*_DB` (StepTable, OrderSent, Pause/Cancel/Resume), mailboxes `"VTD_Order Table"`/`"Buffer_Order Table"` (nomes com espaço), `Time.PC_HeartBeat`/`Time.PLC_HeartBeat`. `FB_HeartBeat` incrementa `PLC_HeartBeat` a cada 500 ms e dá `PC_Disconnected` após 10 s sem mudança (consumidor não exportado). `Watchdog_Settings`: VTD, EConveyor, Pallet, Shuttle = 500 (min); **Level_2..6 = 0** (sem valor → timeout imediato). `Error_ID` usa bits 0 e 8.
- MQTT: biblioteca Siemens **LMQTT V4.0.5** (`LMQTT_Client`; DBs `LMQTT_Client_DB`, `LMQTT_Client_fb`). `MQTT_Handler_FB` subscreve `vehicle/Shuttle-NN/state` em sequência (Shuttle_Count = 10); só subscreve. Broker 10.44.116.9:1883, client 'PLC_1', QoS 0, retain, keepAlive 60, sem TLS. Payload → `ByteArrayToString` (6 janelas) → `ParseShuttle_Status` (requestId…lastFinishedOrderId; várias chamadas com Str2 vazio) → `Shuttle_MQTT_DB[1..24]`. Consumidores: `Screens`, `OPC_Control_FB` (Shuttles_Position x/y), `Shuttle_TCP_Comms` (Charging := Paused). Yusan: broker .8, 23 shuttles e auto-reset (desliga LMQTT e pulsa `Reset_All` 10 s) – removido no Marble.
- TCP: biblioteca **LCom V2.1.0**, `comService=1` (TCP puro), PLC passivo, aceita parceiro desconhecido. `TCP_IP_Shuttle_DB_n`: porta 400n, connID 10n, IP 10.0.34.21n (n=10 → .220), interfaceID 65164; exceção #2 = 10.0.35.62. 24 instâncias Shuttle_TCP_Comms/LCom (herança Yusan), `Shuttle_Count` = 10. Telegrama a cada 500 ms: [0] = 83 ('S') se NOT E-stop, senão 0; [1] = nível do VTD1; nível do VTD2 em [2] nunca enviado (`SendDataLength` = 2). Recepção ignorada.

## 5. Reaproveitar no SpaceX
1. Order table: trocar `MigrationReview/IntegrationReview/Order_Table_FB.TcPOU` (Yusan) pelo porte de `Order_Table_VTD_FB` → `Control.VTD_Order_Table` e `Order_Table_Buffers_FB` → `Control.Buffer_Order_Table`. Para `Carousel_Order_Table` não há referência no Marble (FB novo). Reativar `System_DUT.Watchdog_TimeOut` e `Control.Movement_Completed` (hoje comentados).
2. `OPC_Control_FB.TcPOU`: estrutura Marble (State_VTD + Main/L2..L6) com ENUMs; `ID_Decode_F` já existe no alvo.
3. `Feed_Steptable_FC`, `VTD_Order_FC`, `CNV_Order_FC`: versões Marble, revendo IDs para a topologia SpaceX.
4. Auto_Test: versão Marble + `OT_Charge_Commands` substitui `Auto_Test`/`Auto_Test_1`.
5. HMI de pedidos: `FC_Orders` → GVL de pedidos nova com `ST_HMI_*`.
6. POUs novos de HMI: Feed VTD/ECNV/BCNV → `GVL_HMI_VTD`/`GVL_HMI_System` (implementa `FC_SystemHmiUpdateStatus`), charge-on-select, buffer de settings e `Settings_Limits_FC` corrigido.
7. MQTT: `Tc3_IotBase` + `Tc3_JsonXml` em vez das janelas fixas, mantendo contrato de tópico/campos; criar DUT de status do shuttle.
8. TCP: `Tc2_TcpIp`, um servidor por shuttle.

## Riscos e pegadinhas de porte
- Modelo de índices do alvo incoerente: `Control.TcGVL` escalar (VTD, `LCnv[1..6]`, carrossel), `Settings` [1..2], MAIN usa `Control.VTD_Sys[1]`. Decidir antes de portar código indexado por `[Id]`.
- Resíduos de 5 sistemas: `Auto_Test_DB_DUT.System[1..5]`, rascunhos com `Cnv_Buffer_11..82` e L7/L8, `Screens._id_decoded_OP[1..5]`, `Erros_Word_OPC_1..5`. No Marble [1..5] são **painéis HMI**, não sistemas.
- Tipos/funções S7: DTL → `FB_LocalSystemTime`; CHAR `Pallet_Type` (no SpaceX é BYTE, `'C'`/`' '` não compilam; CHAR→UInt); WString, HW_ANY/CONN_ANY/IP_V4, `%X`, `RESET_TIMER`, `WRIT_DBL`; R_TRIG globais dentro de FUNCTION; `HMI_Reset` (VAR_TEMP) lido antes de escrito; `Status` String[12] comparada por texto → ENUM.
- Precedência AND/OR no reset do watchdog e no `HMI_Reset` (`Reset_All[1] AND (a) OR (b)…`): reset dispara sem botão com caixa 2..5, ou caixa 1x com a chave.
- Bugs de cópia/cola: L3..L6 testam `OPC_UA_state_L2`; reset do watchdog Buffers só cobre L2..L4; `Settings_Limits_FC` escreve `Lowest_Level` em vez de `Highest_Level`; `HMI_Box_Connected_1` duplicado em `Feed_ECNV`, `Feed_BCNV`, `FC_Orders`; `Screens` caso 3 usa `Order_Table_VTD_FB_DB_2`; `System_Buffers_DB_2.Id` = 1; Auto_Test manda buffers com Task_Type 4 e `VTD_System_OrderSent`; caminho de buffers do OPC testa `Source.Level = 11/10`; `FC_Orders` faz CancelThisOrder sem somar `StartRow`; `FB_HeartBeat` chama o timer duas vezes por ciclo.
- Hard-codes: senha '12345' reescrita todo ciclo, broker, IPs/portas, níveis 2..6 por região, Highest_Level 8, estados mágicos 100/250/400, modos 0..5 (0 Disabled, 1 Manual, 2 Semi-Auto, 3 Auto, 4 Teach, 5 Maintenance), códigos de caixa HMI.
- Proteção de máquina: E-stop de shuttle via TCP/HMI e `Reset_All` global são funções sem rating de segurança – revisão à parte conforme AGENTS.md.
