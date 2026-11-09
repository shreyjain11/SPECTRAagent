"""Version-aware download and preparation recipes for the seven original AM axes.

These commands are reconstructed from identified public sources, not claimed to
be recovered shell history. No network or bulk work occurs on import. Original
scientific scripts and archived outputs are never edited by this module.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT.parent
PRIMARY = BUNDLE / 'am-primary'
INPUT = PRIMARY / 'inputs'


def sha256(path, decompress=False):
    h = hashlib.sha256()
    opener = gzip.open if decompress else open
    with opener(path, 'rb') as src:
        for part in iter(lambda: src.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def sources():
    return json.loads((ROOT / 'download_sources.json').read_text())


def download(key, cache=None):
    """Stream a pinned public file to cache; reject any known hash/size mismatch."""
    spec = sources()[key]
    cache = Path(cache or ROOT / 'downloads')
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / spec['filename']
    if not target.exists():
        part = target.with_suffix(target.suffix + '.partial')
        req = urllib.request.Request(spec['url'], headers={'User-Agent': 'SPECTRA historical reproduction'})
        with urllib.request.urlopen(req, timeout=90) as response, part.open('wb') as out:
            shutil.copyfileobj(response, out, 8 * 1024 * 1024)
        part.replace(target)
    if spec.get('bytes') is not None and target.stat().st_size != spec['bytes']:
        raise ValueError(f'{key}: source size differs from the recorded version; refusing to stage {target}')
    digest = sha256(target)
    if spec.get('sha256') and digest != spec['sha256']:
        raise ValueError(f'{key}: SHA256 mismatch ({digest}); refusing to substitute a newer or different source')
    if spec.get('md5'):
        h = hashlib.md5()
        with target.open('rb') as src:
            for part in iter(lambda: src.read(8 * 1024 * 1024), b''):h.update(part)
        if h.hexdigest() != spec['md5']:raise ValueError(f'{key}: published release MD5 mismatch')
    # Whole-archive hashes were not retained for ProteinGym. Every selected
    # member must match its original SHA256 in stage_zip_members below.
    record = dict(source=key, url=spec['url'], path=str(target), bytes=target.stat().st_size,
                  sha256=digest, check=(spec.get('hash_origin', 'original file hash') if spec.get('sha256') else
                                       'published archive MD5' if spec.get('md5') else 'member validation required'))
    target.with_suffix(target.suffix + '.receipt.json').write_text(json.dumps(record, indent=2))
    return target


def _stage(source, target, expected_hash):
    source, target = Path(source), Path(target)
    if sha256(source) != expected_hash:
        raise ValueError(f'Prepared input does not match the original: {source}')
    if target.exists():
        if sha256(target) != expected_hash:
            raise ValueError(f'Existing input has changed; preserve it and resolve before replacing: {target}')
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def stage_zip_members(archive, kind, stage=True):
    """Select only the original 73 DMS files or 66 MSAs; verify before staging."""
    if kind == 'dms':
        manifest = json.loads((PRIMARY / 'INPUT_MANIFEST.json').read_text())
        items = [dict(filename=Path(x['path']).name, sha256=x['sha256'], bytes=x['bytes'])
                 for x in manifest if x['path'].startswith('inputs/proteingym/dms_final_73/')]
        destination = INPUT / 'proteingym/dms_final_73'
        assert len(items) == 73
    elif kind == 'msa':
        items = json.loads((BUNDLE / 'upstream_checks/opus_r2_msa_member_hashes.json').read_text())
        destination = BUNDLE / 'upstream_checks/downloaded_msa'
        assert len(items) == 66
    else:
        raise ValueError('kind must be dms or msa')
    validated = []
    with zipfile.ZipFile(archive) as z:
        by_name = {}
        for name in z.namelist():
            if not name.endswith('/'):
                by_name.setdefault(Path(name).name, []).append(name)
        # Validate all selected members before creating or replacing any input.
        for item in items:
            matches = by_name.get(item['filename'], [])
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one archive member: {item['filename']}; found {matches}")
            h = hashlib.sha256()
            with z.open(matches[0]) as src:
                for part in iter(lambda: src.read(8 * 1024 * 1024), b''):h.update(part)
            if h.hexdigest() != item['sha256'] or z.getinfo(matches[0]).file_size != item['bytes']:
                raise ValueError(f"{item['filename']}: downloaded member differs from the historical input")
            validated.append(dict(**item, member=matches[0], destination=str(destination / item['filename'])))
        if stage:
            destination.mkdir(parents=True, exist_ok=True)
            for item in validated:
                target = Path(item['destination'])
                if target.exists():
                    if sha256(target) != item['sha256']:raise ValueError(f'Existing file changed: {target}')
                else:
                    with z.open(item['member']) as src, target.open('wb') as out:shutil.copyfileobj(src, out)
    return dict(kind=kind, verified_members=len(validated), staged=stage, destination=str(destination), members=validated)


def prepare_gnomad(cache=None):
    source = download('gnomad', cache)
    target = source.parent / 'gnomad_constraint.tsv'
    with gzip.open(source, 'rb') as src, target.open('wb') as out:shutil.copyfileobj(src, out)
    return _stage(target, INPUT / 'clinvar/gnomad_constraint.tsv',
                  '78f14346180de3fb552747099d9a34238ca535924418a3596d75f45654837d69')


def prepare_clinical(cache=None):
    """Download exact VCF/released scores, run original join, and stage its exact result."""
    if shutil.which('bcftools') is None:
        raise RuntimeError('The original clinical constructor requires bcftools on PATH. Install bcftools, then rerun this cell.')
    cache = Path(cache or ROOT / 'downloads')
    vcf = download('clinvar', cache)
    scores = download('am_hg38', cache)
    work = cache / 'clinical_join'
    data, out = work / 'data', work / 'work'
    data.mkdir(parents=True, exist_ok=True);out.mkdir(exist_ok=True)
    for source, name in [(vcf, 'clinvar.vcf.gz'), (scores, 'AlphaMissense_hg38.tsv.gz')]:
        dest = data / name
        if not dest.exists():dest.symlink_to(source.resolve())
        elif dest.resolve() != source.resolve():raise ValueError(f'Unexpected prior staged source: {dest}')
    original = PRIMARY / 'code/build_benchmark.py'
    code = original.read_text()
    old_data = 'DATA = "/home/shreyjain/spectra_alphamissense/data"'
    old_out = 'OUT  = "/home/shreyjain/spectra_alphamissense/work"'
    if code.count(old_data) != 1 or code.count(old_out) != 1:
        raise ValueError('Original clinical constructor has changed; review path adaptation before running it')
    code = code.replace(old_data, f'DATA = {str(data)!r}').replace(old_out, f'OUT = {str(out)!r}')
    runner = work / 'build_benchmark_paths_only.py';runner.write_text(code)
    subprocess.run([sys.executable, str(runner)], check=True)
    return _stage(out / 'clinvar_am_benchmark.tsv', INPUT / 'clinvar/clinvar_am_benchmark.tsv',
                  '783a79533ae1aa4ae4b7d99615f78959fd134aa4913666407720c4bc7f6ad481')


def prepare_official_subset(cache=None):
    """Select the retained 64 accessions from released predictions; no model inference."""
    source = download('am_substitutions', cache)
    with (INPUT / 'proteingym/kept_assays_verified.tsv').open() as f:
        accessions = {row['resolved_accession'] for row in csv.DictReader(f, delimiter='\t')}
    assert len(accessions) == 64
    plain = source.parent / 'official_scores_64_proteins.tsv'
    rows = 0
    with gzip.open(source, 'rt', newline='') as src, plain.open('w', newline='') as out:
        out.write('uniprot_id\tprotein_variant\tam_pathogenicity\tam_class\n')
        for line in src:
            if line.startswith('#'):continue
            if line.split('\t', 1)[0] in accessions:
                out.write(line.rstrip('\r\n') + '\n');rows += 1
    expected_content = '842c6638df5a0f05fd2e45e9e58d395d9718c8ec5338bb8649c3173050c92c58'
    if rows != 955738 or sha256(plain) != expected_content:
        raise ValueError('Official score subset differs from the exact retained 955,738-row input')
    target = INPUT / 'official_scores_64_proteins.tsv.gz'
    existed = target.exists()
    if target.exists():
        if sha256(target, decompress=True) != expected_content:raise ValueError('Existing score subset differs')
    else:
        # Preserve the original gzip filename, timestamp, compression and text
        # flush so the subsequent unchanged byte-hash check also succeeds.
        target.parent.mkdir(parents=True, exist_ok=True)
        with plain.open('r', newline='') as src, target.open('wb') as raw:
            with gzip.GzipFile(filename='official_scores_64_proteins.tsv', mode='wb',
                               fileobj=raw, compresslevel=9, mtime=1793946972) as z:
                with io.TextIOWrapper(z, encoding='utf-8', newline='') as out:shutil.copyfileobj(src, out)
    if sha256(target) != '1657bce1cad681b6755831da727ceb00b5ee9d0a024e274eec4c05acbbdf80b1':
        raise ValueError('Prediction content matches, but gzip bytes differ from the historical envelope; use the retained bundled gzip input')
    return dict(rows=rows, proteins=len(accessions), content_sha256=expected_content,
                prepared=str(plain), input=str(target), compression=('Existing compressed input preserved after exact decompressed-content comparison' if existed else 'New compressed input reproduced the original gzip bytes'))


def prepare_axis(axis, cache=None, include_alignments=False):
    """Download and connect source inputs for one primary notebook (bulk opt-in)."""
    axis = int(axis)
    if axis in [1, 2]:
        result = dict(clinical_benchmark=str(prepare_clinical(cache)))
        if axis == 2:result['gnomad'] = str(prepare_gnomad(cache))
        if axis == 1:
            hits = INPUT / 'clinvar/msa_hits.m8.gz'
            if sha256(hits, decompress=True) != 'cad2f9fe07a1eb492148b560cecdfd162a3652f143d1a5678a4b67972b40b13f':
                raise ValueError('Retained original UniRef50 search-hit file differs')
            result['homology_hits'] = str(hits)
            result['homology_note'] = 'Uses complete retained original search hits; optional full database/search recipe is separate.'
        return result
    if axis not in range(3, 8):raise ValueError('Expected primary axis 1–7')
    result = dict(dms=stage_zip_members(download('proteingym_dms', cache), 'dms'),
                  scores=prepare_official_subset(cache))
    if include_alignments:
        result['msa'] = stage_zip_members(download('proteingym_msa', cache), 'msa')
    return result


def check_packaged_inputs(axis):
    """Cheap executed check; does not imply downloads or inference were rerun."""
    manifest = json.loads((PRIMARY / 'INPUT_MANIFEST.json').read_text())
    paths = ['inputs/clinvar/clinvar_am_benchmark.tsv'] if int(axis) < 3 else [
        x['path'] for x in manifest if x['path'].startswith('inputs/proteingym/dms_final_73/')]
    if int(axis) == 2:paths.append('inputs/clinvar/gnomad_constraint.tsv')
    expected = {x['path']:x for x in manifest}
    for name in paths:
        if sha256(PRIMARY / name) != expected[name]['sha256']:raise ValueError(f'Changed input: {name}')
    if int(axis) >= 3:
        if sha256(INPUT / 'official_scores_64_proteins.tsv.gz', True) != '842c6638df5a0f05fd2e45e9e58d395d9718c8ec5338bb8649c3173050c92c58':raise ValueError('Changed prediction subset')
    return dict(axis=int(axis), verified_packaged_files=len(paths), downloaded_in_this_cell=False,
                prepared_inputs=str(INPUT), official_score_release=True, new_model_inference=False)


def rebuild_uniref_search(cache=None, mmseqs=None):
    """Optional 268 GB archived-database download and original clinical search.

    Requires Linux x86-64 for the supplied historical MMseqs executable, or an
    explicitly supplied executable of the same version. Original complete hit
    bytes remain the default for notebook replay.
    """
    import platform
    if mmseqs is None and (platform.system() != 'Linux' or platform.machine() not in ['x86_64', 'AMD64']):
        raise RuntimeError('Run this optional full search on Linux x86-64, or supply the original-version MMseqs executable.')
    mmseqs = str(mmseqs or BUNDLE / 'upstream_checks/bin/mmseqs')
    version = subprocess.check_output([mmseqs, 'version'], text=True).strip()
    if version != 'fd711934753052544df18fa1dff8c762d6fe2188':raise ValueError('Use the original MMseqs version: ' + version)
    archive = download('uniref', cache)
    work = archive.parent / 'uniref50_search';work.mkdir(exist_ok=True)
    # Stream the official tar and extract only its UniRef50 FASTA, never paths
    # supplied by the archive. Other UniRef families are not used by this axis.
    fasta = work / 'uniref50.fasta';found = False
    if not fasta.exists():
        with tarfile.open(archive, 'r|gz') as tar:
            for member in tar:
                if not member.isfile() or Path(member.name).name not in ['uniref50.fasta', 'uniref50.fasta.gz']:continue
                with tar.extractfile(member) as src, fasta.open('wb') as out:
                    if member.name.endswith('.gz'):
                        with gzip.GzipFile(fileobj=src) as uncompressed:shutil.copyfileobj(uncompressed, out)
                    else:shutil.copyfileobj(src, out)
                found = True;break
        if not found:raise ValueError('Archived release did not contain uniref50.fasta(.gz)')
    db = work / 'uniref50_db'
    subprocess.run([mmseqs, 'createdb', str(fasta), str(db)], check=True)
    hits = work / 'msa_hits.m8'
    command = [mmseqs, 'easy-search', str(ROOT / 'work_quarantined/query.fasta'), str(db), str(hits),
               str(work / 'tmp_search'), '--threads', '16', '-s', '5.7', '--max-seqs', '10000', '-e', '1e-3',
               '-c', '0.5', '--cov-mode', '0', '--format-output', 'query,target,fident,qcov,evalue']
    subprocess.run(command, check=True)
    digest = sha256(hits)
    # Search ordering may differ. Report it; never silently replace the exact
    # original hit records used by the historical curve.
    record = dict(command=command, output=str(hits), sha256=digest,
                  byte_identical_to_original=digest == 'cad2f9fe07a1eb492148b560cecdfd162a3652f143d1a5678a4b67972b40b13f')
    (work / 'search_validation.json').write_text(json.dumps(record, indent=2))
    if not record['byte_identical_to_original']:
        raise ValueError('Fresh UniRef search differs from historical hit bytes; outputs saved separately. Historical notebook still uses its retained exact hits.')
    return record
