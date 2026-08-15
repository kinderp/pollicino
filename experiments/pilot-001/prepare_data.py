from __future__ import annotations

import hashlib
import json
from pathlib import Path

ALLOWED_SUFFIXES = {'.py', '.md', '.json', '.toml', '.yaml', '.yml'}
INCLUDE_PREFIXES = (
    'course/pollicino-quarto-2026/activities/uda-05/',
    'course/pollicino-quarto-2026/activities/uda-06/',
    'src/pollicino/',
    'docs/research/',
)
INCLUDE_EXACT = {
    'course/README.md',
    'course/pollicino-quarto-2026/bundle.json',
    'pyproject.toml',
}
BOUNDARY_PREFIX = b'\n\n===POLLICINO_FILE:'
BOUNDARY_SUFFIX = b'===\n\n'


def include(relative: str) -> bool:
    if relative in INCLUDE_EXACT:
        return True
    return any(relative.startswith(prefix) for prefix in INCLUDE_PREFIXES)


def split_name(relative_path: str) -> str:
    bucket = int.from_bytes(hashlib.sha256(relative_path.encode()).digest()[:4], 'big') % 100
    return 'train' if bucket < 80 else 'validation' if bucket < 90 else 'test'


def collect(repo_root: Path) -> list[tuple[str, bytes]]:
    items=[]
    for path in repo_root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        relative=path.relative_to(repo_root).as_posix()
        if '__pycache__' in relative or '.pytest_cache' in relative or not include(relative):
            continue
        items.append((relative,path.read_bytes()))
    return sorted(items)


def assemble(entries: list[tuple[str, bytes]]) -> bytes:
    out=bytearray()
    for relative,data in entries:
        out.extend(BOUNDARY_PREFIX); out.extend(relative.encode()); out.extend(BOUNDARY_SUFFIX); out.extend(data)
    return bytes(out)


def write_dataset(repo_root: Path, output_dir: Path) -> dict:
    entries=collect(repo_root)
    splits={'train':[],'validation':[],'test':[]}
    files=[]
    for relative,data in entries:
        split=split_name(relative); splits[split].append((relative,data))
        files.append({'path':relative,'split':split,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    output_dir.mkdir(parents=True,exist_ok=True)
    split_meta={}
    for split,items in splits.items():
        blob=assemble(items); (output_dir/f'{split}.bin').write_bytes(blob)
        split_meta[split]={'files':len(items),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
    return {'dataset_id':'pollicino-self-v1','source_parent_commit':'6a65aa6ee30d9d2fd8f39283ad0bac22bba03bd6','selection':{'prefixes':list(INCLUDE_PREFIXES),'exact':sorted(INCLUDE_EXACT),'split':'sha256(path) mod 100: 0-79 train, 80-89 validation, 90-99 test'},'splits':split_meta,'files':files}


def main():
    here=Path(__file__).resolve().parent
    repo_root=Path(__file__).resolve().parents[2]
    manifest=write_dataset(repo_root,here/'data')
    (here/'dataset-manifest.json').write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest['splits'],indent=2))

if __name__=='__main__': main()
