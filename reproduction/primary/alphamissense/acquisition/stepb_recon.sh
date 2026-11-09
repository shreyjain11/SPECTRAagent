#!/usr/bin/env bash
set -u
cd ~/spectra_alphamissense
MM=~/spectra_alphamissense/bin/mmseqs/bin/mmseqs

echo '== disk free =='
df -h / /home 2>/dev/null | awk 'NR==1 || /\/$|\/home/'
echo
echo '== du (work/data/artifacts) =='
du -sh work data artifacts 2>/dev/null

echo
echo '== kept panel (disk = source of truth) =='
wc -l artifacts/step_a_kept_assays.csv
echo -n 'unique proteins (col am_accession): '
tail -n +2 artifacts/step_a_kept_assays.csv | cut -d, -f3 | sort -u | wc -l

echo
echo '== mmseqs =='
ls bin/mmseqs/bin/
$MM version 2>&1 | head -1

echo
echo '== mmseqs prebuilt databases (UniRef rows) =='
$MM databases 2>&1 | grep -iE 'uniref|uniprotkb' | head

echo
echo '== ProteinGym DMS substitutions zip URL checks =='
for u in \
  https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.1/DMS_ProteinGym_substitutions.zip \
  https://marks.hms.harvard.edu/proteingym/ProteinGym/DMS_ProteinGym_substitutions.zip \
  https://marks.hms.harvard.edu/proteingym/DMS_ProteinGym_substitutions.zip ; do
  echo "-- $u"
  curl -sIL --max-time 40 "$u" 2>&1 | grep -iE 'HTTP/|content-length|content-type|location' | head
done
