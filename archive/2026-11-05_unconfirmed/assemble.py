import re, sys
S='.'
front=open('paper_front.md',encoding='utf-8').read()
parts=[open(p,encoding='utf-8').read() for p in ['paper_part_intro.md','paper_part_related_gov.md','paper_part_design.md','paper_part_trust.md','paper_part_experiments.md','paper_part_comparative.md','paper_part_benchmarks.md']]
tail=open('paper_part_tail.md',encoding='utf-8').read()
figs=open('paper_figures.md',encoding='utf-8').read()
fig1, fig2 = figs.split('\n\n<figure>\n')[0], '<figure>\n'+figs.split('\n\n<figure>\n')[1]
parts[2]=parts[2].replace('### 4.2 The EventLog and derived history', fig1+'\n\n### 4.2 The EventLog and derived history',1).replace('### 4.4 Numeric provenance: the NumberLedger', fig2+'\n\n### 4.4 Numeric provenance: the NumberLedger',1)
svg=open('figure_e1_false_accept.svg',encoding='utf-8').read()
fig3='<figure>\n'+svg+'\n<figcaption>Figure 3. Log scale. False-accept rate of fabricated six-figure amounts against the number of synthetic tool results, three arms, mean over five seeds with 95% confidence-interval whiskers where they exceed the marker. The production rule stays below 0.6%; a pooled ledger grows with its size until the cap and without bound otherwise.</figcaption>\n</figure>'
parts[4]=parts[4].replace('**E2. Honest derived claims.**', fig3+'\n\n**E2. Honest derived claims.**',1)
svg4=open('figure_real_cap.svg',encoding='utf-8').read()
fig4='<figure>\n'+svg4+'\n<figcaption>Figure 4. Three recorded turns through the ledger at four base caps: honest six-figure sums over the last read accepted (blue) and fabricated six-figure amounts in the read\'s band accepted (orange). Raising the cap buys about two points of honest recall per point of fabrication acceptance.</figcaption>\n</figure>'
parts[4]=parts[4].replace('Table 8. Recorded turns through the ledger', fig4+'\n\nTable 8. Recorded turns through the ledger',1)
refs=[]
for p in ['paper_refs_academic.md','paper_refs_gov.md','paper_refs_industry.md']:
    refs += [l for l in open(p,encoding='utf-8').read().strip().splitlines() if l.startswith('- ')]
allrefs=sorted(set(refs), key=lambda l: re.sub(r'^- ','',l).lower())
refs_md="## References\n\n"+"\n".join(allrefs)+"\n"
body_tail, appendix = tail.split('## Appendix A',1)
paper="\n\n".join([front.strip()]+[p.strip() for p in parts]+[body_tail.strip(), refs_md.strip(), '## Appendix A'+appendix])
open('paper_final.md','w',encoding='utf-8').write(paper+"\n")
body=paper.split('\n---\n',1)[1]
print(len(body.split()),'words;', 'EMDASH' if '—' in paper else 'no em dash;', len(allrefs),'references')
