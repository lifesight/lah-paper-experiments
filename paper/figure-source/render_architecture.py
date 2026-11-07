#!/usr/bin/env python3
"""Draw LAH's approved architecture interfaces and explicit evaluation boundary.
No experiments, source fetching, HEELO image reuse or implementation inference.
"""
from pathlib import Path
import hashlib,json,os,tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'lah-publication005-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.text import Text
P=Path(__file__).resolve().parent
A=json.loads((P/'architecture_layout.original.json').read_text())
BLUE='#0077BB';INK='#25313B'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','text.color':INK})
fig,ax=plt.subplots(figsize=(6.5,4.25));fig.subplots_adjust(left=.012,right=.988,top=.99,bottom=.025)
ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
# Preserve the nine interfaces and ten relations. Center the measured component
# after removing the author-requested explanatory annotation panel.
boxes={
'question':(.015,.77,.145,.13),'context':(.205,.77,.23,.13),
'evidence':(.48,.77,.19,.13),'answer':(.72,.77,.265,.13),
'ledger':(.365,.49,.27,.16),'action':(.015,.25,.25,.105),
'approval':(.32,.25,.25,.105),'permission':(.625,.25,.36,.105),
'eventlog':(.015,.075,.97,.09)}
for b in A['boxes']:
 x,y,w,h=boxes[b['id']];measured=b['id']=='ledger'
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.004,rounding_size=0.008',fc='#E4F0F7' if measured else '#F5F7F8',ec=BLUE if measured else '#8D9AA4',lw=1.25 if measured else .65))
 ax.text(x+w/2,y+h/2,b['text'],ha='center',va='center',fontsize=8,linespacing=1.25)
points=[((.16,.835),(.205,.835)),((.435,.835),(.48,.835)),((.67,.835),(.72,.835)),((.575,.77),(.50,.65)),((.635,.57),(.85,.77)),((.265,.3025),(.32,.3025)),((.57,.3025),(.625,.3025)),((.14,.25),(.14,.165)),((.445,.25),(.445,.165)),((.805,.25),(.805,.165))]
for rel,pts in zip(A['arrows'],points):
 ax.add_patch(FancyArrowPatch(*pts,arrowstyle='-|>',mutation_scale=8.5,lw=.8,color='#8D9AA4' if rel['style']=='--' else '#5B6974',linestyle=rel['style']))
ax.text(.575,.945,'SOURCE RESULT',ha='center',fontsize=8,fontweight='bold',color='#52616C')
ax.text(.50,.455,'MEASURED HERE',ha='center',fontsize=8,fontweight='bold',color=BLUE)
ax.text(.50,.415,'Retained evidence → numeric decision',ha='center',fontsize=8,color=BLUE)
ax.text(.015,.955,'Inspected architecture ≠\nmeasured system reliability',ha='left',va='center',fontsize=8,color='#52616C',linespacing=1.25)
ax.text(.445,.375,'APPROVAL BOUNDARY — INSPECTED INTERFACES',ha='center',fontsize=8,color='#52616C')
ax.text(.015,.025,'Recording interfaces shown; all-path logging and distributed guarantees were not evaluated.',ha='left',fontsize=8,color='#52616C')
fig.canvas.draw();renderer=fig.canvas.get_renderer();texts=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text()]
w,h=fig.canvas.get_width_height()
assert all(t.get_fontsize()>=8 for t in texts)
assert all((lambda b:b.x0>=-1 and b.y0>=-1 and b.x1<=w+1 and b.y1<=h+1)(t.get_window_extent(renderer)) for t in texts)
labels=[t.get_text() for t in texts]
assert all(b['text'] in labels for b in A['boxes'])
artifacts={}
for ext in ['pdf','svg','png']:
 p=P/f'figure_00_architecture.{ext}';kw={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}
 fig.savefig(p,dpi=300,facecolor='white',**kw);artifacts[p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
plt.close(fig)
r={'status':'PASS','scope':'Architecture figure interface/annotation and page geometry only; no new science','width_inches':6.5,'height_inches':4.25,'minimum_font_pt':8,'all_text_in_page':True,'original_nine_interface_labels_preserved':True,'original_ten_relations_preserved':A['arrows'],'measured_interface_only':'NumberLedger','author_requested_annotation_removed':True,'all_path_logging_caveat_preserved':True,'rendered_labels':labels,'artifacts':artifacts,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(P/'ARCHITECTURE_FIGURE_VALIDATION.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
