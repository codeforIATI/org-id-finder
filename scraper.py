import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from itertools import zip_longest
from urllib.parse import quote_plus
from os import environ
from datetime import datetime

import orgidfinder

import iatikit

def zip_discard_compr(*iterables, sentinel=None):
    return [[entry for entry in iterable if entry is not sentinel]
            for iterable in zip_longest(*iterables, fillvalue=sentinel)]

output_dir = Path('docs')
scrape_started_at = datetime.now().isoformat()

if len(sys.argv) > 1 and sys.argv[1] == '--refresh':
    iatikit.download.data()

guide = orgidfinder.setup_guide()

data = []
for dataset in iatikit.data().datasets.where(filetype='organisation'):
    org_infos = orgidfinder.parse_org_file(dataset)
    for org_info in org_infos:
        if org_info is None: continue
        org_info['org_type'] = guide._org_types.get(org_info['org_type_code'])
        id_ = quote_plus(org_info['org_id'])
        with open(Path(f'{output_dir}/data/{id_}.json'), 'w') as f:
            json.dump(org_info, f)
        data.append(org_info)

with open(Path(f'docs/downloads/org-ids.json'), 'w') as f:
    json.dump(data, f)

fieldnames = ['org_id', 'name', 'org_type', 'org_type_code', 'source_dataset', 'source_url']
with open(Path(f'docs/downloads/org-ids.csv'), 'w') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for d in data:
        w.writerow({f: d.get(f, '') if f != 'name' else d['name'][d['lang']] for f in fieldnames})

counter = defaultdict(set)
minlen = 3
for d in data:
    default_lang = d['lang']
    default_name = d['name'].get(default_lang)
    if not default_name:
        continue

    text = d['org_id'].lower()
    for subtext in set([text[i: j] for i in range(len(text)) for j in range(i + 1, len(text) + 1) if len(text[i:j]) == minlen]):
        counter[subtext].add((default_name, d['org_id']))

    for lang, name in d['name'].items():
        if not name:
            continue
        text = name.lower()
        if lang != default_lang:
            name += ' ({})'.format(d['name'][default_lang])
        for subtext in set([text[i: j] for i in range(len(text)) for j in range(i + 1, len(text) + 1) if len(text[i:j]) == minlen]):
            counter[subtext].add((name, d['org_id']))

for k, v in sorted(counter.items()):
    sorted_v = sorted(v, key=lambda x: x[0])
    quoted_k = quote_plus(k)
    with open(Path(f'{output_dir}/data/lookup/{quoted_k}.json'), 'w') as f:
        json.dump(sorted_v, f)

scrape_finished_at = datetime.now().isoformat()
with(open(Path(f'{output_dir}/data/status.json'), 'w')) as f:
    json.dump({
        'started_at': scrape_started_at,
        'finished_at': scrape_finished_at,
    }, f)
