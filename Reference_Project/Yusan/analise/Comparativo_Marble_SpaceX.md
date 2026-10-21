# Marble + Yusan → SpaceX: o que usar de cada um

## Papel de cada referência
| | Marble (`../../Marble/`) | Yusan 20/10 (esta pasta) |
|---|---|---|
| Sistemas | 2 | 5 |
| Níveis | buffers 2..6, `Charger_Level[2..6]` | 8, nível 1 = infeed/outfeed Logistex |
| Pedidos | `Order_Table_VTD_FB` + `Order_Table_Buffers_FB` (separados) | `Order_Table_FB` único |
| Segurança | 2 Remote Panels, 3 travas, só STO do VTD | Main Panel + 5 Remote Panels, 12 travas, STO por grupo de transportadores, stoppers, freio, muting SICK, **overhang** |
| Integração externa | WMS (StepTable/OPC) | WMS + **Logistex** (handshake infeed/outfeed, status) |
| Export | OB1, Errors_Warings e IDB do OPC_Control **inconsistentes** | OB1 e Errors_Warings OK; **EConveyor_FB inconsistente** |
| Atualidade | 15/10 | 20/10 (correções de reset/watchdog, overhang) |

Regra prática: **estrutura e dimensionamento vêm do Marble** (mais próximo do SpaceX); **lógica corrigida e funções novas vêm do Yusan 20/10**. Os drafts em `Sys1_Inbound/MigrationReview/*` foram feitos a partir do Yusan antigo – revisar contra esta versão antes de promover.

## SpaceX hoje (Control.TcGVL de 20/10)
1 VTD + `ECnv` + `LCnv[1..6]` + carrossel (`Turn_Table`, `TBCnv`, `Pop_Up_Cnv[1..2]`, `Roller_Cnv[1..5]`, `Chain_Cnv`), `VTD_Order_Table` + `Carousel_Order_Table`, `VTDBarcode_Station[1..3]`, `Gate_Station[1..2]`, `Charger_Level[2..6]`.
`Settings.TcGVL` ainda está `[1..2]` para VTD/ECnv e com `LCnv: ARRAY[1..] OF …` incompleto. Código indexado por sistema (`VTD_Sys[n]`, `LCnv_Sys[n]`) dos dois projetos precisa virar instância única.

## Bloco a bloco
| Função | Fonte | Observação para o SpaceX |
|---|---|---|
| VTD_FB | Marble (estrutura = VTD_FB comentado do SpaceX) + correções Yusan | Trazer do Yusan: `OR ECnv.Running` no aviso de move-to-level e parênteses nos termos de reset/chave. Detecção de shuttle (`System_no > 3`) não se aplica, a menos que o SpaceX tenha shuttle no VTD |
| EConveyor_FB | **Pendente** | Compilar o Yusan e exportar (editado 20/10 12:13); comparar com Marble antes de fazer o `EConveyor_FB` com `FB_SEW_VelocityDrive` |
| Buffer_Conveyor_FB | Yusan (sem mudança 08→20/10; o Marble difere, similaridade 0,56) | Já existe em `POUs/Conveyors`; restaurar `Time_CheckPallet/NoPallet := T#2S` |
| Conveyors_Transfer | Yusan (nomes de constantes) | Trocar ID string por `ID := 120000 + lev*100 + sys` |
| Ordens | Marble (VTD/Buffers separados ↔ `VTD_Order_Table`/`Carousel_Order_Table`) | Do Yusan: remoção do reset de watchdog duplicado no Order_Table e precedência corrigida no `OPC_Control_FB` |
| OPC_Control_FB | Yusan 20/10 | Executor interno; Marble com IDB inconsistente |
| Errors_Warings | Yusan (única fonte exportada) | Padrão: palavras de erro por sistema, zeradas no reset de E-stop. Não herdar a cópia sistema 4 = sistema 3 |
| INPUTS | Yusan (filtro TOF 200 ms dos overhang) | Só se o SpaceX tiver sensores de overhang no ECnv – não aparecem hoje em `IO_Cards.TcGVL` |
| Handshake LGX (`Handshake_Infeed_FC`, `Handshake_Outfeed_FC`, `VTD_Status_Update_FC`, `LGX_SM_FC`) | Yusan | Modelo de contrato para VTD ↔ carrossel/sistemas externos (ReadyToSend / ReadyToReceive / InProgress / Occupied + status). Implementar o watchdog que no Yusan é placeholder |
| Feed_* / Conveyor_HMI_FB / VTD_HMI_FB | Marble (2 sistemas) + campos novos do Yusan | GVL_HMI do SpaceX; exibir overhang com nome próprio (não `Sdetect`) |
| Local_Mode_FC, HMI_SAFETY_FC, chaves REMOTE/LOCAL | Yusan | Só se o SpaceX tiver HMI portátil por caixa; E-stop de HMI cabeado (TwinSAFE), sem máscara |
| Main_Panel / Remote_Panel / F_Lock_FB / Bypass | Ambos – **só insumo** | Ver `Seguranca.md` (Yusan) e `../../Marble/analise/Seguranca.md`. Não replicar bypass padrão → F nem resets pelo HMI |
| Muting das cortinas | Yusan (SICK SEE, UK/EURO) | Referência funcional para a cortina do carrossel (EP1957) |
| Carregadores | Marble (`Charger_Level[2..6]`) | Yusan tem 8 painéis × 3 carregadores |
| MQTT/TCP, barcode, light bars | Iguais | Tc3_IotBase/Tc3_JsonXml, Tc2_TcpIp |

## Não herdar (Yusan, além da lista do Marble)
`Bypass_FC` com reset de bypass das portas do sistema 1 comentado; overhang padrão dentro do Safety_OK; `Safety_OK` global sem RP4/RP5; `L6_OK` com `RP5.L4_OK`; E-stop de HMI dependente de `Local_Mode`; `Fault_Handshake := FALSE`; `PLC_E-Stop` como AND dos três sistemas; bits de overhang do CVTD2 trocados (conferir elétrico).

## Perguntas para fechar antes de portar
1. O ECnv do SpaceX tem sensores de overhang? Função de segurança ou de processo?
2. O VTD do SpaceX transporta shuttle (detecção de shuttle do Yusan 4–5)?
3. Há interface tipo Logistex (outro PLC/WMS com handshake por sinais)? Qual protocolo (ADS, OPC UA, EtherCAT bridge)?
4. Settings indexado `[1..2]` x Control escalar – qual fica?
5. Exportar `EConveyor_FB` e os blocos do PLC_HMI depois de compilar o Yusan.
