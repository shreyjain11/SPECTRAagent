#!/usr/bin/env python3
"""Join the four full review ledgers without discarding model-specific details."""
import hashlib
import json
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FILES={'AlphaMissense':'alphamissense-entry-review.json','ESMFold2':'esmfold2-entry-review.json','STATE':'state-entry-review.json','CONCH':'conch-entry-review.json'}
EXPECTED={'ESMFold2':35,'STATE':44,'CONCH':30,'AlphaMissense':34}
index=json.loads((ROOT/'index.json').read_text())
canonical={a['id']:{**a,'model':inv['model']} for inv in index['investigations'] for a in inv['analyses']}
by_notebook={a['notebook']:a for a in canonical.values()}
assert len(canonical)==143 and len(by_notebook)==143
all_entries={};sources={}
for model,filename in FILES.items():
    raw=(HERE/filename).read_bytes();ledger=json.loads(raw)
    entries=ledger['entries'] if isinstance(ledger,dict) else ledger
    sources[model]={'file':filename,'sha256':hashlib.sha256(raw).hexdigest(),'entry_count':len(entries),'source_metadata':{k:v for k,v in ledger.items() if k!='entries'} if isinstance(ledger,dict) else {}}
    for entry in entries:
        # CONCH's source ID uses hyphens; its notebook is the canonical mapping.
        notebook=entry.get('notebook','').removeprefix('reproduction/')
        if notebook:
            assert notebook in by_notebook,(model,entry.get('id'),notebook)
            current=by_notebook[notebook]
        else:
            assert entry['id'] in canonical,(model,entry['id'])
            current=canonical[entry['id']]
        if model!='CONCH': assert entry['id']==current['id']
        assert current['model']==model,(model,current)
        assert current['id'] not in all_entries,current['id']
        all_entries[current['id']]={'id':current['id'],'model':model,'axis':current['axis'],'notebook':current['notebook'],'analysis_record':current['path'],'source_review_file':filename,'review':entry}
    assert len(entries)==EXPECTED[model]
assert set(all_entries)==set(canonical)
counts=dict(Counter(x['model'] for x in all_entries.values()));assert counts==EXPECTED
result={'schema_version':1,'review_date':'2026-11-15','scope':'Individual review records for all 143 inline entries across 28 investigations. Original model-specific findings and source ledger metadata are retained. The review is not a full reexecution of all notebooks or a recovery of exact historical audit chronology.','canonical_index':'../index.json','entry_count':143,'counts_by_model':counts,'sources':sources,'entries':[all_entries[id] for id in canonical]}
(HERE/'all-143-entry-review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
# Assert preservation of every original entry, including source identifiers and fields.
for model,filename in FILES.items():
    original=json.loads((HERE/filename).read_text());original=original['entries'] if isinstance(original,dict) else original
    consolidated=[x['review'] for x in result['entries'] if x['model']==model]
    assert sorted(original,key=lambda x:x['id'])==sorted(consolidated,key=lambda x:x['id'])
print('143 unique canonical entries: ESMFold2 35, STATE 44, CONCH 30, AlphaMissense 34. All source details preserved.')
