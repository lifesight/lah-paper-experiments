"""Offline current-release identity and navigation checks; Python standard library."""
from pathlib import Path
import hashlib,json,zipfile,re
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'archive/ARCHIVE_MANIFEST.json').read_text())
for f in a['files']:
 assert hashlib.sha256((r/f['archive_path']).read_bytes()).hexdigest()==f['sha256'],f['archive_path']
z=r/'reproduction/lah-reproduction-candidate-v2.zip'
assert hashlib.sha256(z.read_bytes()).hexdigest()=='04630a37ffe19b8c5c20bc48df93c63c299cc59f7b2d8d8b4eb44c60dcc5170f'
with zipfile.ZipFile(z) as a:
 for p in (r/'results').glob('*.json'):
  member='aggregate/table4_counts.json' if p.name=='table4_counts.json' else 'original/main001_analysis/'+p.name
  assert p.read_bytes()==a.read('lah-reproduction-candidate/'+member),p.name
for p in [r/'README.md',r/'paper/README.md',r/'paper/manuscript.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()) + re.findall(r'src="([^"]+)"',p.read_text()):
  if '://' not in link and not link.startswith('#'):
   assert (p.parent/link.split('#')[0]).exists(),(p.name,link)
print('PASS: historical hashes, exact archive, six result mirrors and local paper/README links')

m=json.loads((r/'source/SOURCE_MANIFEST.json').read_text())
with zipfile.ZipFile(z) as a:
 for item in m['files']:
  data=(r/'source'/item['path']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==item['sha256']
  assert data==a.read(item['archive_member'])
assert len(m['files'])==4
assert 'https://github.com/lifesight/lah-paper-experiments' in (r/'CITATION.cff').read_text()
print('PASS: four exact browsable source mirrors and canonical repository URL')
