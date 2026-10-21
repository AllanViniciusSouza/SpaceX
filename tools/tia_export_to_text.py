"""Batch-convert TIA SimaticML block exports to readable reference files.
usage: python3 -I dallas_export.py <dir with xml/> 
writes scl/, db/, lad/, udts/PLC_data_types.scl, INDEX.md (blocks part)"""
import os, re, sys, glob, json
import xml.etree.ElementTree as ET

def local(t): return t.split('}', 1)[-1]

def comment_of(m):
    for c in m:
        if local(c.tag) == 'Comment':
            for t in c.iter():
                if local(t.tag) == 'MultiLanguageText' and (t.text or '').strip():
                    return t.text.strip().replace('\n', ' ')
    return ''

def start_of(m):
    for c in m:
        if local(c.tag) == 'StartValue':
            return (c.text or '').strip()
    return ''

def subels(m):
    return [(c.get('Path'), start_of(c)) for c in m if local(c.tag) == 'Subelement']

def attrs_of(m):
    out = []
    for c in m:
        if local(c.tag) == 'AttributeList':
            for a in c:
                n = a.get('Name')
                if n in ('ExternalAccessible', 'ExternalVisible', 'ExternalWritable', 'S7_SetPoint') and a.get('SystemDefined') != 'true':
                    out.append(f"{n} := '{a.text}'")
    return out

def sub_members(m):
    res = []
    for c in m:
        if local(c.tag) == 'Sections':
            for s in c:
                if s.get('Name') != 'None':
                    continue
                res += [mm for mm in s if local(mm.tag) == 'Member']
        elif local(c.tag) == 'Member':
            res.append(c)
    return res

UDTS = {}
def member_struct(m):
    return {'name': m.get('Name'), 'type': m.get('Datatype'), 'comment': comment_of(m),
            'members': [member_struct(x) for x in sub_members(m)]}

def note_udt(m):
    dt = m.get('Datatype') or ''
    mm = re.search(r'"([^"]+)"', dt)
    subs = sub_members(m)
    if mm and subs and mm.group(1) not in UDTS:
        UDTS[mm.group(1)] = [member_struct(x) for x in subs]
    for s in subs:
        note_udt(s)

def decl(m, ind):
    name, dt = m.get('Name'), m.get('Datatype') or ''
    attrs = attrs_of(m); a = (' { ' + '; '.join(attrs) + '}') if attrs else ''
    sv, cm = start_of(m), comment_of(m)
    note_udt(m)
    if dt == 'Struct':
        lines = [f"{ind}{name}{a} : Struct" + (f"   // {cm}" if cm else '')]
        for s in sub_members(m):
            lines += decl(s, ind + '   ')
        return lines + [f"{ind}END_STRUCT;"]
    return [f"{ind}{name}{a} : {dt}" + (f" := {sv}" if sv else '') + ';' + (f"   // {cm}" if cm else '')]

SECT = {'Input': 'VAR_INPUT', 'Output': 'VAR_OUTPUT', 'InOut': 'VAR_IN_OUT', 'Static': 'VAR',
        'Temp': 'VAR_TEMP', 'Constant': 'VAR CONSTANT'}

def interface(iface):
    out = []
    top = next((c for c in iface if local(c.tag) == 'Sections'), None)
    if top is None:
        return out
    for sec in top:
        mem = [m for m in sec if local(m.tag) == 'Member']
        n = sec.get('Name')
        if n == 'Return':
            if mem: out.append(f"   // RETURN : {mem[0].get('Datatype')}")
            continue
        if not mem or n not in SECT:
            continue
        out.append(SECT[n])
        for m in mem:
            out += decl(m, '   ')
        out += ['END_VAR', '']
    return out

def flat_values(m, parts, out):
    name, dt = m.get('Name'), m.get('Datatype') or ''
    seg = name if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) else f'"{name}"'
    if dt.startswith('Array'):
        seg += '[]'
    p = parts + [seg]
    subs = sub_members(m)
    if subs and not dt.startswith('Array') or (subs and '"' in dt) or (subs and 'Struct' in dt):
        for s in subs:
            flat_values(s, p, out)
        return
    sv = start_of(m)
    path = '.'.join(p)
    if sv:
        out.append(f"{path.replace('[]', '')} : {dt} := {sv}")
    for sp, val in subels(m):
        idx = sp.split(',')
        q = path
        for i in idx:
            q = q.replace('[]', f'[{i}]', 1)
        out.append(f"{q} : {dt} := {val}")

def render(el):
    t = local(el.tag)
    if t == 'Token': return el.get('Text')
    if t == 'Blank': return ' ' * int(el.get('Num', '1'))
    if t == 'NewLine': return '\n' * int(el.get('Num', '1'))
    if t in ('LineComment', 'Comment'):
        txt = ''.join((x.text or '') for x in el if local(x.tag) == 'Text')
        return ('(*' + txt + '*)') if (t == 'Comment' or el.get('Inserted') == 'true') else ('//' + txt)
    if t == 'Text': return el.text or ''
    if t in ('BooleanAttribute', 'IntegerAttribute', 'StringAttribute', 'DateAttribute', 'ConstantType'): return ''
    if t == 'Access':
        sc = el.get('Scope'); body = ''.join(render(c) for c in el)
        if sc in ('LocalVariable', 'LocalConstant'): return '#' + body
        if sc == 'GlobalConstant' and not body.startswith('"'): return '"' + body + '"'
        if sc == 'GlobalVariable' and not body.startswith('"'):
            ps = body.split('.', 1); return '"' + ps[0] + '"' + ('.' + ps[1] if len(ps) > 1 else '')
        return body
    if t == 'Symbol': return ''.join(render(c) for c in el)
    if t == 'Component':
        q = any(local(c.tag) == 'BooleanAttribute' and c.get('Name') == 'HasQuotes' and c.text == 'true' for c in el)
        n = el.get('Name'); n = f'"{n}"' if (q or re.search(r'[^A-Za-z0-9_]', n)) else n
        return n + ''.join(render(c) for c in el)
    if t == 'ConstantValue': return el.text or ''
    if t == 'Constant' and el.get('Name'): return el.get('Name')
    if t == 'Instruction': return (el.get('Name') or '') + ''.join(render(c) for c in el)
    if t == 'CallInfo':
        inst, rest = '', []
        for c in el:
            if local(c.tag) == 'Instance': inst = render(c)
            else: rest.append(render(c))
        return (inst if inst else f'"{el.get("Name")}"') + ''.join(rest)
    if t == 'Instance':
        body = ''.join(render(c) for c in el)
        return ('#' + body) if el.get('Scope') == 'LocalVariable' else body
    if t == 'Parameter': return el.get('Name') + ''.join(render(c) for c in el)
    return ''.join(render(c) for c in el)

def unit_title(cu):
    for mt in cu.iter():
        if local(mt.tag) == 'MultilingualText' and mt.get('CompositionName') in ('Title', 'Comment'):
            for t in mt.iter():
                if local(t.tag) == 'Text' and (t.text or '').strip():
                    return mt.get('CompositionName'), t.text.strip()
    return None, ''

def lad_summary(blk):
    out = []
    n = 0
    for cu in blk.iter():
        if local(cu.tag) != 'SW.Blocks.CompileUnit':
            continue
        n += 1
        titles = []
        for mt in cu.iter():
            if local(mt.tag) == 'MultilingualText' and mt.get('CompositionName') in ('Title', 'Comment'):
                txt = ' '.join((t.text or '').strip() for t in mt.iter() if local(t.tag) == 'Text' and (t.text or '').strip())
                if txt: titles.append(f"{mt.get('CompositionName')}: {txt}")
        out.append(f"--- Network {n}  " + ' | '.join(titles))
        calls, syms, parts = [], [], []
        for e in cu.iter():
            k = local(e.tag)
            if k == 'CallInfo':
                inst = ''
                for c in e:
                    if local(c.tag) == 'Instance':
                        inst = '.'.join(x.get('Name') for x in c.iter() if local(x.tag) == 'Component')
                calls.append(f"CALL {e.get('BlockType')} \"{e.get('Name')}\"" + (f"  instance \"{inst}\"" if inst else ''))
            elif k == 'Access' and e.get('Scope') in ('GlobalVariable', 'LocalVariable'):
                s = '.'.join(x.get('Name') for x in e.iter() if local(x.tag) == 'Component')
                syms.append(('#' if e.get('Scope') == 'LocalVariable' else '') + s)
            elif k == 'Part':
                parts.append(e.get('Name'))
            elif k == 'StructuredText':
                out.append(render(e))
        for c in calls: out.append('   ' + c)
        if parts: out.append('   parts: ' + ', '.join(sorted(set(parts))))
        if syms: out.append('   operands: ' + ', '.join(dict.fromkeys(syms)))
    return out

def main(base):
    for d in ('scl', 'db', 'lad', 'udts'):
        os.makedirs(os.path.join(base, d), exist_ok=True)
    index = []
    for f in sorted(glob.glob(os.path.join(base, 'xml', '*.xml'))):
        try:
            root = ET.parse(f).getroot()
            blk = next(e for e in root.iter() if local(e.tag).startswith('SW.Blocks.') and local(e.tag) != 'SW.Blocks.CompileUnit')
            kind = local(blk.tag).split('.')[-1]
            al = next(c for c in blk if local(c.tag) == 'AttributeList')
            def A(k):
                e = next((c for c in al if local(c.tag) == k), None)
                return (e.text or '').strip() if e is not None and e.text else ''
            name, num, lang, author = A('Name'), A('Number'), A('ProgrammingLanguage'), A('HeaderAuthor')
            ka = next((c for c in al if local(c.tag) == 'IsKnowHowProtected'), None)
            iface = next((e for e in blk.iter() if local(e.tag) == 'Interface'), None)
            safe = re.sub(r'[\\/:*?"<>|]', '_', name)
            if kind in ('GlobalDB', 'InstanceDB'):
                inst = A('InstanceOfName')
                out = [f'DATA_BLOCK "{name}"   // {kind} {num}' + (f'  instance of "{inst}"' if inst else ''), '']
                vals = []
                if iface is not None:
                    out += interface(iface)
                    top = next((c for c in iface if local(c.tag) == 'Sections'), None)
                    for sec in (top if top is not None else []):
                        for m in sec:
                            if local(m.tag) == 'Member':
                                flat_values(m, [], vals)
                out += ['', '// ---- start values (path : type := value)'] + vals
                dst, folder = os.path.join(base, 'db', safe + '.txt'), 'db'
            elif lang == 'SCL':
                kw = {'FB': 'FUNCTION_BLOCK', 'FC': 'FUNCTION', 'OB': 'ORGANIZATION_BLOCK'}.get(kind, kind)
                out = [f'{kw} "{name}"   // {kind} {num}, author {author}', '']
                if iface is not None: out += interface(iface)
                out.append('BEGIN')
                for st in blk.iter():
                    if local(st.tag) == 'StructuredText': out.append(render(st))
                out.append(f'END_{kw}')
                dst, folder = os.path.join(base, 'scl', safe + '.scl'), 'scl'
            else:
                out = [f'// {kind} "{name}" {num}  language {lang or "?"}  author {author}',
                       '// Graphic/other language: interface + per-network calls and operands. Full logic in xml/.', '']
                if iface is not None: out += interface(iface)
                out += lad_summary(blk)
                dst, folder = os.path.join(base, 'lad', safe + '.txt'), 'lad'
            open(dst, 'w', encoding='utf-8').write('\n'.join(out))
            index.append((name, kind, num, lang, author, folder + '/' + os.path.basename(dst)))
        except Exception as ex:
            index.append((os.path.basename(f), 'ERROR', '', '', '', str(ex)[:80]))
    lines = ['TYPE / PLC data types (layout from block interfaces; member comments are not exported there)', '']
    for k in sorted(UDTS):
        lines.append(f'TYPE "{k}"'); lines.append('   STRUCT')
        def emit(ms, ind):
            for m in ms:
                n = m['name']; n = n if re.match(r'^[A-Za-z_]\w*$', n) else f'"{n}"'
                if m['type'] == 'Struct':
                    lines.append(f"{ind}{n} : Struct")
                    emit(m['members'], ind + '   '); lines.append(f"{ind}END_STRUCT;")
                else:
                    lines.append(f"{ind}{n} : {m['type']};" + (f"   // {m['comment']}" if m['comment'] else ''))
        emit(UDTS[k], '      ')
        lines += ['   END_STRUCT;', 'END_TYPE', '']
    open(os.path.join(base, 'udts', 'PLC_data_types.scl'), 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump(index, open(os.path.join(base, 'udts', '_index.json'), 'w'))
    print(len(index), 'blocks;', len(UDTS), 'UDTs;', sum(1 for i in index if i[1] == 'ERROR'), 'errors')
    for i in index:
        if i[1] == 'ERROR': print('ERR', i)

main(sys.argv[1])
