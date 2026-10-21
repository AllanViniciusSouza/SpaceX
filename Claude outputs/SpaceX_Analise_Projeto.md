# SpaceX – Análise do projeto TwinCAT 3 (estado em 15/10/2026)

Pasta analisada: `C:\ParkplusDev\SpaceX` (somente leitura – nada foi alterado).
Análise estática: nenhum build TwinCAT foi executado.

---

## 1. Visão geral da máquina

- Armazém SpaceX, área **Inbound** (topologia "SpaceX Warehouse – Rev 9", autor Carlos Amaral, 21/09/2026).
- Áreas: carregadores (48 no total, painéis a definir), VTD estático, VTD móvel / extrator,
  transportadores buffer (níveis 1–6 com stopper), transportadores carrossel (pop-up, turntable, rolos),
  portões com Euchner MGB2, cortinas de luz no carrossel.
- VTD = elevador vertical (VRC): MOVIPRO 22 kW + motor DR2L / redutor FA77B, corrente dupla, freio.
- Redes: EtherCAT / EtherCAT P (EPP), PROFINET via EL6633 (carregadores Siemens S7‑200 SMART,
  leitores de código de barras Keyence SR, IO‑Link), HMI KEBA.
- Referência funcional: projeto Siemens TIA V20 (arquivo `.zap20`, exports SCL em `Reference_Project`,
  PDFs de MAIN, Remote_Panel e Main_Safety_RTG1). A referência tem 5 sistemas; o alvo TwinCAT usa arrays `[1..2]`.

---

## 2. Estrutura do repositório

| Item | Situação |
|---|---|
| `SpaceX.sln` | Solução ativa. Contém **apenas** `TwinCAT Project1\SpaceX.tsproj` (TwinCAT 3.1.4026.26, x64) |
| `TwinCAT Project1\Sys1_Inbound` | **PLC principal de trabalho** (porta 851) |
| `TwinCAT Project1\Main` | PLC "Main" (porta 852): só `IO_Main` + MAIN vazio |
| `TwinCAT Project1\Sys_1_Inbound` | Projeto TwinSAFE (EL6910, TwinSafeGroup1) |
| `TwinCAT Project1\Untitled1..5` | Órfãos (não referenciados no tsproj) – rascunhos PLC/Safety |
| `Main_PLC\` | Projeto antigo standalone, fora da solução (MAIN vazio + IO) |
| `SpaceX\SpaceX.tspproj` | Projeto vazio, fora da solução |
| `Reference_Project\` | 20 exports SCL + 3 PDFs da referência Siemens (somente leitura) |
| `docs\` | Documentação gerada em sessões anteriores (migração TIA, IO cards, safety, visu) |
| `tools\` | Scripts Python de inventário/validação (somente leitura sobre fontes) |
| `AGENTS.md` | Regras já existentes para agentes (ver seção 9) |
| PDFs/ESI/GSDML/msproj | Manuais SEW, desenhos elétricos (Inbound, Outbound, Main), ESI Euchner, GSDML Keyence/S7‑200, projetos MOVISUITE |

Git: remoto `github.com/AllanViniciusSouza/SpaceX`, branch `main`, 6 commits (último 23/09 "REFRESH2").
**96 entradas não commitadas** (todo o trabalho de 24/09 a 14/10: SEW, Inputs/Outputs, docs, tools,
MigrationReview, safety). **Não há `.gitignore`**: `.suo`, `_CompileInfo`, `_Boot`, `.bak`, zips e PDFs estão
versionados; `.git` = 890 MB; arquivos grandes não rastreados (`.zap20` 228 MB, `.drawio` 41 MB).

---

## 3. Solução ativa – `SpaceX.tsproj`

### Tasks
| Task | Prioridade | Ciclo | Uso |
|---|---|---|---|
| PlcTask | 20 | 10 ms | Sys1_Inbound |
| PlcTask1 | 21 | 10 ms | Main |
| PlcTask2 | 22 | 10 ms | **sem uso** |
| VISU_TASK | 30 | 200 ms | Visualização Sys1_Inbound |

### Dispositivos de I/O
- **Sys_1_Inbound (EtherCAT)** – habilitado:
  - Remotos EPP/EP: DI‑01..10 (EPP1008‑0022), ENCODER (EPP5001‑0002, SSI), DIO‑01..07 (EPP2328‑0002),
    DI‑11 (EPP1809‑0022), FDI‑01 (EP1918‑0002), FDIO‑01 (EP1957‑0022), Lock (Euchner MBM‑EC‑S1‑MLI‑3B).
  - Drives SEW: **VTD (MOVI‑C MOVIPRO)**, **C1001** e **T1301** (MOVI‑C Decentralized Electronics),
    todos com Module 1 *Standard 8 PD* + Module 2 *FSoE Safety IO 48 bit*.
  - Rack EK1200: EL1809 ×2, EL2809 ×2, EL6910, EL1918, EL2912, EL9410, EK1322 ×3, EL6633, EK1122, EL9011.
- **MAIN (EtherCAT)** – desabilitado (rack do painel Main).
- **PROFNET_SYS_1 (EL6633)** – desabilitado: chargerlevel1..7, barcodereader1..3, iolink.

### Links existentes (seção `<Mappings>`)
- VTD PI 1..8 / PO 1..8 ↔ `IO_VFDs.VTD_PI_xx / VTD_PO_xx`.
- `IO_OTHERS.Run` / `ErrorAcknowledgement` ↔ entradas standard do TwinSafeGroup1.
- `IO_Chargers.Outputs_1` ↔ chargerlevel1 (dispositivo PROFINET desabilitado).
- Conexões FSoE do EL6910 com EL1918, EL2912, EP1918, EP1957, Lock e VTD.

### Declarado mas **não linkado**
`IO_Cards` (todos os canais do rack), `IO_VFDs.VTD_WcState / VTD_EcState`, `IO_VFDs.FSoE_Slave_*`,
`IO_Chargers.Inputs_*` e `Outputs_2..8`, `IO_Main` (todo), PDs de C1001/T1301, módulos EPP remotos (sem GVL).

---

## 4. PLC `Sys1_Inbound`

### O que roda hoje (MAIN)
```
Inputs()                         // IO_* -> Control
fbVtdProcessDataTest(...)        // TEST ONLY: leitura PI / escrita PO opcional com timeout 10 min
FC_VTD_PdHmiUpdateStatus(...)    // -> GVL_HMI_VTD.stPdStatus
Outputs()                        // Control -> IO_*
```
A visualização `Visualization` é a tela de teste de process data do VTD (ligada só a `GVL_HMI_VTD`).

### Objetos preparados mas **não chamados**
| POU | Estado |
|---|---|
| `VTD_FB` | ~1.180 linhas da máquina de estados legada **comentadas**; 63 linhas ativas = região SEW (modo velocidade 200) usando `FB_SEW_Drive` |
| `FB_SEW_Drive` | Camada de comunicação MOVIKIT "Standard 8 PD": handshake PO1.15/PI1.15, decodificação PI, montagem PO, nunca libera freio sem enable |
| `Buffer_Conveyor_FB` | **Código Siemens ativo** (SinaSpeed, SCALE_X/NORM_X, `"Screen_DB_1"`, `.%X0`, `{REGION}`) |
| `Light_Bars_FB` | **Código Siemens ativo** (`"SinaSpeed_VTD_DB_1".EnableAxis`) |
| `Conveyors_Transfer`, `Barcode_Station_FB`, `Stack_Lights_FB` | Convertidos, não integrados |
| Funções de parsing (`Find*Field`, `ByteArrayToString`, …) + testes `FC_TestTIA*` | Convertidos, testes não executados |
| `DWORD_REAL` | Corpo todo comentado → sempre retorna 0 |

`MigrationReview\` (22 rascunhos, MSBuild `None`, não compilam): integração (HMI, ordens, OPC, MQTT, erros)
e segurança (GateAccess, ModeManager, Safety_Stops).

### Estruturas de dados
- `Control` (estado interno): `ECnv_Sys[1..2]`, `LCnv_Sys[1..2]`, `VTD_Sys[1..2]`, ordens, barcode, gates, `Charger_Level[2..6]`.
- `Settings`, `System_Control`, `Errors`, `CNV_HMI`, `CNV_HMI_IO`, `GVL_HMI_VTD`.
- I/O: `IO_Cards` (rack local, comentado por canal/fio/relé conforme desenho rev D), `IO_VFDs`, `IO_Chargers`, `IO_OTHERS`.
- Nomenclatura mista: legado (`VTD_Control_DUT`, `*_FB`, `*_F`, campos sem prefixo) e nova
  (`FB_`, `FC_`, `ST_`, `E_`, `i_/q_/io_`, prefixos húngaros `b/i/di/w/a/st`).

Bibliotecas: Tc2_Standard, Tc2_System, Tc3_Module (resolução `*`) + Visu. Sem Tc2_MC2 (sem NC).

---

## 5. Drives SEW e realimentação de posição

- VTD: MOVIKIT Positioning Drive, interface "Standard 8 PD" (SBusPLUS, não CiA402) – mapa de palavras
  confirmado no MOVISUITE (PO1 controle … PO7/8 posição alvo; PI1 status … PI7/8 posição real).
- `FB_SEW_Drive` cita o manual SEW 33959862 (cap. 9) para os bits; `FB_SEW_ProcessDataTest` diz que
  os bits ainda estão **pendentes de confirmação da SEW** → informação divergente entre os dois arquivos.
- Escalas/unidades (velocidade, rampa, torque, posição) **ainda não confirmadas**.
- **Contradição sobre encoder** a resolver:
  - `AGENTS.md`: DL50 ligado ao sistema SEW; "nunca assumir encoder de motor".
  - Cotação SEW 426013721 (motor do VRC): encoder absoluto **AK8W** multi‑volta (SIL2) + cartão
    **CSA31A MOVISAFE** com 2ª entrada de encoder (SSI).
  - DL50‑P2228 tem saída **SSI**; o tsproj tem um **EPP5001‑0002 (SSI) "ENCODER"**;
    conversa no WhatsApp mostra compra de encoder absoluto **AHM36B SSI**.

---

## 6. Segurança (TwinSAFE)

- Rascunho offline: `safeEstop` com 5 pares NC (discrepância 500 ms), reset por EL1918 entrada 5,
  resultados internos sem saída física. Endereços FSoE físicos ainda não atribuídos (todos 0).
- **Documentação desatualizada**: `.sal`, `.sal.diagram` e `.splcproj` mudaram depois de 08/10
  (hash diferente de `Source_SHA256.csv`); `.sal` agora tem bloco `safeOr`; aliases FSoE novos para
  C1001 e T1301 (13/10); o arquivo do alias do VTD foi renomeado.
- Saídas standard relacionadas à segurança: `BYPASS_1/2_FROM_DIGITAL_PLC_OUTPUT` (relés 26CR7/26CR8,
  lidos de volta pelo EL1918 entradas 6/8) e `IO_OTHERS.Run/ErrorAcknowledgement` – sem lógica escrita ainda.

---

## 7. Problemas e riscos encontrados (prioridade)

1. **`VTD_WcState`/`VTD_EcState` sem link** → `EcState = 0` → "Communication OK" sempre FALSE na tela de
   teste; `FB_SEW_Drive` nunca daria enable. Precisa de link no XAE (alteração de hardware → humano).
2. **Código Siemens ativo** em `Buffer_Conveyor_FB` e `Light_Bars_FB` → não compila em TwinCAT
   (já registrado como bloqueio nos docs).
3. **`VTD_FB` incompleto**: `HMI_Reset` é VAR_TEMP nunca atribuído; `Safety_OK` sem origem;
   `Motor_UP/Down/Speed` vinham da máquina de estados comentada; `LinearEnc` é TODO.
4. Carregadores inconsistentes: `Charger_Level[2..6]` × `IO_Chargers` 8 níveis × 7 devices PROFINET × 48 carregadores;
   `DWORD_REAL` vazio; ordem de bytes/REAL não confirmada.
5. Fonte de posição do VTD indefinida (seção 5).
6. Docs de safety e `TIA_POU_Migration_Status.csv` desatualizados (CSV cita `ParseShuttle_Status`, arquivo inexistente).
7. `IO_VFDs.FSoE_Slave_*` declarados como entradas standard (resto antigo; quadros FSoE não devem ser lidos pela lógica standard).
8. Lixo/órfãos: `Untitled1..5`, `Main_PLC`, `SpaceX.tspproj`, vários `.bak`, 28 `.compileinfo` (~100 MB),
   `Tc2_Utilities` em `_Libraries` sem referência, `~$...docx`, `PlcTask2` sem uso.
9. Git: muito trabalho não commitado, sem `.gitignore`, arquivos gerados versionados.

---

## 8. O que não pôde ser validado sem TwinCAT
Compilação, resolução de bibliotecas, links reais no runtime, estado online do EtherCAT/FSoE,
verificação do projeto safety, comportamento da visualização.

---

## 9. Base para as regras de edição

`AGENTS.md` já cobre: ST/TwinCAT (não TIA), SEW SBusPLUS (não CiA402), DL50, nomenclatura básica,
máquinas de estado com ENUM, arquitetura FB_SEW_Drive/FB_Positioning/FB_Axis, I/O só em Inputs/Outputs
com regions, proteção de configuração de hardware, conversão de bytes/REAL, segurança, ciclo determinístico,
TON/R_TRIG, diagnóstico, tolerância de posição, unidades, reutilização, XML mínimo, validação de build,
git seguro, comportamento do agente, idioma inglês no projeto.

Lacunas a decidir:
- Política de nomes: renomear legado (`*_DUT`, `*_FB`, `Control.VTD_Sys`) ou manter? Prefixos húngaros obrigatórios?
- Pastas editáveis × somente leitura (Reference_Project, MigrationReview, projeto safety, Main_PLC, Untitled*).
- Como tratar código Siemens em POUs compilados (comentar, excluir do build, mover para MigrationReview).
- Política para código legado comentado (ex.: 1.180 linhas em `VTD_FB`).
- Processo de promoção de rascunho de `MigrationReview` para `Compile`.
- Padrão de HMI (`GVL_HMI_<área>` + `FC_<área>HmiUpdateStatus`) e de código TEST ONLY (marcação, timeout, remoção).
- Número de sistemas (constantes em vez de `[1..2]` fixo).
- Fluxo git (branch por tarefa, quem faz commit, `.gitignore`, mensagem em inglês).
- Obrigação de atualizar `docs/` junto com cada mudança.
- Correção da regra de encoder no `AGENTS.md` conforme a resposta da seção 5.
