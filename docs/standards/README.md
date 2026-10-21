# TwinCAT 3 PLC Standards

Personal programming standards for Beckhoff TwinCAT 3 PLC projects
(IEC 61131-3 Structured Text). Written for AI coding agents.

Apply them in every TwinCAT project, unless the project's own instructions
say otherwise.

---

# Files

| File | Content |
| --- | --- |
| 01_Naming_And_Variables.md | Object names, variable prefixes, BOOL vocabulary, units, constants, enums, declaration comments |
| 02_Folder_Organization.md | Repository layout, PLC project folders, where each new object goes, .plcproj registration |
| 03_Code_Structure.md | Header comment, declaration layout, regions, formatting, latches, timers, state machines, diagnostics, MAIN cycle |
| 04_IO_And_HMI_Architecture.md | I/O GVLs, Inputs/Outputs, GVL Control, HMI contract (Command/Status/Settings), device communication layers |

Read all four before writing or changing PLC code.

---

# Precedence

1. Explicit instruction from the user in the current task.
2. The project's AGENTS.md (project facts: devices, process data, I/O,
   safety, legacy objects).
3. These standards.
4. TwinCAT / IEC 61131-3 defaults.

---

# General rules

- Use Beckhoff TwinCAT 3 Structured Text. Do not use Siemens TIA syntax.
- Write all code, identifiers, comments, documentation and HMI texts in
  English.
- Apply these standards to new objects and to new variables or fields added
  to existing objects.
- Do not rename existing or legacy objects to match these standards.
- Correctness and readability first. Line count last.
- Never change safety logic, I/O hardware configuration or motion limits
  without explicit instruction.
- Never invent process-data words, bit meanings, units, byte order or
  encoder formats. Use documented values only and cite the source.
- Do not claim that a project compiles unless a real TwinCAT build ran.

---

# Quick reference

```
FB_<Area>_<Name>          function block         FB_SEW_VelocityDrive
FC_<Area>_<Name>          function               FC_SEW_MovikitModeName
ST_<Area>_<Name>          structure              ST_SEW_ProcessInput8
E_<Area>_<Name>           enumeration            E_SEW_MovikitMode
GVL_<Area>                global variable list   GVL_HMI_VTD
IO_<Group>                physical I/O GVL       IO_VFDs
MAIN, Inputs, Outputs, Control                   fixed framework names

i_  q_  io_               VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT
b by w dw i ui di udi r lr s t e a st fb          type prefixes
ton tof tp rtrig ftrig    timer / edge instances
UPPER_SNAKE_CASE          VAR CONSTANT
_mm _mm_s _mm_s2 _A _pct _0p1pct                 unit suffixes

{region "<Name>"} ... {endregion}                body sections
Inputs() first, Outputs() last                   MAIN cycle
HMI -> GVL_HMI_<Area> only                       HMI contract
```
