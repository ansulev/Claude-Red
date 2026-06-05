#!/usr/bin/env python3
"""
Claude Skills Converter v4
Markdown parser for ## headers and - **Field**: value format.
name = folder value (not skill_name field)
"""
import re
import zipfile
from pathlib import Path

INPUT_DIR = Path("Skills")
OUTPUT_DIR = Path("skills-converted")
ZIP_DIR = Path("skills-zip")

def parse_skill(content: str, file_path: Path) -> dict:
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')

    meta = {
        'name': None,  # equals folder value
        'folder': None,
        'source': None,
        'description': [],
        'triggers': [],
        'body': []
    }

    state = 'INIT'

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if state in ('DESCRIPTION', 'BODY'):
                if state == 'DESCRIPTION' and meta['description']:
                    meta['description'].append('')
                elif state == 'BODY':
                    meta['body'].append('')
            continue

        header_match = re.match(r'^##\s+(.+)', stripped, re.I)
        if header_match:
            section = header_match.group(1).strip().lower()
            if section == 'metadata':
                state = 'METADATA'
            elif section == 'description':
                state = 'DESCRIPTION'
            elif section == 'trigger phrases':
                state = 'TRIGGER'
            elif section == 'instructions for claude':
                state = 'BODY'
                meta['body'].append('# Instructions for Claude')
            elif section == 'full methodology':
                state = 'BODY'
                meta['body'].append('## Full Methodology')
            continue

        if state == 'METADATA' and stripped.startswith('- **'):
            match = re.match(r'-\s*\*\*([^*]+)\*\*\s*:\s*(.+)', stripped)
            if match:
                key = match.group(1).strip().lower().replace(' ', '_')
                val = match.group(2).strip()
                if key == 'skill_name':
                    pass  # skill_name field is ignored; name derives from folder
                elif key == 'folder':
                    meta['folder'] = val
                    meta['name'] = re.sub(r'[^a-z0-9]+', '-', val.lower()).strip('-')
                elif key == 'source':
                    meta['source'] = val

        elif state == 'DESCRIPTION':
            if not stripped.startswith('##') and not stripped.startswith('- **'):
                meta['description'].append(stripped)

        elif state == 'TRIGGER':
            match = re.search(r'`([^`]+)`', stripped)
            if match:
                raw = match.group(1)
                meta['triggers'] = [t.strip() for t in raw.split(',') if t.strip()]

        elif state == 'BODY':
            if not stripped.startswith('##') or stripped.startswith('###'):
                meta['body'].append(line.rstrip())

    meta['description'] = ' '.join(d for d in meta['description'] if d.strip())
    if not meta['description']:
        meta['description'] = 'No description available.'

    meta['body'] = '\n'.join(meta['body']) if meta['body'] else '# Instructions for Claude\n[No content parsed]'

    if not meta['name']:
        parent = file_path.parent.name
        meta['name'] = re.sub(r'[^a-z0-9]+', '-', parent.lower()).strip('-') if parent != 'Skills' else file_path.stem

    return meta

def build_yaml(meta: dict) -> str:
    lines = ['---', f'name: {meta["name"]}', 'description: >']
    words = meta['description'].split()
    line = '  '
    for w in words:
        if len(line) + len(w) + 1 > 80:
            lines.append(line)
            line = '  ' + w
        else:
            line += (' ' if len(line) > 2 else '') + w
    if line.strip():
        lines.append(line)

    lines.append('trigger_phrases:')
    for t in meta['triggers']:
        lines.append(f'  - "{t}"')
    if meta.get('folder'):
        lines.append(f'folder: {meta["folder"]}')
    if meta.get('source'):
        lines.append(f'source: {meta["source"]}')
    lines.append('---')
    return '\n'.join(lines)

def process_file(in_path: Path, out_dir: Path, debug: bool = False) -> bool:
    try:
        for enc in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                text = in_path.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return False

        meta = parse_skill(text, in_path)

        if debug:
            print(f"\n🔍 DEBUG {in_path.name}")
            print(f"   Name: {meta['name']}")
            print(f"   Folder: {meta['folder']}")
            print(f"   Desc: {meta['description'][:120]}...")
            print(f"   Triggers: {meta['triggers'][:3]}... ({len(meta['triggers'])} total)")
            print(f"   Source: {meta['source']}")
            print(f"   Body preview: {meta['body'][:100]}...")
            return True

        yaml_block = build_yaml(meta)
        final = f"{yaml_block}\n\n{meta['body']}\n"

        out = out_dir / meta['name']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'SKILL.md').write_text(final, encoding='utf-8', newline='\n')
        print(f"✅ {in_path.parent.name:35} → {meta['name']}/SKILL.md (Triggers: {len(meta['triggers'])})")
        return True
    except Exception as e:
        print(f"❌ {in_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_zips(conv_dir: Path, zip_dir: Path) -> None:
    zip_dir.mkdir(parents=True, exist_ok=True)
    for d in sorted(conv_dir.iterdir()):
        if d.is_dir():
            zp = zip_dir / f"{d.name}.zip"
            with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in d.rglob('*'):
                    if f.is_file():
                        zf.write(f, f.relative_to(d.parent))
            print(f"📦 {zp.name}")

def main() -> None:
    print("🚀 Claude Skills Converter v4\n")

    in_dir, out_dir, zip_dir = INPUT_DIR, OUTPUT_DIR, ZIP_DIR
    if not in_dir.exists():
        print(f"❌ Directory not found: {in_dir.resolve()}")
        return

    files = set(list(in_dir.rglob('SKILL.md')) + list(in_dir.rglob('skill.md')))
    if not files:
        print("⚠️  No SKILL.md files found")
        return

    print(f"🔍 Found {len(files)} files\n")

    import sys
    if '--debug' in sys.argv:
        process_file(sorted(files)[0], out_dir, debug=True)
        return

    ok = sum(1 for f in sorted(files) if process_file(f, out_dir))

    if ok:
        print(f"\n📦 Generating {ok} ZIP(s)...")
        create_zips(out_dir, zip_dir)
        print(f"\n✨ {ok}/{len(files)} skills converted successfully.")
        print(f"📁 Skills: {out_dir.resolve()}")
        print(f"🗜️  ZIPs:   {zip_dir.resolve()}")
        print("\n📋 Upload to Claude Console:")
        print("   • Each ZIP contains: [folder-name]/SKILL.md")
        print("   • The 'name' in YAML = folder name inside the ZIP")
    else:
        print("\n❌ No skills converted. Run with --debug to diagnose.")

if __name__ == '__main__':
    if not __import__('importlib').util.find_spec('yaml'):
        print("⚠️  Installing PyYAML dependency...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pyyaml'])

    main()
