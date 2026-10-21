"""Offline structural checks only; this does not compile or execute ST."""
from pathlib import Path
import csv
import hashlib
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLC = ROOT / 'TwinCAT Project1/Sys1_Inbound'
NS = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
project = ET.parse(PLC / 'Sys1_Inbound.plcproj')
symbols, compiled, review = {}, set(), set()
for kind in ('Compile', 'None'):
    for item in project.findall(f'.//m:{kind}', NS):
        path = PLC / item.attrib['Include'].replace('\\', '/')
        if kind == 'Compile' or 'MigrationReview' in path.parts:
            assert path.is_file(), f'Missing project item: {path}'
        if kind == 'Compile':
            assert 'MigrationReview' not in path.parts, f'Draft compiled: {path}'
            assert path not in compiled, f'Duplicate compile item: {path}'
            compiled.add(path)
        elif 'MigrationReview' in path.parts:
            assert path not in review, f'Duplicate review item: {path}'
            review.add(path)
        if path.suffix in ('.TcPOU', '.TcDUT', '.TcGVL') and path.exists():
            tree = ET.parse(path)
            obj = next(iter(tree.getroot()))
            name = obj.attrib['Name'].lower()
            assert name not in symbols, f'Duplicate object name: {name}'
            symbols[name] = path
            if path in review:
                assert 'MIGRATION DRAFT' in obj.findtext('Declaration')
                assert obj.findtext('Implementation/ST').strip(), f'Empty draft: {path}'

reference = {}
for path in (ROOT / 'Reference_Project').glob('*.scl'):
    source = path.read_text(encoding='utf-8-sig')
    for m in re.finditer(r'^\s*(FUNCTION_BLOCK|FUNCTION)\s+"([^"\n]+)".*?^\s*END_\1\b', source, re.M | re.S):
        name = m.group(2)
        digest = hashlib.sha256(m.group().strip().encode()).hexdigest()
        assert name not in reference or reference[name] == digest, f'Conflicting source: {name}'
        reference[name] = digest
with (ROOT / 'docs/TIA_POU_Migration_Status.csv').open(encoding='utf-8', newline='') as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == len(reference), 'Status inventory is incomplete'
assert {r['Name'] for r in rows} == set(reference)
for row in rows:
    assert row['SHA256'] == reference[row['Name']], f'Stale inventory: {row["Name"]}'
    path = PLC / row['Target'].replace('\\', '/')
    assert path == symbols[row['Name'].lower()]
    if 'NOT compiled' in row['Status']:
        assert path in review and path not in compiled
    else:
        assert path in compiled
for path in (PLC / 'MigrationReview').rglob('*.TcPOU'):
    assert path in review, f'Unregistered draft: {path}'

active_names = ('RemovePlusSign', 'FindBoolField', 'FindIntField',
                'FindINTFieldFragmented', 'FindDINTFieldFragmented',
                'ByteArrayToString', 'FC_TIAScalarToken', 'FC_TIAParseDINT',
                'FC_TestTIAParsing')
for name in active_names:
    path = symbols[name.lower()]
    assert path in compiled
    text = ET.parse(path).find('POU').findtext('Implementation/ST')
    # Ignore comments/string literals when checking platform leftovers.
    code = re.sub(r"//[^\n]*|'(?:\$.|''|[^'])*'", ' ', text)
    assert not re.search(r'\b(WHILE|SinaSpeed|TON_TIME|REGION|LMQTT)\b|#(?=[A-Za-z_])', code), path
    assert not re.search(r'\b(Control|IO_Cards|IO_VFDs)\.', code), path
print(f'PASS: XML, unique symbols, project references, {len(reference)} source routines, '
      f'{len(review)} non-compiled drafts, {len(active_names)} new compiled-source items.')
print('ST compilation and runtime tests: NOT performed by this validator.')
