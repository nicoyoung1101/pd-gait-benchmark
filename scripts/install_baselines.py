"""Clone pinned baseline code and apply recorded CARE-PD patches; excludes assets."""
from pathlib import Path
import argparse
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--models',nargs='+',choices=['PIP','PNP','DynaIP','TIP'],default=['PIP','PNP','DynaIP','TIP'])
args=parser.parse_args()
sources=json.loads((ROOT/'scripts/baselines.json').read_text())
for name in args.models:
    destination=ROOT/name
    if destination.exists():
        raise SystemExit(f'{name} already exists; preserve or move it before creating a pinned checkout.')
    source=sources[name]
    subprocess.run(['git','clone','--filter=blob:none',source['url'],str(destination)],check=True)
    subprocess.run(['git','-C',str(destination),'checkout',source['revision']],check=True)
    patch=ROOT/'patches'/f'{name}.patch'
    if patch.exists():
        subprocess.run(['git','-C',str(destination),'apply','--check',str(patch)],check=True)
        subprocess.run(['git','-C',str(destination),'apply',str(patch)],check=True)
    print(f'Prepared {name} at {source["revision"]}; follow its upstream asset instructions.')
