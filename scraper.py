from os import environ
from datetime import datetime

import orgidfinder

import iatikit
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_status(started_at, finished_at=None, success=False):
    doc_ref = db.collection('status').document(started_at)
    doc_ref.set({
        'started_at': started_at,
        'finished_at': finished_at,
        'success': success,
    })

scrape_started_at = datetime.now().isoformat()
save_status(scrape_started_at)

# iatikit.download.data()

key = ['org_id', 'lang', 'self_reported']
guide = orgidfinder.setup_guide()
org_ref = db.collection('organisations')

for dataset in iatikit.data().datasets.where(filetype='organisation'):
    org_infos = orgidfinder.parse_org_file(dataset)
    for org_info in org_infos:
        org_info['org_type'] = guide._org_types.get(org_info['org_type_code'])
        org_info['valid_org_id'] = True
        suggested_org_id = guide.get_suggested_id(org_info['org_id'])
        if suggested_org_id != org_info['org_id']:
            org_info['valid_org_id'] = False
            org_info['suggested_org_id'] = suggested_org_id
        org_info['updated_at'] = datetime.now().isoformat()

        org_ref.document('.'.join([
            str(org_info[k]) for k in key])).set(org_info)

# ###########################################
# # remove old data
# expr = ' FROM organisations WHERE updated_at < "{}"'.format(scrape_started_at)
# results_to_remove = scraperwiki.sqlite.select('*' + expr)
# for x in results_to_remove:
#     print('Deleting expired data: {} ({})'.format(x['name'], x['org_id']))
# _ = scraperwiki.sqlite.execute('DELETE' + expr)
# ###########################################

scrape_finished_at = datetime.now().isoformat()
save_status(scrape_started_at, scrape_finished_at, True)
