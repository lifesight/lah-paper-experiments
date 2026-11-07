#!/usr/bin/env python3
"""Restyle four frozen LAH figures. No experiments, network or new inference.
Run: python3 render_figures.py
Requires matplotlib>=3.9 and numpy>=2.0; paths resolve relative to this file.
Frozen data retain original source hashes. PDF/SVG stay vector; PNG is 300 dpi.
"""
from pathlib import Path
import hashlib
import json
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'lah-figure-restyle-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.text import Text
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE/'data.json').read_text())
ARCH = json.loads((HERE/'architecture_layout.json').read_text())
FAMILIES = ('direct_exact','direct_compact','sum','difference','ratio_named','percent',
            'random_value','near_value','wrong_entity','wrong_date','wrong_currency','wrong_sign')
LABELS = ('Exact value','Compact value','Sum','Signed difference','Named ratio','Percentage',
          'Random value','Nearby value','Wrong entity','Wrong date','Wrong currency','Wrong sign')
SOURCES = (8,80,800)
BLUE = '#0077BB'
INK = '#25313B'
GRAY = '#D9E1E5'
plt.rcParams.update({
    'font.family':'DejaVu Sans','font.size':8.5,'axes.titlesize':9.5,
    'axes.labelsize':8.5,'xtick.labelsize':8,'ytick.labelsize':8,
    'legend.fontsize':8,'figure.dpi':160,'savefig.dpi':300,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.65,'axes.edgecolor':'#74818C',
    'text.color':INK,'axes.labelcolor':INK,
    'xtick.color':INK,'ytick.color':INK,
})
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
OUTPUTS=[]
TEXTS={}
GEOMETRY=[]

def save(fig,name):
    """Fixed 6.5in page width: preserve label point sizes in manuscript."""
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    all_text=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text()]
    assert all(t.get_fontsize()>=8 for t in all_text), name
    # Visible text must stay within the figure page; axis bboxes are not clipping checks.
    outside=[]
    w,h=fig.canvas.get_width_height()
    for t in all_text:
        bb=t.get_window_extent(renderer)
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1>w+1 or bb.y1>h+1:
            outside.append(t.get_text())
    assert not outside,(name,outside)
    TEXTS[name]=[t.get_text() for t in all_text]
    GEOMETRY.append({'figure':name,'width_inches':fig.get_figwidth(),
                     'height_inches':fig.get_figheight(),'minimum_visible_font_pt':min(t.get_fontsize() for t in all_text),
                     'all_text_within_page':True})
    for ext in ('pdf','svg','png'):
        p=HERE/f'{name}.{ext}'
        kwargs={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}
        fig.savefig(p,dpi=300,facecolor='white',**kwargs)
        OUTPUTS.append({'file':p.name,'sha256':SHA(p),'bytes':p.stat().st_size})
    plt.close(fig)

# Architecture uses the current source renderer; numeric figures remain unchanged.
import subprocess, sys
subprocess.run([sys.executable, str(HERE/'render_architecture.py')], check=True, stdout=subprocess.DEVNULL)
architecture_check=json.loads((HERE/'ARCHITECTURE_FIGURE_VALIDATION.json').read_text())
TEXTS['figure_00_architecture']=architecture_check['rendered_labels']
GEOMETRY.append({'figure':'figure_00_architecture','width_inches':architecture_check['width_inches'],
                 'height_inches':architecture_check['height_inches'],'minimum_visible_font_pt':8,'all_text_within_page':True})
for file, info in architecture_check['artifacts'].items():
    OUTPUTS.append({'file':file,'sha256':info['sha256'],'bytes':info['bytes']})

# All 36 cells: same 0..100% neutral sequential mapping in both panels.
# High acceptance is not coded as "good": the right panel contains incorrect claims.
counts=DATA['counts']
assert tuple(r['family'] for r in counts)==FAMILIES
cmap=LinearSegmentedColormap.from_list('neutral_blue',['#F1F5F9','#B8D0E4','#6A9FC4','#155486'])
fig,axes=plt.subplots(1,2,figsize=(6.5,3.5))
fig.subplots_adjust(left=.18,right=.985,bottom=.31,top=.87,wspace=.79)
for panel,ax in enumerate(axes):
    entries=counts[panel*6:(panel+1)*6]
    values=np.array([[c['accepted']/c['attempted'] for c in r['conditions']] for r in entries])
    im=ax.pcolormesh(np.arange(4)-.5,np.arange(7)-.5,values,cmap=cmap,vmin=0,vmax=1,shading='flat',rasterized=False)
    ax.set_xlim(-.5,2.5);ax.set_ylim(5.5,-.5)
    ax.set_xticks(range(3),[str(s) for s in SOURCES])
    ax.set_yticks(range(6),LABELS[panel*6:(panel+1)*6])
    ax.tick_params(length=0,pad=5)
    ax.set_title(('(a) Full-fact correct','(b) Full-fact incorrect')[panel],loc='left',pad=9,fontweight='bold',fontsize=9)
    for i,row in enumerate(entries):
        for j,c in enumerate(row['conditions']):
            label=f"{c['accepted']:,}"+('†' if c['exempt_tokens'] else '')
            ax.text(j,i,label,ha='center',va='center',fontsize=8,
                    color='white' if values[i,j]>=.65 else INK)
    ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,6,1),minor=True)
    ax.grid(which='minor',color='white',lw=.7);ax.tick_params(which='minor',length=0)
    for sp in ax.spines.values():sp.set_visible(False)
fig.text(.575,.225,'Source condition (categorical; 8 facts per source)',ha='center',fontsize=8.5)
cax=fig.add_axes([.31,.14,.45,.035])
cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.25,.5,.75,1])
cb.solids.set_rasterized(False)
cb.ax.set_xticklabels(['0%','25%','50%','75%','100%']);cb.ax.tick_params(length=2,pad=2,labelsize=8)
fig.text(.15,.145,'Acceptance (%)',fontsize=8)
fig.text(.015,.065,'Cells: accepted / 1,000 attempted. † Includes one exempt difference target.',fontsize=8)
fig.text(.015,.02,'Numeric acceptance does not establish semantic truth.',fontsize=8)
save(fig,'figure_01_family_acceptance')

# Six panels, pointwise CIs. The categorical conditions deliberately have no lines.
fig,axes=plt.subplots(2,3,figsize=(6.5,4.25),sharey=True,sharex=True)
fig.subplots_adjust(left=.10,right=.99,bottom=.24,top=.92,hspace=.53,wspace=.22)
for index,(family,label,ax) in enumerate(zip(FAMILIES[:6],LABELS[:6],axes.flat)):
    entries=[next(r for r in DATA['seed_cluster_intervals'] if r['family']==family and r['sources']==s) for s in SOURCES]
    y=np.array([r['rate']*100 for r in entries]);lo=np.array([r['interval'][0]*100 for r in entries]);hi=np.array([r['interval'][1]*100 for r in entries])
    ax.errorbar(range(3),y,yerr=[y-lo,hi-y],fmt='o',linestyle='none',
                color=BLUE,ecolor=BLUE,markersize=4.5,capsize=3,elinewidth=1.1)
    ax.set_title(f'({chr(97+index)}) {label}',loc='left',fontweight='bold',fontsize=9)
    ax.set_ylim(-5,110);ax.set_xlim(-.4,2.4);ax.set_yticks([0,25,50,75,100]);ax.set_xticks(range(3),[str(s) for s in SOURCES])
    ax.tick_params(length=2.5,pad=3);ax.grid(axis='y',color='#DDE4E9',lw=.6,zorder=0)
    for x,rate in enumerate(y):
        ax.annotate(f'{rate:g}%',(x,rate),xytext=(0,8 if rate<90 else -15),textcoords='offset points',ha='center',fontsize=8)
fig.supylabel('Accepted target instances (%)',fontsize=8.5,x=.012)
fig.text(.55,.14,'Source condition (categorical)',ha='center',fontsize=8.5)
fig.text(.10,.07,'Pointwise descriptive 95% seed-cluster percentile intervals; 10 seeds.',fontsize=8)
fig.text(.10,.025,'Repeated instances are not independent; one exempt difference target is included.',fontsize=8)
save(fig,'figure_02_valid_family_intervals')

# Current/history repeated-exposure totals. Gray patterned exemptions are not verification.
r=DATA['recorded_aggregate']
fig,ax=plt.subplots(figsize=(6.5,2.65))
fig.subplots_adjust(left=.25,right=.985,top=.70,bottom=.39)
exempt=[r['current_source']['exempt'],r['historical_ingested']['exempt']]
supported=[r['current_source']['supported'],r['historical_ingested']['supported']]
ax.barh([1,0],exempt,color=GRAY,edgecolor='#74818C',lw=.6,height=.55,hatch='///',label='Exempt (not verified)')
ax.barh([1,0],supported,left=exempt,color=BLUE,height=.55,label='Supported nonexempt magnitude')
for y,e,s in zip([1,0],exempt,supported):
    ax.text(e/2,y,f'{e:,}',ha='center',va='center',fontsize=8.5)
    ax.text(e+s/2,y,f'{s:,}',ha='center',va='center',fontsize=8.5,color='white')
    ax.text(e+s+120,y,f'n = {e+s:,}',ha='left',va='center',fontsize=8)
ax.set_yticks([1,0],['Current source','Earlier ingested sources']);ax.tick_params(length=2,pad=3)
ax.set_xlim(0,10000);ax.set_xticks([0,2000,4000,6000,8000],['0','2,000','4,000','6,000','8,000'])
ax.set_ylim(-.55,1.55)
ax.set_xlabel('Across-prefix numeric-leaf exposures (count)',labelpad=5,fontsize=8.5)
ax.legend(loc='lower center',bbox_to_anchor=(.41,1.15),frameon=False,ncol=1,
          columnspacing=1,handlelength=1.7,labelspacing=.45)
fig.text(.015,.145,'137 negative source leaves; 290 sign-loss exposures across all temporal prefix checks,',fontsize=8)
fig.text(.015,.095,'including future sources. Supported magnitude does not establish signed or semantic correctness.',fontsize=8)
fig.text(.015,.035,'Exposures are repeated, not independent observations.',fontsize=8)
save(fig,'figure_03_recorded_quotability')

(HERE/'RENDERED_TEXT_LABELS.json').write_text(json.dumps(TEXTS,indent=2)+'\n')
(HERE/'FIGURE_MANIFEST.json').write_text(json.dumps({
    'scope':'Formatting only. Same frozen component data, labels and inspection boundary; no new experiments.',
    'script_sha256':SHA(Path(__file__)),'data_sha256':SHA(HERE/'data.json'),
    'architecture_layout_sha256':SHA(HERE/'architecture_layout.json'),
    'geometry_checks':GEOMETRY,'artifacts':OUTPUTS},indent=2)+'\n')
print(json.dumps({'status':'PASS','figure_count':4,'artifact_count':len(OUTPUTS),'minimum_font_pt':8}))
