from os import environ
from datetime import datetime

import orgidfinder

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


def save_status(started_at, finished_at=None, success=False):
    scraperwiki.sqlite.save(
        ['started_at'],
        {
            'started_at': started_at,
            'finished_at': finished_at,
            'success': success,
        },
        'status'
    )


scrape_started_at = datetime.now().isoformat()
save_status(scrape_started_at)

key = ['org_id', 'lang', 'self_reported']
guide = orgidfinder.setup_guide()
datasets = orgidfinder.fetch_org_datasets_from_registry()
for dataset_name, url in datasets:
    try:
        org_infos = orgidfinder.parse_org_file(dataset_name, url)
    except orgidfinder.ParseError as e:
        print(str(e))
        continue
    except orgidfinder.FetchError as e:
        print(str(e))
        continue
    for org_info in org_infos:
        org_info['org_type'] = guide._org_types.get(org_info['org_type_code'])
        org_info['valid_org_id'] = True
        suggested_org_id = guide.get_suggested_id(org_info['org_id'])
        if suggested_org_id != org_info['org_id']:
            org_info['valid_org_id'] = False
            org_info['suggested_org_id'] = suggested_org_id
        org_info['updated_at'] = datetime.now().isoformat()
        scraperwiki.sqlite.save(key, org_info, 'organisations')

# remove old data
expr = ' FROM organisations WHERE updated_at < "{}"'.format(scrape_started_at)
results_to_remove = scraperwiki.sqlite.select('*' + expr)
for x in results_to_remove:
    print('Deleting expired data: {} ({})'.format(x['name'], x['org_id']))
_ = scraperwiki.sqlite.execute('DELETE' + expr)

scrape_finished_at = datetime.now().isoformat()
save_status(scrape_started_at, scrape_finished_at, True)
