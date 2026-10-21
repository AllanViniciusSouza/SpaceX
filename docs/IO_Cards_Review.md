# IO Cards Review

Source: `INBOUND VTD ELECTRICAL DRAWING_9_17_26.pdf`, revision D.
Scope: the Inbound local PLC rack. Remote EPP/EP modules, drive process data,
chargers and communication modules are excluded. Use a separate `IO_Remote`
GVL when remote module signals are implemented; none are added by this change.

## Standard cards

| Card | Drawing sheet / PDF page | Channels |
| --- | --- | --- |
| DI-01 / EL1809 / 23.0-1 | 24.0 / 92 | 16 assigned inputs |
| DI-02 / EL1809 / 23.0-2 | 25.0 / 94 | 16 assigned inputs |
| DO-01 / EL2809 / 23.0-3 | 26.0 / 95 | CH01-09 assigned; CH10-16 spare |
| DO-02 / EL2809 / 23.0-4 | 27.0 / 97 | CH01-14 spare; UPS remote on/off CH15; backup stop CH16 |

Existing assigned signal names and types are retained. Each standard channel
now has a channel and wire reference; outputs also identify their relay.
Twenty-one spare output declarations complete the two EL2809 cards.
Declaration order does not establish physical links. No hardware links,
PDO configuration, safety logic or output-writing logic were changed.

## Corrections to review

- DI-01 CH01 is **8RS1 redundancy OK** in the drawing. Consider renaming
  `REDUNDANCY_OK_8PS1` to `REDUNDANCY_OK_8RS1`, updating consumers and links together.
- DO-02 UPS commands must link to **CH15 and CH16**. The previous GVL had
  only those two declarations, without channel references.
- Sheet 27.0 labels the tenth channel wire **27.27** and relay **27CR27**.
  Verify this apparent numbering inconsistency against the panel; the GVL
  preserves the drawing labels in its comment.

## Safety card inventory for human review

Sheet 29.0 (PDF page 99), FDI-01 / EL1918:

| Channel | Drawing signal |
| --- | --- |
| 1 | Door emergency stop, 29ES1, first channel |
| 2 | Door emergency stop, 29ES1, second channel |
| 3 | HMI emergency stop, 29ES2, contacts 9-7 |
| 4 | HMI emergency stop, 29ES2, contacts 6-8 |
| 5 | Door emergency-stop reset, 29PB1 |
| 6 | PLC bypass 1 relay contact, 26CR7 |
| 7 | HMI enabling switch, 29SPB1 |
| 8 | PLC bypass 2 relay contact, 26CR8 |

Sheet 30.0 (PDF page 101), FDO-01 / EL2912: CH1 drives 30SCR1
(VFD STO group 1); CH2 drives 30SCR2 (VFD STO group 2).

The three existing safety-related BOOL declarations were retained unchanged.
`EMERGENCY_STOP_ON_HMI` does not identify which of the two physical HMI
channels it represents. Resolve that ambiguity in the safety design before
linking it. No additional safety channels or STO outputs were exposed as
ordinary PLC controls. Any PLC status mirrors must come from a reviewed
TwinSAFE diagnostic interface and must not replace validated safety logic.

## Validation

XML parsing, declaration uniqueness and preservation of existing names/types
were checked. Channel order was compared visually with the drawing.
TwinCAT compilation and physical channel verification remain pending.
