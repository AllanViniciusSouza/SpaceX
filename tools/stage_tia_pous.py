"""Stage missing SCL routines as NON-COMPILED TwinCAT review objects.

This is a lexical preparation tool, not a Siemens-to-Beckhoff compiler.
It never promotes files to Compile, maps hardware, or replaces existing POUs.
Run after reviewing the exports; see docs/TIA_Missing_Blocks.md.
"""
from pathlib import Path
import csv
import hashlib
import re
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLC = ROOT / 'TwinCAT Project1/Sys1_Inbound'
PROJECT = PLC / 'Sys1_Inbound.plcproj'
NS = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
SAFETY = {'GateAccessControl_FB', 'GateAccess_Station_FB',
          'ModeManager_FB', 'Safety_Stops_FB'}
TOKEN = re.compile(r"//[^\n]*|\(\*.*?\*\)|'(?:\$.|''|[^'])*'|\{[^}]*\}|\"[^\"\n]*\"|[^/'\"{]+|.", re.S)


def identifier(name):
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    return ('TIA_' if not name or name[0].isdigit() else '') + name


def prepare(text):
    parts = []
    for match in TOKEN.finditer(text):
        token = match.group()
        if token.startswith('//') or token.startswith('(*'):
            # Original commentary remains in the immutable SCL reference.
            parts.append('\n' * token.count('\n'))
        elif token.startswith('{'):
            parts.append(' ')
        elif token.startswith("'"):
            parts.append(token)
        elif token.startswith('"'):
            parts.append(identifier(token[1:-1]))
        else:
            token = re.sub(r'#(?=[A-Za-z_])', '', token)
            token = re.sub(r'\bTON_TIME\b', 'TON', token)
            token = re.sub(r'\bTOF_TIME\b', 'TOF', token)
            token = re.sub(r'\bTP_TIME\b', 'TP', token)
            parts.append(token)
    text = ''.join(parts)
    text = re.sub(r'^\s*(VERSION|AUTHOR|FAMILY|NAME)\s*:.*$', '', text, flags=re.M)
    text = re.sub(r'^\s*(REGION\b[^\n]*|END_REGION)\s*$', '', text, flags=re.M)
    return '\n'.join(line.rstrip() for line in text.strip().splitlines()) + '\n'


def main():
    tree = ET.parse(PROJECT)
    compiled = {}
    for item in tree.findall('.//m:Compile', NS):
        path = PLC / item.attrib['Include'].replace('\\', '/')
        if path.suffix == '.TcPOU':
            obj = ET.parse(path).find('POU')
            compiled[obj.attrib['Name'].lower()] = path
    objects = {}
    for path in sorted((ROOT / 'Reference_Project').glob('*.scl')):
        source = path.read_text(encoding='utf-8-sig')
        for match in re.finditer(r'^\s*(FUNCTION_BLOCK|FUNCTION)\s+"([^"\n]+)".*?^\s*END_\1\b', source, re.M | re.S):
            kind, name = match.group(1, 2)
            content = match.group().strip()
            if name in objects and objects[name][1] != content:
                raise ValueError(f'Conflicting definitions: {name}')
            objects[name] = (kind, content, path.name)

    project = PROJECT.read_text(encoding='utf-8-sig')
    entries, rows = [], []
    for name, (kind, source, origin) in sorted(objects.items()):
        digest = hashlib.sha256(source.encode()).hexdigest()
        if name.lower() in compiled:
            rows.append([name, kind, 'PLC source (build unverified)', str(compiled[name.lower()].relative_to(PLC)), origin, digest])
            continue
        category = 'SafetyReview' if name in SAFETY else 'IntegrationReview'
        path = PLC / 'MigrationReview' / category / f'{name}.TcPOU'
        adapted = prepare(source)
        declaration, body = re.split(r'^\s*BEGIN\s*$', adapted, maxsplit=1, flags=re.M)
        body = re.sub(r'\s*END_' + kind + r'\s*$', '', body).strip()
        # Keep unknown types/globals explicit. Do not disguise them as valid adapters.
        banner = (f'// MIGRATION DRAFT: not included in PLC compilation.\n'
                  f'// Reference: Reference_Project/{origin}, object {name}.\n'
                  '// Types, globals, calls, units and behavior require manual reconciliation.\n'
                  '// See docs/TIA_Missing_Blocks.md before importing as PLC code.\n')
        if name in SAFETY:
            banner += '// SAFETY REVIEW REQUIRED: not a TwinSAFE implementation.\n'
        guid = uuid.uuid5(uuid.NAMESPACE_URL, f'SpaceX/TIA/MigrationReview/{name}')
        xml = (f'<?xml version="1.0" encoding="utf-8"?>\n<TcPlcObject Version="1.1.0.1">\n'
               f'  <POU Name="{name}" Id="{{{guid}}}" SpecialFunc="None">\n'
               f'    <Declaration><![CDATA[{banner}{declaration.strip()}\n]]></Declaration>\n'
               f'    <Implementation><ST><![CDATA[{banner}{body}\n]]></ST></Implementation>\n'
               '  </POU>\n</TcPlcObject>\n')
        ET.fromstring(xml)
        # Review work must not be overwritten on subsequent runs.
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(xml, encoding='utf-8', newline='\r\n')
        relative = str(path.relative_to(PLC)).replace('/', '\\')
        if f'Include="{relative}"' not in project:
            entries.append(f'    <None Include="{relative}" />')
        rows.append([name, kind, category + ' (NOT compiled)', relative, origin, digest])
    if entries:
        project = project.replace('  <ItemGroup>', '  <ItemGroup>\n' + '\n'.join(entries) + '\n', 1)
        PROJECT.write_text(project, encoding='utf-8', newline='\r\n')
    with (ROOT / 'docs/TIA_POU_Migration_Status.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Name', 'Kind', 'Status', 'Target', 'Reference', 'SHA256'])
        writer.writerows(rows)
    print(f'{len(rows)} reference routines accounted for; {len(entries)} review items added.')


if __name__ == '__main__':
    main()
