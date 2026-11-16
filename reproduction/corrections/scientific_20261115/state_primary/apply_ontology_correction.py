"""Correct the same copied regression helper in ontology checks 13-19."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=(Path(__file__).with_name('apply_correction.py')).read_text()
function=next(ast.literal_eval(t.value) for t in ast.parse(source).body if isinstance(t,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='FUNCTION' for n in t.targets))
function=function.replace('c_standardized_ols','m_clustered_support_fit').replace('c_SUPPORT_COL',"'support_norm_log_mean'").replace('reactome_pathway_count','feature_count').replace('support_log_mean_z','support_norm_log_mean_z')
wrapper='''def m_ols_support_coef(examples):
    result = m_clustered_support_fit(examples, m_TARGET_METRIC, True)
    support = next(c for c in result['coefficients'] if c['term']=='support_norm_log_mean_z')
    return {'n_rows':result['n_rows'], 'r2':result['r2'], **support}

'''
for test in range(13,20):
    path=ROOT/'inline/state/state-featured'/f'test-{test:02d}.ipynb'
    book=json.loads(path.read_text());cell=book['cells'][15];s=''.join(cell['source'])
    start=s.index('def m_ols_support_coef(');end=s.index('curve,trends=m_summarize',start)
    cell['source']=(s[:start]+function+wrapper+s[end:]).splitlines(keepends=True)
    s=''.join(book['cells'][14]['source'])+'\nThe adjusted few-shot regression uses context and representation indicators, without redundant subset indicators. Canonical-gene clusters preserve dependence across repeated contexts and representations. The 95% interval uses finite-sample-corrected cluster covariance and t(G−1) inference; the number of genes, design rank, exclusions and reference categories are displayed. This is a within-benchmark conditional association.\n'
    book['cells'][14]['source']=s.splitlines(keepends=True)
    s=''.join(book['cells'][17]['source']).replace("decision='Accept '+COLLECTION+' as supporting the training-support association' if supported else 'Reject '+COLLECTION+' as a consistent training-support association'", "decision=COLLECTION+(': all displayed confirmation endpoint contrasts favor higher support with at least three populated levels.' if supported else ': the displayed endpoint direction, ordering and populated-level conditions are not all met.')")
    s+="\nprint('Gene-clustered 95% interval:', controlled['ci_low'], controlled['ci_high'], '; gene clusters:', controlled['n_gene_clusters'])\nprint('The endpoint summary is descriptive and is not a full protocol certification or external replication.')\n"
    book['cells'][17]['source']=s.splitlines(keepends=True)
    book['cells'][16]['source']=('## 6. What the agent decided, and why\n\nThe endpoint summary describes the observed confirmation partitions. The separately adjusted few-shot coefficient now includes canonical-gene-clustered uncertainty. These alternate ontology features use the same released outcomes and are not independent experimental replications.\n').splitlines(keepends=True)
    path.write_text(json.dumps(book,indent=1,ensure_ascii=False)+'\n')
