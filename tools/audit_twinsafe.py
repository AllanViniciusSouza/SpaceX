"""Read-only TwinSAFE source audit; write evidence tables under docs/safety.

No safety files, CRCs, aliases, topology or physical addresses are modified.
This checks saved project data, not the installed machine or online state.
"""
from pathlib import Path
import csv
import hashlib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SAFETY = ROOT / 'TwinCAT Project1/Sys_1_Inbound'
GROUP = SAFETY / 'TwinSafeGroup1'
OUT = ROOT / 'docs/safety'
OUT.mkdir(parents=True, exist_ok=True)
hardware = ET.parse(ROOT / 'TwinCAT Project1/SpaceX.tsproj').getroot()
parents = {child: parent for parent in hardware.iter() for child in parent}
modules = {}
for element in hardware.iter('Module'):
    value = element.get('Id', '')
    if not value.startswith('#x'):
        continue
    node, names = element, []
    while node in parents:
        if node.findtext('Name'):
            names.append(node.findtext('Name'))
        node = parents[node]
    modules[str(int(value[2:], 16))] = ' > '.join(reversed(names))

aliases, channels, snapshots = [], [], []
for path in sorted(SAFETY.rglob('*')):
    if path.is_file() and path.suffix in ('.sds', '.sal', '.diagram', '.xml', '.splcproj'):
        snapshots.append([str(path.relative_to(ROOT)), hashlib.sha256(path.read_bytes()).hexdigest()])
for path in sorted((GROUP / 'Alias Devices').glob('*.sds')):
    root = ET.parse(path).getroot()
    sid = root.findtext('SDSID')
    alias = root.find('SafetyAliasDevice')
    if alias is None:
        aliases.append([path.stem, sid, 'Standard', '', '', '', '', '', 'Manual standard PLC mapping'])
        continue
    obj = alias.findtext('ObjectId')
    ack = alias.find('ComErrAck')
    aliases.append([path.stem, sid, 'FSoE', alias.findtext('ConnectionId'),
                    alias.findtext('SafeAddress'), alias.findtext('Watchdog'), obj,
                    ack.get('Type', '') if ack is not None else '',
                    modules.get(obj, 'UNRESOLVED ObjectId')])
    for io in alias.findall('.//Messages/IO'):
        channels.append([path.stem, sid, io.findtext('Direction'), io.findtext('Name'),
                         io.findtext('SafetyType'), io.findtext('DataType'),
                         io.findtext('Index'), io.findtext('SubIndex'),
                         io.findtext('BitOffsData'), io.findtext('BitOffsMessage'),
                         io.findtext('BitSize')])

def save(name, columns, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)

save('Alias_Devices.csv', ['Alias', 'SDSID', 'Type', 'ConnectionId', 'SavedSafeAddress',
                          'SavedWatchdog_ms', 'ObjectId', 'ComErrAck', 'PhysicalModule'], aliases)
save('Alias_Process_Data.csv', ['Alias', 'SDSID', 'Direction', 'Name', 'SafetyType', 'DataType',
                               'Index', 'SubIndex', 'BitOffsData', 'BitOffsMessage', 'BitSize'], channels)
save('Source_SHA256.csv', ['File', 'SHA256'], snapshots)
ns = {'s': 'http://schemas.microsoft.com/dsltools/SafetyApplicationLanguage'}
sal = ET.parse(GROUP / 'TwinSafeGroup1.sal')
print('Networks:', len(sal.findall('.//s:Network', ns)))
print('Aliases:', len(aliases), '; FSoE:', sum(row[2] == 'FSoE' for row in aliases))
print('Unresolved FSoE physical modules:', sum(row[-1].startswith('UNRESOLVED') for row in aliases))
print('Saved SafeAddress=0:', sum(row[4] == '0' for row in aliases))
print('Exported process-data entries:', len(channels))
print('Wrote evidence tables only:', OUT)
