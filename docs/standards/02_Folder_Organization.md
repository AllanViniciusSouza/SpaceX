# 02 - Folder Organization

---

# Repository root

```
<Repository>/
├─ AGENTS.md                        Project facts and rules for agents (entry point)
├─ <Solution>.sln
├─ <TwinCAT project>/               .tsproj, PLC projects, TwinSAFE project
├─ docs/                            Project documentation (Markdown)
│  ├─ standards/                    These standards
│  ├─ safety/                       Safety review, alias lists, checksums
│  └─ visu/                         Screen previews and HMI documentation
├─ tools/                           Offline helpers (Python): inventory, validation, generators
├─ Reference_Project/               Read-only comparison baseline
└─ _backup_<what>_<yyyymmdd_hhmm>/  Backup taken before a generated or bulk change
```

Rules:

1. AGENTS.md at the root holds the project facts. These standards hold the
   generic rules.
2. `Reference_Project/` is read-only. Never change it as part of a
   conversion or refactor.
3. Before a generated or bulk change (for example rewriting visualization
   XML), copy the affected folder to `_backup_<what>_<yyyymmdd_hhmm>/`.
   Backups are not part of the solution.
4. Reference documents (manuals, datasheets, drawings, ESI/GSDML files) stay
   outside the PLC project folder. Code cites them by document number and
   chapter.
5. `tools/` scripts run offline and never change hardware configuration.

---

# PLC project

```
<PlcProject>/
├─ POUs/
│  ├─ MAIN.TcPOU                    Cycle entry point
│  ├─ Inputs.TcPOU                  Only reader of physical inputs
│  ├─ Outputs.TcPOU                 Only writer of physical outputs
│  ├─ <Vendor>/                     Device communication layers       (SEW/)
│  ├─ <MachineFunction>/            Machine logic per function        (VTD/, Conveyors/)
│  └─ System/                       Shared logic
│     ├─ Functions/                 Generic helpers (parsing, conversion)
│     └─ Tests/                     Test functions FC_Test*
├─ DUTs/
│  ├─ <Vendor>/                     Process images, decoded status, vendor enums
│  ├─ <MachineFunction>/            Device data structures stored in Control
│  ├─ HMI/                          All HMI contract structures
│  └─ System/                       Shared types
├─ GVLs/
│  ├─ Control.TcGVL                 Internal state of all devices
│  ├─ <System GVLs>                 Settings, errors (system-wide)
│  ├─ IO/                           IO_<Group>: physical I/O only
│  └─ HMI/                          GVL_HMI_<Area>: HMI contract only
├─ VISUs/                           Screens, frames (FP_*), image pool
└─ MigrationReview/                 Drafts and review copies, NOT compiled
```

Rules:

1. Use the same area folder names in POUs, DUTs and GVLs
   (POUs/SEW <-> DUTs/SEW, POUs/VTD <-> DUTs/VTD).
2. `<Vendor>` folder: code that talks to a device type and can be reused in
   any machine (communication layer, process image, status decoding).
3. `<MachineFunction>` folder: logic and data of one machine part
   (the owner of an axis, a conveyor, a station).
4. POUs root: only MAIN, Inputs and Outputs.
5. GVLs root: only Control and system-wide GVLs. Physical I/O only in
   GVLs/IO. HMI variables only in GVLs/HMI.
6. DUTs root: nothing new. Every new type goes to an area folder.
7. A type used only by the HMI goes to DUTs/HMI, even when it belongs to a
   device.
8. File name = object name. One object per file.
9. Do not create a folder for a single object when an existing area fits.
10. Drafts, review copies and code that must not compile go to
    MigrationReview/.

---

# Where does a new object go

| New object | Folder |
| --- | --- |
| Communication layer for a device type (drive, I/O module) | POUs/<Vendor> |
| Process image, decoded status, enum of that device type | DUTs/<Vendor> |
| Logic of a machine part (owner of the axis or station) | POUs/<MachineFunction> |
| Data structure of a device stored in Control | DUTs/<MachineFunction> |
| HMI Command / Status / Settings / Summary structure | DUTs/HMI |
| HMI GVL | GVLs/HMI/GVL_HMI_<Area> |
| Physical I/O variables | GVLs/IO/IO_<Group>, plus a region in Inputs or Outputs |
| HMI status update function | Next to the FB it reads |
| Generic helper function | POUs/System/Functions |
| Test function | POUs/System/Tests |
| Test-only FB (commissioning) | Area folder, marked TEST ONLY in the header |
| Draft, not compiled | MigrationReview/ |
| Screen | VISUs/<Area> or VISUs/<Area>_<Purpose> |
| Frame / faceplate | VISUs/FP_<Name> |

---

# .plcproj registration

TwinCAT compiles only the files registered in the .plcproj.

1. Register every new POU, DUT and GVL as a Compile item in the .plcproj of
   its PLC project, with the folder path:

   ```
   <Compile Include="POUs\SEW\FB_SEW_VelocityDrive.TcPOU">
     <SubType>Code</SubType>
   </Compile>
   ```

2. Register a new folder as a Folder item:

   ```
   <Folder Include="POUs\SEW" />
   ```

3. Drafts in MigrationReview are `None` items, never `Compile` items.
4. Edit the .plcproj with minimal diffs. Do not reformat or regenerate it.
5. Copy the exact item format (SubType, attributes) from existing entries
   of the same file type in that .plcproj.

---

# Documentation

1. One Markdown file per topic in docs/.
2. When behavior, interfaces or open points change, update the related doc
   in the same change.
3. Every doc lists its open points (to confirm, to link, to test).
