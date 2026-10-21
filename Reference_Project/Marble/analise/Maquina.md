# Marble – lógica de máquina (VTD, buffers, extrator, transferência, periféricos)

Análise estática de `../scl` e `../db` (19/10/2026), comparada com `Reference_Project/*.scl` (Yusan) e com `TwinCAT Project1/Sys1_Inbound`.
**Ressalvas:** o OB1 do Marble não foi exportado (inconsistente) e os DBs de instância não trazem valores atuais; parametrização das chamadas (Safety_OK, Mode/Timeout dos stoppers, Time_SlowDown_Ramp) não é confirmável. O conversor perdeu operandos que eram constantes locais (`scl/VTD_FB.scl` l.1179 `> THEN`, comparações de gate em `scl/Bypass_FC.scl`, `Status =` em `scl/Auto_Test.scl`).

## 1. Topologia
- Por sistema (2 iguais): 1 VTD com transportador embarcado (ECnv, tags CVTDn_*), 8 cotas ensinadas (`Levels_LE[1..8]`), buffers só nos níveis 2..6 (`Cnv_VTD_*.Cnv_Level : Array[2..6]`), Cnv1 + Cnv2 por nível → 10 buffers/sistema, 20 no total; com os 2 ECnv `System.Cnv_Count = 22`. Level_Count = 6, Shuttle_Count = 10 (MQTT). Níveis 7/8 têm cota mas não têm I/O nem buffer.
- Nomenclatura `C{S}{n}{LL}` (confirmada em `scl/INPUTS.scl`): C1102 → `LCnv_Sys[1].Cnv_Level[2].Cnv1`; C1202 → …Cnv2; C2102 → `LCnv_Sys[2]`…Cnv1. `Sf_Cxxxx` = instância de Safety_Stops_FB do mesmo transportador.
- Só existem transferências ECnv↔Cnv1 e Cnv1↔Cnv2 → Cnv1 junto ao poço, Cnv2 em linha atrás. Stoppers físicos só em C11xx/C21xx (`tags/IO_ET200_1/2.xml`); instâncias Sf_C12xx/C22xx existem sem I/O. Cada buffer: 2 sensores (Forward/Backward = `Cx_Inputs.%X0/%X1`) + 1 G120.
- IDs (`scl/ID_Decode_F.scl`): DInt decimal XXYYZZ → Device_Type = ID/10000, Level = (ID MOD 10000)/100, VTD = ID MOD 100. Tipos: 10 = Cnv1, 11 = Cnv2, 12 = ECnv, 20/21 = stoppers (não usados). Código do VTD inconsistente: 01 (comentário VTD_FB), 40 (comentário Buffer), 30 (VTD_Order_FC monta 300LL0S). Settings: Cnv1 = 10LL0S, Cnv2 = 11LL0S; ECnv começa 120101/120102 e é reescrito a cada ciclo para 12LL0S (nível atual) pelo Conveyors_Transfer.
- Barcode_ID (posição do shuttle), passo 8 por nível: Sys1 Cnv1 14/22/30/38/46, Cnv2 15…47; Sys2 Cnv1 16…48, Cnv2 17…49; ECnv 1/2.

## 2. VTD_FB (`scl/VTD_FB.scl`)
Modos (Mode_Change): 0 desabilitado; 1 manual e 5 manutenção → estado 500; 2 semi; 3 auto (força Enable); 4 teach sem estado (Start_Teach não é lido; cotas fixas no Settings).

Máquina de estados (auto/semi):
- 0 → 10 (standby): Move_To_Level em [Lowest,Highest], VTD sem palete e Task_ID>0. Precedência: `Task_ID>0 OR (Metadata<>'' AND Mode=3 AND Task_Type=1)` → Task_ID>0 sozinho basta. Já no nível pedido → Warning 1.
- 20/25: Extend em todos os stoppers Cnv1/Cnv2 e espera DP_Extended de todos (níveis 2..6 fixos).
- 30 → 35 → 36/40 (desacoplar): se docked/perto do nível, sobe a Dock_speed até LE+40 mm, espera NOT Level_Detect e recolhe os pinos (DP_Timer).
- 45: escolhe velocidade (Empty/Shuttle/Pallet/Loaded) e sentido.
- 50/65 (perfil em degraus por distância): > Slowdown_Count_LE do destino → cruzeiro; dentro da janela, faixas 80/60/40/20 % → Slow_Calib ×1,8/1,6/1,4/1,2; < 20 % → Slow_Calib.
- Fim: subindo, 55 entra em creep em dest−Creep_Count e 60 passa do nível até dest+Creep_Count e para; descendo, 70 para em dest+Creep_Count, sem creep.
- 80/85: estende os pinos acima do nível. 90: desce a Dock_speed até |LE−dest| ≤ Level_Detect_LE e mantém CS_Timer (Chain_Slack_Timeout) para afrouxar a corrente sobre os pinos. 95 → 100 → 0: espera Level_Detect1 AND 2 (LD_Timer; ×5 se nenhum sensor).
- 400 erro (reset limpa as 5 words). 500 manual: Manual_Up/Down a Manual_Speed, creep perto do nível com pinos estendidos; pinos só com VTD parado.
- Watchdog dinâmico calculado (dist/(%×8 mm/s)×1,5 ou ×2,0, mín. 5 s) mas a avaliação está comentada.

Interlock com shuttle (I_State; Mode 3, Interlock_Request e Task_ID>0, vindos do OPC_Control_FB): 10 valida Docked, parado, VTD vazio e Position_ID do shuttle (`Shuttle_MQTT_DB`) = Start_Location; escolhe Cnv1/Cnv2 pelo Barcode_ID → 20/25 Retract do stopper do nível → 30/35 com LP_State=0 liga Ready_To_Interlock → 40/45 espera shuttle no destino com Operational_State='IDLE' e manda Extend → 50/55 confirma stopper estendido em 5 s → 60 espera Ack. Timeout Shuttle_Interlock_Timeout×1000 ms → EW3.3.

Posição e drive:
- Usa só o LE = `LE_X_Unsafe_Position/10` (mm); cotas em `Settings.Levels_LE`.
- AFx60 (`FB_SICK_AFx60_PN`, biblioteca): só acíclico (RDREC/WRREC PROFIdrive) para parâmetros/diagnóstico; não é chamado no SCL exportado (provavelmente no OB1). A posição cíclica do AE (escalonada em INPUTS) serve só para Encoder_Delta = |AE−LE|. Levels_AE, *_AE, AE_Ratio e Teach_* não são usados.
- Drive SINAMICS via SinaSpeed (G120_Hardware_ID 475/959): RefSpeed 1762 rpm; SpeedSp = %/120×1762; ZSW1 bits 0/1/2/3/7/13; Acc_Factor (16384 = 100 %) por faixa de Pallet_Weight.

Erros (Set_Bit_F):
| Word | Bits |
|---|---|
| EW1 | b0 Safety; b1 Stop; b2/3 overtravel; b4/5 LE fora de Max/Min; b8/9 auto sem docked / sem level detect; b11 pinos em movimento; b12 retrair docked |
| EW2 | b2 delta entre encoders; b3 timeout dos pinos; b5 pinos em estado desconhecido; b7/8 limite em jog |
| EW3 | b1/b2 interlock; b3 timeout do interlock **e** erro Profinet (bit compartilhado); b4 LE; b5 AE; b6 "still moving" |
| EW4 | VFD/LE/AE/pinos/limites; b11 level detect |
| EW5 | b0..3 chain slack |
`Bypass` (Safety_Bypass_RemotePanel) mascara overtravel, limites e chain slack; `LE_Bypass_HMI` mascara LE e delta.

Defeitos do Marble (o alvo herda se reativar como está):
- (a) "Still moving": Position_OLD fica 0 enquanto anda e não há gate de "parado" → dispara em qualquer movimento.
- (b) Timeout de retração `DP2_Retract AND DP2_Extend` nunca é verdadeiro.
- (c) Checagem "em movimento" cobre LevelBelowExtractor <7 e =8; nível 7 nunca verificado.
- (d) `FOR Lowest..Highest` (1..8) indexa `Cnv_Level[2..6]` fora dos limites.
- (e) `VTD_Control.Shuttle_Loaded` nunca é escrito → velocidade sempre Empty/Pallet (100 %).
- (f) Overrides Ultimate_SlowDown/Creep sobrescritos nos estados 50/65.
- (g) `Settings_Limits_FC`: com Highest>8 grava `Lowest_Level := 8`.

Yusan → Marble (diff): o Marble **removeu** classificação CHEP/EURO por 5 sensores e detecção de shuttle no VTD; Safety_OK_Delayed e ConfigAxis 16#003D (OFF2); Stopper_Extend_Timer com alarme por stopper (EW2.6, EW3.6–15, EW5.4–7); guarda LE<>0 na descida e erro LE=0 (EW1.13); Shuttle_In_Place no interlock 50/55; níveis 7/8 do estado 25 e reset para 5 caixas × 8 níveis. **Acrescentou** "still moving", exigência de Shuttle_Interlock_Task_ID>0, WCS_OPC_Control → "VTD_Order Table", Set_Bit_F sem Bit_Value.

Para reativar no alvo (`POUs/VTD/VTD_FB.TcPOU`) – o bloco comentado **já é o Marble** (diff normalizado: só sintaxe, LE→LinearEnc, Motor.Speed→Motor_Speed, REAL_TO_UINT, fbSewDrive.q_bError, `Tol_VTD_Still_Moving` e um `System_no>3` a mais no estado 10). Pendências:
1. Preencher LinearEnc a partir de PI7/8 (TODO). Sem isso LE=0 → EW1.5 na hora.
2. Decisão de arquitetura: o FB faz o perfil de posição no PLC com o LE; o AGENTS.md proíbe malha de posição no PLC sem documentação; a região VFD atual usa speed mode (200). Sugestão (a confirmar): estados 45–70 viram posicionamento MOVIKIT até Levels_LE[n]+Creep_Count; docking (80–95) continua em velocidade.
3. Tirar/substituir a lógica de AE (não há AFx60 no SpaceX), senão EW2.2/EW3.5.
4. LE_Status.0/.1 → validade de posição SEW; Errors_Profinet_x → `q_stStatus.bCommunicationOk`.
5. HMI_Reset (KEY REMOTE/LOCAL, HMI_Box_Connected) → GVL de HMI. Referências a Shuttle_MQTT_DB, "Settings_DB" e Control_GVL precisam de interface.
6. VTD_Errors_DUT UINT → WORD (VAR_IN_OUT do Set_Bit_F), como no Cnv_Errors; estados → ENUM.
7. `GVLs/Control.TcGVL` (modificado 19/10 13:30) declara VTD/ECnv únicos, `LCnv[1..6]` e Turn_Table/Pop_Up/Roller/Chain (DUTs inexistentes), enquanto MAIN, Inputs, Conveyors_Transfer, VTD_FB e Buffer usam `Control.VTD_Sys[n]/LCnv_Sys[n]/ECnv_Sys[n]` e Settings continua [1..2] → definir a topologia antes de portar.

## 3. Buffer_Conveyor_FB / EConveyor_FB
Estados: 0 (zera flags) → 10: `Ready_For_Task` (= Inbound_Ready OR Outbound_Ready) e borda de Execute ou Start_Transfer → Transfer_in_Progress + Running. 20 decide o sentido pelo próprio ID e From/To: 12→10 Forward (recebe; exige ECnv ocupado); 10→11 Forward (envia; espera Cnv2.SM_State=30); 11→10 Reverse (envia); 10→12 Reverse (envia; espera ECnv.SM_State=30). 30 roda; 35 para e liga Done; 400 erro; 500 manual (Foward/Backward, ou Start_Transfer com CNV_In_Out/CNV1_2_Selected).

Handshake: receptor vai para 30 primeiro; emissor espera. Receptor para quando fica Occupied; emissor para quando deixa de estar Occupied. Transfer_Complete nunca vai a TRUE.
**Possível defeito no estado 20:** faltam os casos de recepção Cnv1→Cnv2 (Cnv2 recebendo) e Cnv2→Cnv1; o OPC_Control_FB grava o mesmo From/To nos dois → receptor cai no ELSE (EW2.5), emissor espera para sempre. Confirmar em campo; o alvo herdou.

Sensores/tempos: ocupado = ambos os sensores por Time_CheckPallet (padrão T#2s) ou um sensor com transportador parado; livre = rodando sem sensores por Time_CheckNoPallet (2 s) ou parado sem sensores. Timeout de transferência Transfer_Time×1000 (20 s) → EW2.3. `Time_SlowDown_Ramp` nunca atribuído → PT=0 → cai para Slow_Speed no 1º ciclo do estado 30 (salvo escrita no IDB pelo OB1). EW3.2 com `ID_Decoded.Level = 10` nunca verdadeiro. Escala: Speed 130 = 1865 rpm, Forward = setpoint negativo. Profinet EW3.3 fixo por VTD 1/2.

ECnv: mesma estrutura, troca só com o Cnv1 do nível; recebe Reverse, envia Forward; EW3.2 se VTD Current_Level=0; manual só com `VTD_Current_Level = Cnv_Settings.Cnv_Level`; ainda tem IDs Profinet 1..5 (resto do Yusan).

Yusan tinha: 6 sensores, tipo de palete, alinhamento (240–295), handover LGX no nível 1, Safety_OK_Delayed, rampa por sensor (R_Slow + Time_*_Buffers); Cnv1 e Cnv2 ambos encostados no ECnv (12↔10 e 12↔11).

No alvo: `POUs/Conveyors/Buffer_Conveyor_FB.TcPOU` = lógica do Marble + SEW (FB_SEW_VelocityDrive). **Time_CheckPallet/NoPallet perderam o padrão T#2s** (declarados sem valor → T#0s). O rascunho `MigrationReview/IntegrationReview/EConveyor_FB.TcPOU` é do **Yusan** (Lpd1/Rpd1, alinhamento) → refazer a partir de `scl/EConveyor_FB.scl`, compatível com o Cnv_Inputs_DUT do alvo.

## 4. Conveyors_Transfer
Para cada sistema: grava `ECnv_Sys.ID := 12LL0S` e Cnv_Level a partir do Current_Level do VTD (concatenação de string). Pronto para receber: ECnv livre, parado e Cnv1 do nível parado (avaliado para todo nível, sem gate); Cnv1 livre com ECnv e Cnv2 parados; Cnv2 livre. Pronto para enviar: ECnv ocupado e Cnv1[nível].Inbound_Ready; Cnv1 ocupado e (ECnv Inbound_Ready com VTD no nível, ou Cnv2 Inbound_Ready) e Cnv2 sem transferência; Cnv2 ocupado e Cnv1 Inbound_Ready. As flags só são ligadas aqui (o Yusan também desligava). Laço 2..Highest_Level (8), mas Cnv_Level é [2..6]. No alvo é cópia fiel, mas `RIGHT(StrSys, L:=…)` e `StrSys[1]='+'` não compilam em TwinCAT → usar `ID := 120000 + lev*100 + sys`.

## 5. Periféricos
- Safety_Stops_FB: stopper rotativo de um motor (`STOPPER MOTOR := Sf_x.T_Run.Q XOR Force…`; T_Run = TOF com PT = Timer_1 = 0). Extend/Retract em modo 2/3, timeout LP_Timer, os dois sensores ativos → erro. LP_State: 1 Ext, 0 Ret, 2 perdido (codificação diferente do LP_State do VTD). Defeitos: `Error := 0` no estado desconhecido; precedência de OR deixa Manual_Extend passar por cima dos intertravamentos. Corpo idêntico ao Yusan.
- Light_Bars (Turck): cor por modo – 0 apagado, manual amarelo 4, semi azul 9, auto verde 0, teach laranja 2, manutenção branco 19, falha vermelho 1 piscando; animação por faixa de velocidade. Usa `"SinaSpeed_VTD_DB_1".EnableAxis` nas duas instâncias (no alvo virou `i_bDriveEnabled`).
- Stack_Lights_FB: falha → vermelho piscando (Clock_0.5Hz); auto → verde; senão laranja. Saídas XOR Force.
- Barcode_Station_FB + SICK_Lector_Control_FB: abre o gate do CLV6xx (lib `SICK_Lector_CLV6xx_PNDP`, HW IDs 554/555, 32 B) por até 15 s; parse de "Number", "Code" e "NRG" → `VTD_Sys[n].Inputs."Barcode 1"`. A "confirmação" do Auto_Stop no estado 30 é sempre verdadeira. Quase idêntico ao Yusan.
- Bypass_FC: bypass via HMI de overtravel, limites e chain slack só enquanto o sensor está atuado; expira 3 s depois de normalizar (chain slack: na hora). Gates: bypass entre RTE_REQUESTED e READY_TO_RESTART. `Bypass` (DB comum) entra no VTD_FB.Bypass; `Bypass_Safe` é F-DB; `Force` faz XOR das saídas. Pelo AGENTS.md: TEST ONLY + revisão de segurança.
- Auto_Test: burn-in – VTD vai ao nível de origem → ECnv→Cnv1 → Cnv1→Cnv2 → Cnv2→Cnv1 → Cnv1→ECnv → sobe um nível → repete (VTD_Order_FC + CNV_Order_FC).
- System_VTD_DB / System_Buffers_DB: instâncias de System_UDT (tabelas de ordens), não lógica de máquina.

## 6. Settings do Marble (ponto de partida – NÃO são valores do SpaceX)
| Parâmetro | Sys1 / Sys2 |
|---|---|
| Lowest/Highest_Level | 1 / 8 |
| Levels_LE (mm) | 58, 2525, 4722, 6927, 9276, 11627, 13978, 16325 (Sys2 +5..22 mm) |
| Max/Min altura | 16500 / 55 e 0 |
| Granularity, Level_Detect_LE | 20 mm; 3,0 / 2,0 mm |
| Velocidades % | Creep 3, Slow 5/15, Slow_Calib 10, Dock 5, Manual 15, Empty e Pallet 100, Shuttle e Loaded 50 |
| Slowdown / Creep_Count_LE | 700 mm / 60 e 50 mm |
| Delta de encoders warn/erro | 80 e 50 / 200 mm |
| Timeouts | pinos 3000 ms; Level_Detect 500/900 ms; Chain_Slack 750/500 ms |
| Acc % por peso | 60/70/80 até 250/500/750; acima 100; vazio 60 |
| Buffer | Full 86, Slow 10, Manual 40 (escala 130), Transfer 20 s, stopper 3000 ms |
| ECnv | Full 100, Slow 10, Manual 40, Transfer 20 s |
| Interlock / Tol "still moving" | 999 (×1000 ms) / 5,0 mm |

## 7. Reaproveitar e riscos
Reaproveitar: VTD_FB (reativar por região), Buffer (já convertido; corrigir padrões Time_* e rampa), EConveyor (novo `POUs/Conveyors/EConveyor_FB` a partir do Marble com FB_SEW_VelocityDrive), Conveyors_Transfer (corrigir strings e limites), Safety_Stops (em revisão de segurança), Light_Bars/Stack_Lights (já portados), Barcode (falta driver do leitor), ID_Decode_F/Set_Bit_F (já portados; o do alvo é mais robusto), Settings só como valores iniciais.
Riscos: SinaSpeed/ZSW → SEW (unidades SEW_*_At_100pct = 0 → sem movimento; sentido não verificado); NORM_X/SCALE_X → REAL com LIMIT; `%Xn` → `.n`; hard-codes por sistema (Errors_Profinet_1..8, `System_no<>5`/`>3`, níveis 2..6 no estado 25, KEY L1..L6, SinaSpeed_VTD_DB_1); acessos fora de limites (sem CheckBounds sobrescrevem memória); UINT×WORD em VAR_IN_OUT, UInt×Real, `RIGHT`/indexação de string; AE e MQTT inexistentes no SpaceX; Bypass/Force são lógica de segurança; inconsistência da GVL Control.
