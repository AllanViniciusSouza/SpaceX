# Yusan – o que mudou entre 08/10 e 20/10/2026

Base: export de 08/10 em `Reference_Project/*.scl` + `MAIN.pdf`, `Main_Safety_RTG1.pdf`, `Remote_Panel.pdf`.
Diff textual normalizado (sem comentários e atributos `{...}`) e datas `modified` lidas com `read_block` (UTC).
Blocos que não existiam no export de 08/10 (INPUTS, Feed_*, LGX_SM_FC, Bypass_FC…) têm só a data, sem diff.
Somente leitura – nada foi alterado no TIA.

## Mudança principal: overhang do transportador do VTD virou parada pela segurança
Cadeia completa (sistemas 1–5, `n` = sistema):

1. `CVTDn OVERHANG LEFT/RIGHT` – DI do carro do VTD, no mesmo byte dos sensores comuns do CVTD (ex. CVTD1 %I156.7 / %I156.6; tabela `IO_ET200_n`, não nas tabelas do Remote Panel).
2. `INPUTS` (padrão): `T_OH_Left_n.TOF(IN := sensor OR NOT Control_DB.VTD_Sys[n].Running, PT := T#200ms)` → `Control_DB.ECnv_Sys[n].Inputs.Overhang_Left/Right` (DB padrão).
3. `Overhang_IO_FC` (F_LAD, **novo**, 15/10) chamado na NW12 do `Main_Safety_RTG1`: copia para `Overhang_IO_DB.ECnv_n.Left/Right` (F-DB, UDT novo `F_ECnv_Overhang`).
4. `Remote_Panel` NW34/35 (novas): `ESTOP1(E_STOP := Overhang_Left/Right, ACK := #ACK)` – sem bypass, com rearme.
5. NW36 `Safety_OK` / `Safety_Ok_Conf` passam a exigir `Overhang_Left_DB.Q AND Overhang_Right_DB.Q` (nos dois ramos, inclusive sistemas 4–5).
6. `Safety_OK` → STO VTD, STO CONVEYOR VTD, STO CNV VFD (níveis/lados), Power Enable Safety Stopper e VTU Hoist Brake Enable daquele sistema.

Lado padrão:
- `Errors_Warings`: nova `REGION OVERGANG SENSORS` → `Error_Word_Overhang` (%MW848; X0/X1 = sistema 1 L/R … X8/X9 = sistema 5 L/R). Zerado junto com `Estop_Error_Word_n` no reset de E-stop e em `Error_Word_Overhang := 0`.
- `Conveyor_HMI_FB` (todas as chamadas por nível) e `Feed_ECNV`/`Feed_ECNV(1)` mostram o estado nas tags HMI antigas `HMI_CNV_Sdetect1/2`.
- Os sensores são os antigos `Sdetect1/2`, **renomeados** no UDT `Cnv_Inputs` (`Sdetect1` → `Overhang_Left`, `Sdetect2` → `Overhang_Right`). O `VTD_FB` continua usando-os como detecção de shuttle (`Shuttle_Loaded` 0..3), só para `System_no > 3`.

## Tabela por bloco
| Bloco | Modificado (UTC) | Mudança |
|---|---|---|
| Remote_Panel (FB, F_LAD) | 19/10 11:56 | +entradas `Overhang_Left/Right`, +NW34/35, Safety_OK com overhang (36 → 38 networks). UDT `F_Bypass_RemotePanel` ganhou `Overhang_Left/Right` (copiados em `Bypass assignments_1..5`), mas o FB não os usa e `Bypass_Warning` não os inclui |
| Main_Safety_RTG1 | 19/10 09:33 | Continua com 14 networks; chamadas `Remote_Panel` 1–5 recebem `Overhang_IO_DB.ECnv_n`; NW12 chama `Overhang_IO_FC` |
| Overhang_IO_FC / Overhang_IO_DB | 15/10 15:51 | Novos (5 networks, cópia padrão → F) |
| INPUTS | 19/10 13:27 | Filtro TOF 200 ms por sensor, monitoramento só com VTD em movimento (instância do sistema 4 Right chama-se `I_OH_Right_4`) |
| Errors_Warings | 19/10 09:33 | +93/−30: região overhang; parênteses em `(HMI_Box_Connected = x AND KEY REMOTE/LOCAL …) OR …` (correção de precedência AND/OR) |
| VTD_FB | 19/10 09:33 | Shuttle detect lê `Cnv_Sensors.Overhang_*`; aviso de move-to-level ganhou `OR Control_DB.ECnv_Sys[n].Running`; parênteses nos termos HMI_Reset/chave/caixa |
| OPC_Control_FB | 19/10 09:33 | Precedência do reset de watchdog corrigida; termos de HMI box 1–5 removidos |
| Order_Table_FB | 19/10 09:33 | Removido o bloco de 48 linhas de reset de watchdog |
| Conveyor_HMI_FB | 19/10 14:26 | Parâmetros `Overhang_Left/Right := "CVTDn OVERHANG …"` em todas as chamadas |
| Feed_ECNV / Feed_ECNV(1) | 19/10 14:26 / 15/10 17:12 | Overhang → `HMI_CNV_Sdetect1/2` |
| Conveyors_Transfer | 20/10 11:39 | Só renome de constantes (`T1S700MS`, `T2S100MS`) |
| LGX_SM_FC | 20/10 11:39 | Sem base anterior (conteúdo em `Arquitetura_IO.md`) |
| **EConveyor_FB** | **20/10 12:13** | **Inconsistente – não exportável.** É o bloco editado mais recente; compilar (Ctrl+B) e exportar para ver a mudança |
| Buffer_Conveyor_FB | 15/10 15:51 | Só a linha de autor |
| Main (OB1) | 15/10 15:52 | Mesmas 57 networks do `MAIN.pdf` |
| Bypass_FC, Feed_VTD_HMI_FC(_1), Feed_BCNV_*, VTD_HMI_FB, Conveyor_HMI_FB_1, Feed_ECNV_1 | 19/10 | Sem base anterior para diff |

Sem mudança de código: Barcode_Station_FB, GateAccessControl_FB, GateAccess_Station_FB, MQTT_Handler_FB, ModeManager_FB, Safety_Stops_FB, Screens, FC_Orders, Stack_Lights_FB, VTD_HMI_FB, ID_Decode_F, Set_Bit_F.

## Pontos a verificar (achados, não conclusões)
1. **Sinal padrão dentro da lógica F.** O overhang chega à segurança por DB padrão (`Control_DB`), filtrado em código padrão. Ele desliga STO, mas sem integridade de segurança (1oo1, sem discrepância/teste). Decidir se é função de segurança (sensor e entrada seguros) ou intertravamento de processo (parada controlada no programa padrão).
2. **Monitoramento só em movimento** (`OR NOT VTD_Sys[n].Running`). Com o VTD parado um pallet saliente não é visto; o trip ocorre até 200 ms depois da partida, já com o VTD em movimento.
3. **Sistemas 4–5:** os mesmos sensores significam "shuttle no lugar" no `VTD_FB` (ambos TRUE = shuttle, ambos FALSE = vazio). Se o VTD 4/5 se mover vazio, `Overhang_* = FALSE` → trip. Confirmar polaridade e uso nesses sistemas.
4. **CVTD2 com bits invertidos:** LEFT %I1275.6 / RIGHT %I1275.7. Nos outros, LEFT = .7 e RIGHT = .6. Conferir com o elétrico.
5. Bypass de overhang no UDT/F-DB sem uso – manter sem uso (ou remover).
6. `Errors_Warings`: o reset do sistema 4 usa `HMI_Box_Connected = 31..38` e `KEY … CH1(3)` (cópia do sistema 3; já existia em 08/10).
