"""Scope supporting records separately from the preferred inline calculations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC = ('dataset_split','axis_levels','model_evaluation','curve','insight')
def read(p): return json.loads((ROOT/p).read_text())
def write(p,d): (ROOT/p).write_text(json.dumps(d,indent=2)+'\n')

def main():
    records={}
    for p in sorted((ROOT/'analyses').glob('*/*.json')):
        d=json.loads(p.read_text()); impl=d['inline_implementation']; identifier=d['id']
        for key in SCIENTIFIC:
            d[key].setdefault('scope','supporting_implementation')
        d['scientific_record_scope']={
            'supporting_fields':list(SCIENTIFIC),
            'supporting_implementation':'implementation',
            'current_fields':'current_inline_analysis',
            'historical_result':'historical_decision',
            'note':'Supporting fields describe the separately retained implementation. Use current_inline_analysis for the preferred notebook; historical equivalence is not inferred from successful execution.'}
        d.setdefault('reconstruction_notes_scope','supporting_implementation')
        current=d.setdefault('current_inline_analysis',{
            'notebook':impl['notebook'],
            'dataset_and_methods':{'sections':[1,2,3,4],'description':'Use the acquisition, sample selection, axis construction and model evaluation shown by this inline notebook.'},
            'verification_boundary':'Saved executed outputs and their provenance; not a new full execution performed by the November 15 consistency correction.'})
        current['notebook']=impl['notebook']
        current['execution_evidence']=impl['execution_evidence']
        current['notebook_sha256']=impl['published_notebook_sha256']
        current['result_location']=d['preferred_result']
        if identifier.startswith(('esmfold2-codex-','esmfold2-opus-')) and identifier!='esmfold2-codex-r1/test-04':
            current['historical_comparison']={
                'relationship':'Current reconstruction of the stated question; exact historical sample and prediction identity is not established.',
                'original_records':{'path':'traceability_review.json','record_id':identifier}}
        if identifier=='conch-opus-r2/test-01':
            current['blur_comparison']={
                'source':'Saved scientific_results display in sections 5 and 6; values rounded as displayed.',
                'samples_per_level':1080,'blur_sigmas':[0,1,2,3],
                'conch_accuracy_drop':0.537963,'reference_accuracy_drop':0.297222,
                'additional_conch_loss':0.240741,'additional_loss_ci95':[0.20092592592592592,0.28055555555555556],
                'historical_additional_loss':0.219,
                'scope':'Controlled blur on the NCT source family. The current reconstruction and original reported estimate are separate results.'}
        records[identifier]=d
        p.write_text(json.dumps(d,indent=2)+'\n')
    notes=read('reconstruction.json')
    for row in notes:
        row['scope']='supporting_implementation'
        row['current_inline_record']='analyses/'+row['id']+'.json#/current_inline_analysis'
        if row['id'].startswith(('am-opus-r1/','am-opus-r2/')):
            row['current_correction']='The preferred inline notebook now restores all 1,934 omitted variants and maps canonical residue coordinates: 273,135 variants before axis eligibility. The preserved notes above describe the historical supporting inputs.'
    write('reconstruction.json',notes)
    for filename,key in [('traceability_review.json','entries'),('NONPRIMARY_REVIEW.json','analyses')]:
        review=read(filename)
        review['implementation_scope']='This review and its counts describe supporting implementations and original historical traceability. Preferred inline reconstructions are described separately in each analysis current_inline_analysis.'
        for row in review[key]:
            identifier=row.get('id',row.get('analysis_id'))
            row['current_inline_record']='analyses/'+identifier+'.json#/current_inline_analysis'
            if identifier.startswith(('am-opus-r1/','am-opus-r2/')):
                row['current_correction']='The preferred inline cohort is corrected and includes 273,135 variants (1,934 restored), before axis-specific eligibility; historical artifact availability and protocol timing remain separate questions.'
        write(filename,review)
    index=read('index.json');index['preferred_scientific_fields']='current_inline_analysis'
    index['supporting_scientific_fields']=list(SCIENTIFIC)
    write('index.json',index)
    print(f'Scoped supporting/current scientific fields for {len(records)} records.')

if __name__=='__main__':main()
