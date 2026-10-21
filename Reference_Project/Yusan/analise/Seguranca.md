# Yusan (20/10) – segurança e modos (insumo para TwinSAFE, NÃO é lógica validada)

Método: parser de FlgNet sobre `../xml/*.xml` dos blocos F (expressões booleanas por network), endereços de `../tags/_all_tags.csv`,
comparação com os PDFs de 08/10 (`Reference_Project/Main_Safety_RTG1.pdf`, `Remote_Panel.pdf`) e com `../../Marble/analise/Seguranca.md`.
Qualquer uso no SpaceX exige análise e verificação humana (AGENTS.md, seção Safety).

## 1. Main_Safety_RTG1 (FB, F_FBD, 14 networks – estrutura igual a 08/10)
| NW | Lógica reconstruída |
|---|---|
| 1 | `Main_Panel`: `Estop_Cabinet_Ch1 := "EMERGENCY STOP (CABINET) - CH1" ∧ Lock_Secured_x_OK/EStop_Lock_x_OK de RP1–5 ∧ F_Lock 7/8/11/12 (Lock_Secured_OK ∨ Bypass.Main_Panel.Lock_Secured_n, ∧ EStop_Lock_OK)`; `Reset_Cabinet := "EMERGENCY STOP RESET (CABINET)" ∨ Bypass_Safe.Main_Panel.ACK` |
| 2–3 | `HMI_SAFETY_FC` ×2 (HMI 1/2), 5 sistemas: `Pressed_n := ¬HMI_EStop ∧ ¬Profinet_Error ∧ Local_Mode ∧ (n1 ≤ Box ≤ n8)`; `Reset_Comissioning_n := faixa ∧ Screen_DB_1.Reset_Comissioning[k]` |
| 4–8 | `Remote_Panel` 1–5: `Estop := "E-STOP (CABINET) - CH1(n)" ∧ Main_Panel_OK ∧ ¬HMI_1/2_Pressed_n`; `Reset := "RESET (CABINET)(n)" ∨ Bypass_Safe.Main_Panel.ACK ∨ reset do painel principal ∨ HMI Reset_Comiss_n`; sistemas 4–5 com `TRUE` em Light Guards, Gate_2, EStop_Lock_2, Lock_Secured_2; **novo: `Overhang_Left/Right := Overhang_IO_DB.ECnv_n`** |
| 9 | `L1_OK … L8_OK` (memória padrão) `:= Ln_OK de RP1–5 ∧ Main_Panel_OK ∧ L(n-1)_OK de RP1–5 ∧ ¬Ln_Estop ∧ ¬Shuttle_EStop_All [∧ Lock_x_Estop_CH1 em L1–L3]`. **L6 usa `Remote_Panel_DB_5.L4_OK`** no lugar de L5 (erro de digitação provável) |
| 10 | `F_Lock_FB` ×12; ACK = `Remote_Panel_DB_n.ACK` (locks 1–6, 9, 10) ou **`Bypass_Safe.Main_Panel.ACK`** (locks 7, 8, 11, 12) |
| 11 | `#Safety_OK := RP1 ∧ RP2 ∧ RP3` – **RP4 e RP5 fora** (igual a 08/10) |
| 12 | `Bypass assignments_0..5` + **`Overhang_IO_FC` (novo)** |
| 13 | `ACK_GL(ACK_GLOB := Main_Panel.ACK ∨ RP1..5.ACK ∨ Bypass_Safe.Main_Panel.ACK ∨ HMI Reset_Comiss_1..5)` |
| 14 | `"RESET PLC HMI - CH1/CH2"` := mesma expressão do ACK |

## 2. Remote_Panel (FB, F_LAD, 38 networks; 36 em 08/10)
- NW1 `ACK := Reset`. NW2–8: overtravel, E-stop do painel, chain slack 1–4 (TOF 200 ms) → `ESTOP1(E_STOP := sinal ∨ Bypass.sinal)`.
- NW9–18: light guards CX101/CX201 com muting **SICK Safe Entry Exit (FB1000)**: TP 6 s (UK) / 4,8 s (EURO) conforme `Material_Selection`; `I_S_ESPE_Channel_1 = I_S_ESPE_Channel_2 =` o mesmo sinal derivado do CH1; `Override := Bypass."Light Guards CXx01 - CH1"`; material 1000/800 mm, 167 (velocidade), distância 200.
- NW19–32: Gate_1/2, Lock_Secured_1/2, EStop_Lock_1/2, E-STOP L1–L8 → ESTOP1 com bypass. NW33 `Ln_OK`, `EStop_Levels_OK`.
- **NW34–35 (novas): `ESTOP1(E_STOP := Overhang_Left/Right)` sem bypass.**
- NW36 `Safety_OK := TOF 2 s( OT ∧ Cab ∧ CS1–4 ∧ Levels ∧ Gate_1 ∧ Lock1 ∧ Overhang L/R ∧ [LG1 ∧ LG2 ∧ Gate_2 ∧ Lock2 ∨ 4 ≤ ID ≤ 5] )`; `Safety_Ok_Conf` = mesma expressão sem atraso.
- NW37 `Bypass_Warning` = OR de overtravel, E-stop painel, chain slack, light guards (não inclui gates, locks, níveis).
- NW38: todos os STO (VTD, CONVEYOR VTD, CNV VFD por grupo de níveis/lado), Power Enable Safety Stopper e VTU Hoist Brake Enable CH1/CH2 `:= Safety_OK` (hoist brake atribuído duas vezes).

## 3. Achados (verificar online / com o time – não conclusões)
| # | Achado | Onde |
|---|---|---|
| a | **Bypass de porta/trava do sistema 1 nunca é desfeito por código.** No `Bypass_FC` (REGION SAFETY GATES) o `ELSE … := FALSE` está comentado só para GATE 1 e GATE 2 do sistema 1; sistemas 2–5 resetam. Depois do primeiro ciclo de acesso, `Bypass.Remote_Panel_1.Gate_1/2` e `Lock_Secured_1/2` ficam TRUE → copiados para `Bypass_Safe` → ESTOP1 das portas do sistema 1 sempre OK, e o erro de porta no `Errors_Warings` também fica mascarado | `scl/Bypass_FC.scl` linhas ~610–630 |
| b | Overhang = sinal padrão dentro da lógica F (ver `Mudancas_20-10.md`) | INPUTS → Control_DB → Overhang_IO_FC |
| c | Resets vindos do HMI/padrão: `Screens`: `Bypass.Main_Panel.ACK := Reset_Comissioning` (%M70.0) → `Bypass_Safe.Main_Panel.ACK` reseta Main Panel, todos os Remote Panels, locks 7/8/11/12 e ACK_GL | Screens.scl:267, NW1/4–8/10/13 |
| d | E-stop do HMI portátil só atua com `Local_Mode` (chave) e é ignorado com `Profinet_Error` | HMI_SAFETY_FC |
| e | `Safety_OK` global (NW11) sem RP4/RP5 | NW11 |
| f | Muting: os dois canais ESPE do FB SICK recebem o mesmo sinal (avaliação 2 canais anulada); override por bypass padrão (`Bypass_FC`: erro do transportador ∧ comando HMI) | Remote_Panel NW13/18, Bypass_FC |
| g | E-stops (painel, níveis, travas) aceitam `∨ Bypass.x` no ESTOP1; nenhum código padrão exportado escreve esses bypass – mas o caminho existe | Remote_Panel, Main_Panel |
| h | `L6_OK` com `Remote_Panel_DB_5.L4_OK` | NW9 |
| i | Freio: `VTU HOIST BRAKE SAFETY ENABLE EDM FEEDBACK` (%I514.7 no sistema 1) e EDM dos stoppers existem nas tags, mas nenhum bloco exportado os lê | tags IO_Remote_Panel_n |
| j | Para Logistex: `PLC_E-Stop := System_DB_1.Error AND System_DB_2.Error AND System_DB_3.Error` (só TRUE com os três em erro – conferir se deveria ser OR) | LGX_SM_FC |

## 4. Diferenças em relação ao Marble (ver `../../Marble/analise/Seguranca.md`)
- Yusan tem `Main_Panel` (E-stop do armário principal + travas do lado esquerdo 7/8/11/12), 5 Remote Panels, 12 travas, 8 níveis, `Local_Mode` no HMI_SAFETY_FC, STO por grupo de transportadores, Power Enable dos stoppers, Brake Enable, `Safety_Ok_Conf`, muting SICK e overhang.
- Marble: 2 painéis, 3 travas, 6 níveis, só STO do VTD, sem muting, `Safety_OK` = AND de todos os painéis.
- Igual nos dois: ESTOP1 por dispositivo com `∨ Bypass`, caminho `Bypass_FC` (padrão) → `Bypass_Safe` (F), ACK global com fontes padrão, E-stop do HMI mascarado por Profinet_Error.

## 5. Insumo para TwinSAFE (validar por humano)
Complementa a tabela da seção 6 do Marble:
| Função no Yusan | Sugestão para o SpaceX |
|---|---|
| Overhang no Safety_OK | Decidir: função de segurança (sensor seguro em EL1918/EP1918) ou intertravamento padrão com parada controlada (MOVIKIT). Não copiar o caminho padrão → F |
| STO por grupos de transportadores + Power Enable stoppers | Mapear para as áreas TwinSAFE do plano (carrossel / VTD+extrator+buffers) |
| Brake Enable = Safety_OK, sem EDM | Definir com a SEW (MOVISAFE/brake control) e incluir realimentação |
| Muting SICK SEE (UK/EURO) | Bloco de muting TwinSAFE com dois canais reais; parâmetros de material só como referência funcional |
| Main_Panel + reset por HMI | Reset só por botoeira física; HMI apenas diagnóstico |
| Bypass de portas pelo GateAccess (ModeManager) | Não replicar; acesso por trava Euchner MBM-EC + modo seguro |
