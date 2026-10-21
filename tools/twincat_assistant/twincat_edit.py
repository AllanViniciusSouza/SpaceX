#!/usr/bin/env python3
"""twincat_edit.py - minimal-diff helpers for TwinCAT 3 PLC source files.

Part of the twincat-assistant plugin.

Commands
  info     <file>                         BOM, line endings, object kind/name/id, line counts
  show     <file> [--part decl|impl|all]  print the ST text with XAE-style line numbers
  replace  <file> <old1> <new1> [<old2> <new2> ...] [--part decl|impl|any] [--count N] [--dry-run]
                                          anchored replacement; old/new are text FILES (exact text);
                                          all-or-nothing; keeps BOM, line endings and everything else
  contains <file> <snippet>               exit 0 if the snippet text (file) is present, 1 otherwise
  new      <kind> <plcproj> <relpath> --decl <file> [--impl <file>] [--dry-run]
                                          kind = fb | function | program | dut | gvl;
                                          creates the object file and registers it in the .plcproj
  register <plcproj> <relpath> [--dry-run] add a Compile item (and missing Folder items)
  check    <plcproj>                      structural checks of the whole PLC project (read-only)
  dump     <plcproj> <outdir>             write the ST of every Compile item to outdir (read-only on project)

Notes
  * Snippet files are compared after converting CRLF to LF. Tabs and spaces must match exactly.
  * The file is read again at write time: edits are applied to the current content on disk,
    so changes made by someone else in other parts of the file are kept.
  * Nothing here compiles ST. Only a real TwinCAT build proves that a project compiles.
"""
import argparse
import difflib
import os
import re
import sys
import uuid
import xml.etree.ElementTree as ET

VERSION = "0.1.0"

IEC_TYPES = {
    'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'INT', 'UINT', 'DINT', 'UDINT',
    'LINT', 'ULINT', 'REAL', 'LREAL', 'TIME', 'LTIME', 'DATE', 'TOD', 'TIME_OF_DAY', 'DT',
    'DATE_AND_TIME', 'STRING', 'WSTRING', 'BIT', 'ANY', 'ANY_INT', 'ANY_NUM', 'ANY_REAL',
    'POINTER', 'REFERENCE', 'ARRAY', 'OF', 'TO', 'PVOID', 'XINT', 'UXINT', 'XWORD',
    'TON', 'TOF', 'TP', 'R_TRIG', 'F_TRIG', 'CTU', 'CTD', 'CTUD', 'RS', 'SR', 'LTON', 'LTOF', 'LTP',
    'TIMESTRUCT', 'T_MAXSTRING', 'AXIS_REF', 'STRUCT', 'UNION', 'END_STRUCT',
}


# ----------------------------------------------------------------------------- file helpers
class TcFile:
    """Text of a TwinCAT file with its original encoding details."""

    def __init__(self, path):
        self.path = path
        raw = open(path, 'rb').read()
        self.bom = raw.startswith(b'\xef\xbb\xbf')
        body = raw[3:] if self.bom else raw
        text = body.decode('utf-8')
        crlf = text.count('\r\n')
        lf_only = text.count('\n') - crlf
        self.eol = '\r\n' if crlf > 0 and crlf >= lf_only else '\n'
        self.text = text.replace('\r\n', '\n')

    def encode(self, text):
        data = text.replace('\n', '\r\n') if self.eol == '\r\n' else text
        return (b'\xef\xbb\xbf' if self.bom else b'') + data.encode('utf-8')

    def save(self, text):
        # Write in place (no temp file / rename: deleting may be blocked on connected folders).
        with open(self.path, 'wb') as stream:
            stream.write(self.encode(text))


def read_snippet(path):
    return open(path, 'rb').read().decode('utf-8-sig').replace('\r\n', '\n')


def parts_of(text):
    """Return spans (start, end) of CDATA blocks: list of (label, start, end)."""
    spans = []
    for match in re.finditer(r'<Declaration><!\[CDATA\[(.*?)\]\]></Declaration>', text, re.S):
        spans.append(('decl', match.start(1), match.end(1)))
    for match in re.finditer(r'<ST><!\[CDATA\[(.*?)\]\]></ST>', text, re.S):
        spans.append(('impl', match.start(1), match.end(1)))
    return sorted(spans, key=lambda s: s[1])


def object_info(text):
    root = ET.fromstring(text.encode('utf-8'))
    obj = next(iter(root))
    return obj.tag, obj.get('Name'), obj.get('Id'), root


def xml_ok(text):
    try:
        ET.fromstring(text.encode('utf-8'))
        return True, ''
    except ET.ParseError as exc:
        return False, str(exc)


def unified(old, new, name):
    diff = difflib.unified_diff(old.split('\n'), new.split('\n'), name + ' (before)', name + ' (after)',
                                n=2, lineterm='')
    return '\n'.join(diff)


def closest_lines(text, snippet):
    first = next((l for l in snippet.split('\n') if l.strip()), '')
    lines = text.split('\n')
    near = difflib.get_close_matches(first, lines, n=3, cutoff=0.5)
    out = ['  first anchor line: ' + repr(first)]
    for line in near:
        out.append('  similar line in file: ' + repr(line))
    return '\n'.join(out)


# ----------------------------------------------------------------------------- commands
def cmd_info(args):
    tc = TcFile(args.file)
    kind, name, oid, _ = object_info(tc.text)
    print(f'file: {args.file}')
    print(f'object: {kind} {name} {oid}')
    print(f'bom: {tc.bom}  eol: {"CRLF" if tc.eol == chr(13) + chr(10) else "LF"}  '
          f'ends_with_newline: {tc.text.endswith(chr(10))}')
    for label, start, end in parts_of(tc.text):
        print(f'part {label}: {tc.text[start:end].count(chr(10)) + 1} lines')
    print(f'mtime_ns: {os.stat(args.file).st_mtime_ns}')


def cmd_show(args):
    tc = TcFile(args.file)
    kind, name, _, root = object_info(tc.text)
    print(f'==== {kind} {name}')
    obj = next(iter(root))

    def emit(title, body):
        print(f'---- {title}')
        for number, line in enumerate((body or '').split('\n'), 1):
            print(f'{number:4d}  {line}')

    if args.part in ('decl', 'all'):
        emit('Declaration', obj.findtext('Declaration'))
    if args.part in ('impl', 'all'):
        impl = obj.find('Implementation/ST')
        if impl is not None:
            emit('Implementation', impl.text)
    if args.part == 'all':
        for sub in list(obj):
            if sub.tag in ('Method', 'Property', 'Action', 'Transition'):
                emit(f'{sub.tag} {sub.get("Name")} - Declaration', sub.findtext('Declaration'))
                st = sub.find('Implementation/ST')
                if st is not None:
                    emit(f'{sub.tag} {sub.get("Name")} - Implementation', st.text)


def cmd_replace(args):
    pairs = args.pairs
    if len(pairs) % 2:
        sys.exit('replace: give old/new snippet files in pairs')
    tc = TcFile(args.file)
    before = tc.text
    _, name_before, _, _ = object_info(before)
    text = before
    for index in range(0, len(pairs), 2):
        old = read_snippet(pairs[index])
        new = read_snippet(pairs[index + 1])
        if not old:
            sys.exit(f'replace: snippet {pairs[index]} is empty')
        if ']]>' in new:
            sys.exit('replace: new text contains "]]>", which would break the CDATA section')
        if args.part == 'any':
            found = text.count(old)
            if found != args.count:
                print(f'ABORT: anchor {pairs[index]} found {found} time(s), expected {args.count}. File unchanged.')
                print(closest_lines(text, old))
                sys.exit(2)
            text = text.replace(old, new)
        else:
            spans = [s for s in parts_of(text) if s[0] == args.part]
            hits = [(s, e) for _, s, e in spans for _ in range(text[s:e].count(old))]
            if len(hits) != args.count:
                print(f'ABORT: anchor {pairs[index]} found {len(hits)} time(s) in part "{args.part}", '
                      f'expected {args.count}. File unchanged.')
                print(closest_lines(text, old))
                sys.exit(2)
            for _, start, end in reversed(spans):
                segment = text[start:end]
                if old in segment:
                    text = text[:start] + segment.replace(old, new) + text[end:]
    ok, err = xml_ok(text)
    if not ok:
        print(f'ABORT: result is not valid XML ({err}). File unchanged.')
        sys.exit(2)
    _, name_after, _, _ = object_info(text)
    if name_after != name_before:
        print('ABORT: the object name would change. File unchanged.')
        sys.exit(2)
    print(unified(before, text, os.path.basename(args.file)))
    if args.dry_run:
        print('DRY RUN: nothing written.')
        return
    # Re-read right before writing: apply to the latest content on disk.
    latest = TcFile(args.file)
    if latest.text != before:
        print('ABORT: the file changed on disk while preparing the edit (someone saved it). '
              'Read it again and repeat. File unchanged.')
        sys.exit(3)
    tc.save(text)
    print(f'WRITTEN: {args.file}')


def cmd_contains(args):
    tc = TcFile(args.file)
    snippet = read_snippet(args.snippet)
    present = snippet in tc.text
    print('PRESENT' if present else 'MISSING')
    sys.exit(0 if present else 1)


TEMPLATE_POU = '''<?xml version="1.0" encoding="utf-8"?>
<TcPlcObject Version="1.1.0.1">
  <POU Name="{name}" Id="{{{guid}}}" SpecialFunc="None">
    <Declaration><![CDATA[{decl}]]></Declaration>
    <Implementation>
      <ST><![CDATA[{impl}]]></ST>
    </Implementation>
  </POU>
</TcPlcObject>'''

TEMPLATE_DECL_ONLY = '''<?xml version="1.0" encoding="utf-8"?>
<TcPlcObject Version="1.1.0.1">
  <{tag} Name="{name}" Id="{{{guid}}}">
    <Declaration><![CDATA[{decl}]]></Declaration>
  </{tag}>
</TcPlcObject>'''

KIND_EXT = {'fb': '.TcPOU', 'function': '.TcPOU', 'program': '.TcPOU', 'dut': '.TcDUT', 'gvl': '.TcGVL'}
KIND_KEYWORD = {'fb': r'FUNCTION_BLOCK\s+{n}\b', 'function': r'FUNCTION\s+{n}\b', 'program': r'PROGRAM\s+{n}\b',
                'dut': r'TYPE\s+{n}\b', 'gvl': r'VAR_GLOBAL'}


def norm_rel(relpath):
    return relpath.replace('/', '\\').strip('\\')


def rel_stem(relpath):
    """Object name from a .plcproj relative path (backslash separated)."""
    return os.path.splitext(norm_rel(relpath).split('\\')[-1])[0]


def register_text(plcproj_text, relpath):
    """Return (new_text, added_lines) with a Compile item (and Folder items) for relpath."""
    rel = norm_rel(relpath)
    existing = re.findall(r'<(?:Compile|None) Include="([^"]+)"', plcproj_text)
    if rel.lower() in (e.lower() for e in existing):
        return plcproj_text, []
    ext = os.path.splitext(rel)[1].lower()
    items = list(re.finditer(r'(?m)^([ \t]*)<Compile Include="([^"]+)"(?:\s*/>|>.*?</Compile>)[ \t]*\n',
                             plcproj_text, re.S))
    if not items:
        raise SystemExit('register: no Compile item found to copy the format from')
    sample = next((m for m in items if m.group(2).lower().endswith(ext)), items[-1])
    block = sample.group(0).replace(f'Include="{sample.group(2)}"', f'Include="{rel}"', 1)
    insert_at = items[-1].end()
    text = plcproj_text[:insert_at] + block + plcproj_text[insert_at:]
    added = [block.rstrip('\n')]
    # Folder items for every parent folder
    folders = re.findall(r'<Folder Include="([^"]+)"', text)
    parts = rel.split('\\')[:-1]
    for depth in range(1, len(parts) + 1):
        folder = '\\'.join(parts[:depth])
        if folder.lower() in (f.lower() for f in folders):
            continue
        last = list(re.finditer(r'(?m)^([ \t]*)<Folder Include="[^"]+"\s*/>[ \t]*\n', text))
        if not last:
            raise SystemExit('register: no Folder item found to copy the format from')
        line = f'{last[-1].group(1)}<Folder Include="{folder}" />\n'
        text = text[:last[-1].end()] + line + text[last[-1].end():]
        folders.append(folder)
        added.append(line.rstrip('\n'))
    return text, added


def cmd_register(args):
    pj = TcFile(args.plcproj)
    text, added = register_text(pj.text, args.relpath)
    if not added:
        print('already registered')
        return
    print('\n'.join('+ ' + a for a in added))
    if args.dry_run:
        print('DRY RUN: nothing written.')
        return
    pj.save(text)
    print(f'WRITTEN: {args.plcproj}')


def cmd_new(args):
    kind = args.kind
    rel = norm_rel(args.relpath)
    if not rel.endswith(KIND_EXT[kind]):
        sys.exit(f'new: {kind} must use the extension {KIND_EXT[kind]}')
    name = rel_stem(rel)
    decl = read_snippet(args.decl)
    if not decl.endswith('\n'):
        decl += '\n'
    if not re.search(KIND_KEYWORD[kind].format(n=re.escape(name)), decl, re.I):
        sys.exit(f'new: the declaration does not declare {kind} {name}')
    project_dir = os.path.dirname(os.path.abspath(args.plcproj))
    target = os.path.join(project_dir, *rel.split('\\'))
    if os.path.exists(target):
        sys.exit(f'new: {target} already exists')
    guid = str(uuid.uuid4())
    if kind in ('fb', 'function', 'program'):
        impl = read_snippet(args.impl) if args.impl else ''
        if impl and not impl.endswith('\n'):
            impl += '\n'
        if ']]>' in decl + impl:
            sys.exit('new: text contains "]]>"')
        body = TEMPLATE_POU.format(name=name, guid=guid, decl=decl, impl=impl)
    else:
        tag = 'DUT' if kind == 'dut' else 'GVL'
        body = TEMPLATE_DECL_ONLY.format(tag=tag, name=name, guid=guid, decl=decl)
    ok, err = xml_ok(body)
    if not ok:
        sys.exit(f'new: generated XML invalid: {err}')
    pj = TcFile(args.plcproj)
    text, added = register_text(pj.text, rel)
    print(f'new object: {kind} {name} Id={{{guid}}}')
    print(f'file: {target}')
    print('\n'.join('+ ' + a for a in added))
    if args.dry_run:
        print('DRY RUN: nothing written.')
        return
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'wb') as stream:
        stream.write(b'\xef\xbb\xbf' + body.replace('\n', '\r\n').encode('utf-8'))
    pj.save(text)
    print(f'WRITTEN: {target}')
    print(f'WRITTEN: {args.plcproj}')


# ----------------------------------------------------------------------------- check
def strip_code(code):
    code = re.sub(r'\(\*.*?\*\)', lambda m: '\n' * m.group().count('\n'), code, flags=re.S)
    code = re.sub(r'//[^\n]*', '', code)
    code = re.sub(r"'(?:\$.|''|[^'])*'", "''", code)
    code = re.sub(r'"(?:\$.|[^"])*"', '""', code)
    return code


def declared_names(decl):
    names = set()
    for match in re.finditer(r'(?m)^\s*([A-Za-z_]\w*)\s*(?:AT\s+%\S+\s*)?:(?!=)', strip_code(decl)):
        names.add(match.group(1).upper())
    return names


def type_refs(decl):
    refs = []
    clean = strip_code(decl)
    for number, line in enumerate(clean.split('\n'), 1):
        match = re.search(r':\s*(?:ARRAY\s*\[[^\]]*\]\s*OF\s+)?(?:POINTER\s+TO\s+|REFERENCE\s+TO\s+)?'
                          r'([A-Za-z_][\w\.]*)', line)
        if match and ':=' not in line[:match.start() + 1]:
            refs.append((number, match.group(1)))
    return refs


def cmd_check(args):
    pj = TcFile(args.plcproj)
    project_dir = os.path.dirname(os.path.abspath(args.plcproj))
    ok, err = xml_ok(pj.text)
    problems, warnings = [], []
    if not ok:
        problems.append(f'.plcproj is not valid XML: {err}')
    items = re.findall(r'<(Compile|None) Include="([^"]+)"', pj.text)
    objects = {}
    compiled = []
    for kind, rel in items:
        path = os.path.join(project_dir, *rel.split('\\'))
        if not os.path.exists(path):
            (problems if kind == 'Compile' else warnings).append(f'{kind} item missing on disk: {rel}')
            continue
        if kind == 'Compile' and rel.lower().startswith('migrationreview'):
            warnings.append(f'draft registered as Compile: {rel}')
        if not rel.lower().endswith(('.tcpou', '.tcdut', '.tcgvl')):
            continue
        try:
            tc = TcFile(path)
            tag, name, oid, root = object_info(tc.text)
        except Exception as exc:  # noqa: BLE001
            problems.append(f'invalid XML: {rel}: {exc}')
            continue
        if kind != 'Compile':
            continue
        stem = rel_stem(rel)
        if name != stem:
            warnings.append(f'object name {name} differs from file name {stem}')
        if name.upper() in objects:
            problems.append(f'duplicate object name {name}: {rel} and {objects[name.upper()][0]}')
        objects[name.upper()] = (rel, tag, root)
        compiled.append((rel, tag, name, root))
    on_disk = set()
    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = [d for d in dirnames if d not in ('_Libraries', '_CompileInfo', 'MigrationReview')]
        for fn in filenames:
            if fn.lower().endswith(('.tcpou', '.tcdut', '.tcgvl')):
                on_disk.add(os.path.relpath(os.path.join(dirpath, fn), project_dir).replace('/', '\\').lower())
    registered = {rel.lower() for _, rel in items}
    for rel in sorted(on_disk - registered):
        warnings.append(f'file on disk not registered (not compiled): {rel}')
    # qualified_only GVL variables used without the GVL name; members of every GVL
    gvl_vars = {}
    gvl_members = {}
    for rel, tag, name, root in compiled:
        if tag != 'GVL':
            continue
        decl = root[0].findtext('Declaration') or ''
        gvl_members[name.upper()] = declared_names(decl)
        if "attribute 'qualified_only'" in decl:
            for var in declared_names(decl):
                gvl_vars.setdefault(var, name)
    known_types = set(objects) | IEC_TYPES
    for rel, tag, name, root in compiled:
        obj = root[0]
        decl = obj.findtext('Declaration') or ''
        # type references that do not exist in the project (may be library types)
        for line_no, ref in type_refs(decl):
            base = ref.split('.')[-1].upper()
            if base not in known_types and not ref.upper().startswith(('TC2_', 'TC3_', 'VISU')):
                warnings.append(f'{name} decl line {line_no}: type "{ref}" not found in the project '
                                f'(library type or missing DUT/FB)')
        if re.search(r'ARRAY\s*\[\s*[\w\-]+\s*\.\.\s*\]', strip_code(decl)) and tag == 'GVL':
            problems.append(f'{name}: ARRAY[n..] without upper bound is only allowed for VAR_IN_OUT')
        impl_el = obj.find('Implementation/ST')
        if impl_el is None or not impl_el.text:
            continue
        local = declared_names(decl)
        for line_no, line in enumerate(strip_code(impl_el.text).split('\n'), 1):
            for match in re.finditer(r'(?<![\.\w])([A-Za-z_]\w*)\b', line):
                token = match.group(1).upper()
                if token in gvl_vars and token not in local and token not in objects:
                    after = line[match.end():match.end() + 1]
                    if after != '(':
                        warnings.append(f'{name} impl line {line_no}: "{match.group(1)}" looks like a variable of '
                                        f'qualified_only GVL {gvl_vars[token]} used without "{gvl_vars[token]}."')
            for match in re.finditer(r'(?<![\.\w])([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)', line):
                gvl, member = match.group(1).upper(), match.group(2).upper()
                if gvl in gvl_members and gvl not in local and member not in gvl_members[gvl]:
                    problems.append(f'{name} impl line {line_no}: "{match.group(1)}.{match.group(2)}" - '
                                    f'{match.group(2)} is not declared in GVL {match.group(1)}')
            if re.search(r'%X\d|"[A-Za-z_]', line):
                warnings.append(f'{name} impl line {line_no}: Siemens-style syntax (%X bit or quoted name)')
            if re.search(r'\{\s*(REGION|END_REGION)\b', line):
                warnings.append(f'{name} impl line {line_no}: Siemens {{REGION}} pragma; use {{region "..."}}')
    def grouped(entries):
        # Merge identical findings of one object that differ only in the line number.
        order, lines = [], {}
        for entry in entries:
            match = re.match(r'^(\S+) (impl|decl) line (\d+): (.*)$', entry)
            key = (match.group(1), match.group(2), match.group(4)) if match else (entry, '', '')
            if key not in lines:
                order.append(key)
                lines[key] = []
            if match:
                lines[key].append(match.group(3))
        out = []
        for key in order:
            if key[1]:
                nums = sorted(set(lines[key]), key=int)
                out.append(f'{key[0]} {key[1]} line(s) {", ".join(nums)}: {key[2]}')
            else:
                out.append(key[0])
        return out

    for line in grouped(problems):
        print('PROBLEM: ' + line)
    for line in grouped(warnings):
        print('WARN:    ' + line)
    print(f'checked {len(compiled)} compiled objects: {len(problems)} problem(s), {len(warnings)} warning(s)')
    print('Structural check only. It does not compile ST; only a TwinCAT build proves the project compiles.')
    sys.exit(1 if problems else 0)


def cmd_dump(args):
    pj = TcFile(args.plcproj)
    project_dir = os.path.dirname(os.path.abspath(args.plcproj))
    os.makedirs(args.outdir, exist_ok=True)
    count = 0
    for rel in re.findall(r'<Compile Include="([^"]+\.(?:TcPOU|TcDUT|TcGVL))"', pj.text, re.I):
        path = os.path.join(project_dir, *rel.split('\\'))
        if not os.path.exists(path):
            continue
        tc = TcFile(path)
        try:
            tag, name, _, root = object_info(tc.text)
        except Exception:  # noqa: BLE001
            continue
        obj = root[0]
        out = [f'(* ==== {tag} {name} | {rel} ==== *)', '(* ---- Declaration ---- *)',
               obj.findtext('Declaration') or '']
        st = obj.find('Implementation/ST')
        if st is not None:
            out += ['(* ---- Implementation ---- *)', st.text or '']
        for sub in list(obj):
            if sub.tag in ('Method', 'Property', 'Action'):
                out += [f'(* ---- {sub.tag} {sub.get("Name")} ---- *)', sub.findtext('Declaration') or '']
                sst = sub.find('Implementation/ST')
                if sst is not None:
                    out.append(sst.text or '')
        fn = rel.replace('\\', '__') + '.st'
        open(os.path.join(args.outdir, fn), 'w', encoding='utf-8').write('\n'.join(out))
        count += 1
    print(f'dumped {count} objects to {args.outdir}')


def main():
    parser = argparse.ArgumentParser(description='TwinCAT 3 minimal-diff helpers (twincat-assistant %s)' % VERSION)
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('info'); p.add_argument('file'); p.set_defaults(fn=cmd_info)
    p = sub.add_parser('show'); p.add_argument('file'); p.add_argument('--part', default='all',
                                                                       choices=['decl', 'impl', 'all'])
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser('replace'); p.add_argument('file'); p.add_argument('pairs', nargs='+')
    p.add_argument('--part', default='any', choices=['decl', 'impl', 'any'])
    p.add_argument('--count', type=int, default=1); p.add_argument('--dry-run', action='store_true')
    p.set_defaults(fn=cmd_replace)
    p = sub.add_parser('contains'); p.add_argument('file'); p.add_argument('snippet'); p.set_defaults(fn=cmd_contains)
    p = sub.add_parser('new'); p.add_argument('kind', choices=sorted(KIND_EXT)); p.add_argument('plcproj')
    p.add_argument('relpath'); p.add_argument('--decl', required=True); p.add_argument('--impl')
    p.add_argument('--dry-run', action='store_true'); p.set_defaults(fn=cmd_new)
    p = sub.add_parser('register'); p.add_argument('plcproj'); p.add_argument('relpath')
    p.add_argument('--dry-run', action='store_true'); p.set_defaults(fn=cmd_register)
    p = sub.add_parser('check'); p.add_argument('plcproj'); p.set_defaults(fn=cmd_check)
    p = sub.add_parser('dump'); p.add_argument('plcproj'); p.add_argument('outdir'); p.set_defaults(fn=cmd_dump)
    args = parser.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
