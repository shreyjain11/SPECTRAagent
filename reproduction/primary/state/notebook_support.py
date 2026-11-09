"""Readable notebook display helpers; scientific calculations are original source."""
import importlib.util
import inspect
import io
import json

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import pandas as pd
from IPython.display import display, Markdown, Image
import recovered_pipeline as rp


def show_acquisition(stage):
    records=json.loads((rp.COMPUTED/'initial/artifacts/download_revisions.json').read_text())
    table=pd.DataFrame(records)
    display(table[['repo','revision']].drop_duplicates().reset_index(drop=True))
    print('Original evaluation used official scored CSVs. The replay loads the original cached bytes at these revisions.')
    print('All 55 score filenames and the three metadata downloads are in computed/initial/artifacts/download_revisions.json.')
    print('Initial acquisition implementation: original/state_generalizability_20260602_single_controller/scripts/run_state_spectra_audit.py')
    if stage!='initial':
        print('Annotation snapshots and split inputs: original/state_generalizability_continued_20260603/external and original/state_generalizability_20260602_single_controller/external/state/state_preprint_toml_files.')
        sources=json.loads((rp.CONTINUED/'artifacts/multi_pathway_source_manifest.json').read_text())
        display(pd.DataFrame(list(sources['sources'].items()),columns=['source','original_download_URL']))


def show_code(stage, number):
    initial,base=rp.modules()
    functions=[]
    if stage=='initial':
        functions=[initial.load_target_results,initial.load_tahoe_metadata,
                   initial.compute_context_chemical_axis if number==1 else initial.dose_axis]
    elif stage=='replogle':
        functions=[base.infer_replogle_train_sets,base.add_replogle_features]
        functions += [base.freeze_replogle_reactome_axis] if number==3 else [base.quantile_cutpoints_for_axis,base.assign_support_bins]
    elif stage=='parse':
        functions=[base.ligand_family,base.infer_parse_train_sets,base.run_parse_family_axis]
    elif stage=='controls':
        m=rp.load_module('display_controls',rp.CONTINUED/'scripts/state_replogle_controls.py')
        functions=[m.standardized_ols] if number==10 else [m.high_low_gaps,m.matched_pathway_count_gaps]
    elif stage=='zeroshot':
        m=rp.load_module('display_zero',rp.CONTINUED/'scripts/state_replogle_zeroshot_confirmation.py')
        functions=[m.main]
    elif stage=='ontology':
        m=rp.load_module('display_multi',rp.CONTINUED/'scripts/state_multi_pathway_support.py')
        parser={13:m.reactome_collection,14:m.hgnc_group_collection,15:m.parse_go_collections,16:m.parse_go_collections,17:m.parse_go_collections,18:m.parse_wikipathways,19:m.parse_kegg}[number]
        functions=[parser,m.build_fewshot_examples,m.build_zeroshot_examples,m.test_collection]
    for function in functions:
        display(Markdown('```python\n'+inspect.getsource(function)+'\n```'))


def show_curve(table):
    display(table)
    if 'overlap_at_N_mean' not in table or 'level' not in table:
        return
    groups=[c for c in ['spectra_subset','representation'] if c in table]
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    levels=sorted(table.level.astype(str).unique())
    order={value:i for i,value in enumerate(levels)}
    grouped=table.groupby(groups,dropna=False) if groups else [('STATE',table)]
    for key,part in grouped:
        part=part.copy();part['plot_x']=part.level.astype(str).map(order);part=part.sort_values('plot_x')
        ax.plot(part.plot_x,part.overlap_at_N_mean,marker='o',label=str(key),linewidth=1.4)
    ax.set_xticks(range(len(levels)),levels,rotation=25,ha='right')
    ax.set_ylabel('Original STATE overlap@N mean');ax.set_xlabel('Original declared level')
    ax.legend(fontsize=7);ax.spines[['top','right']].set_visible(False)
    stream=io.BytesIO();fig.savefig(stream,format='png',dpi=130);plt.close(fig)
    display(Image(data=stream.getvalue()))
    print('Curves are recalculated means under the original grouping rule. No new confidence bands have been added.')


def display_json(path):
    value=json.loads(path.read_text())
    display(Markdown('```json\n'+json.dumps(value,indent=2,ensure_ascii=False)+'\n```'))


def compare_curve(relative, initial=False):
    computed=rp.COMPUTED/('initial' if initial else 'continued')/'artifacts'/relative
    original=(rp.INITIAL if initial else rp.CONTINUED)/'artifacts'/relative
    new=pd.read_csv(computed);old=pd.read_csv(original)
    keys=[c for c in ['subset','spectra_subset','representation','level'] if c in new and c in old]
    columns=[c for c in ['n_rows','similarity_mean','overlap_at_N_mean','de_sig_genes_recall_mean','pearson_delta_mean'] if c in new and c in old]
    if keys and columns:
        result=rp.compare_table(new,original,keys,columns)
        display(result)
        assert result['all_match'], 'A historical comparison differs; inspect the difference before interpreting the result.'
    return new
