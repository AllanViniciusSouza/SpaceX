# Marble – segurança e modos (insumo para TwinSAFE, NÃO é lógica validada)

Método: parser de FlgNet (Parts/Wires/Access/Negated) sobre `../xml/*.xml` dos blocos F; endereços das tag tables `../tags/`. Yusan comparado pelos PDFs `Reference_Project/Main_Safety_RTG1.pdf` e `Remote_Panel.pdf`. Somente leitura.
Qualquer uso no SpaceX exige análise e verificação humana (AGENTS.md, seção Safety).

## 1. Main_Safety_RTG1 (FB1, F_FBD, 10 networks)
| NW | Lógica reconstruída |
|---|---|
| 1–2 | `HMI_SAFETY_FC` para HMI 1 e HMI 2. Entradas: `HMI_Box_Connected_1/_2` (%MW152/%MW162, padrão), `Screen_DB_1.Reset_Comissioning[1/2]` (padrão), `"PLC_HMI - HMI n Estop"` (%I356.2/%I357.2), `"PLC_HMI - Profinet_Error_HMI n"` (%I356.3/%I357.3). Saídas temp `HMI_n_Estop_Pressed_1/_2`, `HMI_n_Reset_Comiss_1/_2` |
| 3 | `Remote_Panel_DB_1`, ID=1. `Estop = "E-STOP (CABINET) - CH1(1)" ∧ ¬HMI_1_Pressed_1 ∧ ¬HMI_2_Pressed_1`; `Reset = "RESET (CABINET)(1)" ∨ Reset_Comissioning(%M70.0) ∨ HMI_1_Reset_Comiss_1 ∨ HMI_2_Reset_Comiss_1`. Demais entradas só CH1 (overtravel, chain slack 1–4, light guard 1/2, SAFETY_GATE_1/2, Lock_1/2_Estop_CH1, Lock_1/2_Closed_CH1, E-STOP L1–L6), `Bypass := Bypass_Safe.Remote_Panel_1`. Saídas `"STO VTD - CH1/CH2(1)"` %Q370.2/.3 |
| 4 | Idem `Remote_Panel_DB_2` (ID=2), STO %Q446.2/.3, só Lock_3. **`EStop_Lock_2` e `Lock_Secured_2` sem conexão (OpenCon) – confirmado no XML** |
| 5 | `Ln_OK` (%M26.6…%M39.2) `:= RP1.Ln_OK ∧ RP2.Ln_OK ∧ RP1.L(n-1)_OK ∧ RP2.L(n-1)_OK ∧ ¬Ln_Estop ∧ ¬Shuttle_EStop_All` (L1 sem termo n-1). `Ln_Estop`/`Shuttle_EStop_All` vêm de `Screens.scl` (padrão). Consumidor de `Ln_OK` não exportado |
| 6 | `F_Lock_FB_DB_1/_2` (Lock_1/2, ACK = RP1.ACK) e `_3` (Lock_3, ACK = RP2.ACK) → `Lock_n_Reset_Input1..4` |
| 7 | `#Safety_OK := RP1.Safety_OK ∧ RP2.Safety_OK` (sem consumidor no SCL; o código padrão usa `Remote_Panel_DB_n.Safety_OK` por sistema) |
| 8 | `Bypass assignments_1` (FC35) e `_2` (FC36) |
| 9 | `ACK_GL(ACK_GLOB := RP1.ACK ∨ RP2.ACK)` – reintegração global das F-I/O |
| 10 | `"RESET 1 PLC HMI"` %Q174.4 e `"RESET 2 PLC HMI"` %Q174.5 `:= RP1.ACK ∨ RP2.ACK` |

Sem I-Device nem comunicação F-CPU↔F-CPU; a troca com o S7-1200 é por canais físicos no Remote Panel 2.

Comparação com Yusan (FB123, 14 networks): Main_Panel FB16 eliminado; Remote_Panel 5 → 2 instâncias; `HMI_SAFETY_FC` perdeu `Local_Mode` e caiu de 5 para 2 saídas; níveis 8 → 6 e agregação sem `Main_Panel_OK`/`Lock_x_Estop_CH1`; travas 12 → 3; FCs de bypass 6 → 2; **Safety_OK agora é AND de todos os painéis** (a anomalia do Yusan – AND só de 1–3 – não existe no Marble); `ACK_GL` e `RESET PLC HMI` não usam mais `Bypass_Safe.Main_Panel.ACK`.

## 2. Remote_Panel (FB17, F_LAD, 26 networks)
Interface: entradas ID, Overtravel_Lower/Upper_limit, Estop, Reset, Chain_Slack_1..4, Light Guards 1/2, Gate_1/2, EStop_Lock_1/2, Lock_Secured_1/2, EStop Level 1..6, Bypass (`"F_Bypass_RemotePanel"`); saídas Safety_OK, Bypass_Warning, STO VTD CH1/CH2, ACK, L1..L6_OK; 21 instâncias ESTOP1.
- NW1: `ACK := Reset`.
- NW2–22: cada sensor → `ESTOP1(E_STOP := sinal ∨ Bypass.sinal, ACK := #ACK)`, ACK_NEC aberto (TRUE), TIME_DEL aberto → todo dispositivo trava e pede reset. Chain slack: `E_STOP := ¬Chain_Slack_n ∨ Bypass` (TRUE = folga).
- NW23: `Ln_OK := EStop Level n_DB.Q`; `EStop_Levels_OK` = AND dos 6.
- NW24: `Safety_OK := OT_L ∧ OT_U ∧ EstopCab ∧ CS1..4 ∧ Levels ∧ Gate_1 ∧ EStopLock1 ∧ LockSec1 ∧ [(LG1 ∧ LG2 ∧ Gate_2 ∧ EStopLock2 ∧ LockSec2) ∨ (4 ≤ ID ≤ 5)]` (ramo ID 4..5 herdado do Yusan, inativo).
- NW25: `Bypass_Warning` = OR dos bypass de overtravel, E-stop do painel, chain slack e light guards.
- NW26: `STO VTD CH1 := STO VTD CH2 := Safety_OK`.
Existia no Yusan e não no Marble: STO CONVEYOR VTD e STO CNV VFD (por nível/lado), Power Enable Safety Stopper, VTU Hoist Brake Sfty Enable CH1/2, `Safety_Ok_Conf` (TON 2 s), muting por SICK SEE, filtro TOF 200 ms do chain slack.
Instâncias: DB_1 = sistema/VTD 1 (C11xx/C12xx, Lock_1 e Lock_2); DB_2 = sistema/VTD 2 (C21xx/C22xx, Lock_3).

Pontos a verificar (achados, não conclusões):
- a) RP2 com `EStop_Lock_2`/`Lock_Secured_2` abertos e sem escritor de bypass → `RP2.Safety_OK` ficaria FALSE, salvo valores no IDB ou escrita não exportada. Confirmar online.
- b) Polaridade do chain slack: com a inversão, canal passivado (0) é lido como "OK".
- c) Light guards sem muting: `Bypass."Light Guards"` sem escritor (região de `Bypass_FC` comentada).
- d) Freio sem lógica: "BRAKE SUPPLY SAFETY CONTACTOR 1/2" (%Q370.0/.1, %Q446.0/.1) e "VTU HOIST BRAKE SAFETY ENABLE EDM FEEDBACK" (%I329.0/%I452.0) existem nas tags mas nenhum bloco exportado os usa.
- e) Só canais CH1 entram no FB; 1oo2/discrepância estariam na HW config (não exportada). SAFETY_GATE_3/4 não usados.

## 3. Blocos auxiliares
- F_Lock_FB (FB24): `GUARD_SWITCH = ESTOP1(Lock_Closed_CH1 ∧ CH2, ACK_NEC := FALSE)` (rearme automático); `ESTOP = ESTOP1(EStop_CH1 ∧ CH2)` com ACK; `Lock_Reset_Input1..4 := ACK`. Saídas Q não entram no Safety_OK (no Yusan alimentavam `GateLockedFeedback`/`NoEStop` do `GateAccess_Station_FB` via OB Main). Tags (Switches, Guard/Lock Position, Lamps, Solenoid Enable, Lock Reset) e comentários R1/S1/LS/RS_GSx/RS_ESx batem com **Euchner MGB2 PROFIsafe** (inferência; SpaceX usa Euchner MBM-EC via FSoE).
- HMI_SAFETY_FC (FC43): `Pressed_1 := ¬HMI_EStop ∧ ¬HMI_Profinet_Error ∧ 11 ≤ Box ≤ 18`; `Pressed_2` faixa 21..28; `Reset_Comissioning_k := faixa ∧ HMI_Reset`. O E-stop do HMI só atua no sistema da caixa onde está plugado (escolha por INT padrão). **Com Profinet_Error = TRUE o E-stop do HMI é ignorado** – avaliação humana obrigatória; não reproduzir.
- Bypass assignments_1/_2 + Bypass_Safe (F-DB39): 21 cópias `Bypass_Safe.Remote_Panel_n.x := Bypass.Remote_Panel_n.x` (DB padrão → F-DB). Quem escreve o DB padrão é `Bypass_FC`: overtravel (botão HMI, só com CH1 FALSE, cancela 3 s após normalizar), chain slack (só com folga ativa), gates/travas (TRUE entre RTE_REQUESTED e READY_TO_RESTART do ModeManager). Ninguém escreve bypass de E-stop de painel, EStop_Lock, níveis ou light guards. **Existe caminho padrão→F que mantém o STO do VTD liberado com porta aberta** – não replicar.
- SICK Safe Entry Exit HW PLC V02 (FB1000): biblioteca SICK protegida, só interface (ESPE_Channel_1/2, MR, TE, Reset, Override, material 1–4 → Q_Safety_release_1/2, status). Sem instância/chamada no Marble (no Yusan era usado).

## 4. PLC_HMI (S7-1200 1214FC)
`Main` (OB1) e `Main_Safety_RTG1` (FB1) com uma network vazia cada. Nada a migrar. Interface física: E-stop e Profinet_Error dos HMIs no F-DI do RP2; `RESET 1/2 PLC HMI` no DQ do RP2. Verificar se esses canais são 1oo1 ou 1oo2 (pares I356.x/I357.x misturam HMI 1 e 2).

## 5. SCL de modos: Marble vs Yusan
| Bloco | Marble | Yusan |
|---|---|---|
| GateAccessControl_FB | Latch de forced-open **ativo**; `GateFault := GateFault_Latch`. Timeouts de lock/unlock e `ForceRTE_Request` comentados | Latch comentado; `GateFault := GateFault_Latch := FALSE` |
| ModeManager_FB | `*_Edge_M` continuam em **VAR_TEMP** (não corrigido); sem bloco "Emergency Access"; `Reset` só desvia o estado dentro de uma faixa | E-stop força SAFE_TO_UNLOCK; `Reset` → AUTO_RUNNING sem condição |
| GateAccess_Station_FB | Mapeamento antigo dos botões (Right_True: Reset X1 / Restart X2 / RTE X3); não manda dispositivos para manual em ACCESS_MANUAL_MODE; `Lock Reset` nunca atribuído | Botões remapeados; ACCESS_MANUAL_MODE faz `Mode := 1` |
| Safety_Stops_FB | Idêntico ao Yusan (stopper padrão; `Error := 0` no estado unknown, AND/OR sem parênteses no estado 10, `T_Run.PT = Timer_1` nunca configurado) | Igual |
Conclusão: "fault-latching desabilitado" corrigido só em parte (forced-open); "edge memory temporária" não corrigida. Os drafts em `MigrationReview/SafetyReview` correspondem ao Yusan.

## 6. Insumo para TwinSAFE (validar por humano)
| Função no Marble | Alvo (`docs/safety/TwinSafeGroup1_Assembly_Plan.md`) | Observação |
|---|---|---|
| Estop_Cabinet + Reset | EL1918 1/2 (29ES1), Restart = 29PB1 | Corresponde ao NW 01 do plano |
| E-stop do HMI via HMI_SAFETY_FC | EL1918 3/4 (29ES2), cabeado | Não reproduzir máscara por Profinet_Error nem seleção por INT padrão |
| Overtravel (latched + bypass HMI) | EP1918 In1–4 | Recuperação por modo seguro (29SPB1 enabling, MOVISAFE), não por bypass padrão |
| Chain slack 1–4 | Não está no inventário | Lacuna: confirmar hardware e polaridade NC |
| Light guards | EP1957 (cortina do carrossel) | Muting não especificado (Yusan usava SICK SEE; TwinSAFE tem FB de muting – confirmar) |
| F_Lock_FB + Lock_Secured/EStop_Lock | Euchner MBM-EC (FSoE) | Mapear bits closed/locked/E-stop/RS_* pela configuração MGB2 |
| E-stops de nível L1–L6 e KEY REMOTE/LOCAL | Ausentes | Confirmar se o Inbound tem esses dispositivos |
| STO VTD CH1/CH2 = Safety_OK | SEW FSoE (bits a definir com a SEW) | EL2912 não equivale a CH1/CH2: são 2 áreas (carrossel / VTD+extrator+buffers). Marble não tinha STO de transportadores |
| Freio do hoist | A definir com a SEW | Marble sem lógica de freio; no Yusan Brake Enable = Safety_OK |
| ACK padrão + ACK_GL global | Restart do ESTOP; ErrAck do grupo | Separar rearme do ESTOP do ErrAck, fonte explícita de cada um |
| Safety_OK por sistema (usado por Buffer/EConveyor/VTD_HMI) | Diagnóstico do grupo → PLC | Só status, não permissão |
| Bypass_FC → Bypass_Safe | Relés 26CR7/26CR8 lidos pelo EL1918 | Não replicar; projetar modo de manutenção seguro |

Não concluível com o export: OB Main (chamadas de GateAccess_Station, consumidor de `Ln_OK`), HW config (1oo2, discrepância, passivação), valores atuais dos IDBs, programa do 1200 (vazio), FB1000 (protegido).
