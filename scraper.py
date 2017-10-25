from datetime import datetime
from os import environ
import time

import requests
from lxml import etree

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


rows = 1000
tmpl = 'https://iatiregistry.org/api/3/action/package_search?' + \
       'q=extras_filetype:organisation&start={{}}&rows={}'.format(rows)


def fetch(url):
    print('Fetching: {}'.format(url))
    r = requests.get(url)
    time.sleep(0.5)
    return r


page = 1
data = []
while True:
    start = (page - 1) * rows
    j = fetch(tmpl.format(start)).json()
    cur_data = j['result']['results']
    if cur_data == []:
        break
    data += cur_data
    page += 1


def get_text(el, path):
    text = {}
    ns = 'http://www.w3.org/XML/1998/namespace'
    narratives = el.xpath('{}/narrative'.format(path))
    if narratives != []:
        for narrative in narratives:
            lang = narrative.attrib.get('{{{}}}lang'.format(ns), 'en')
            text[lang] = narrative.text
    else:
        text['en'] = el.find(path).text
    return text


for r in data:
    if len(r['resources']) == 0:
        continue
    url = r['resources'][0]['url']
    dataset_name = r['name']
    r = fetch(url)
    try:
        xml = etree.fromstring(r.content)
    except:
        continue
    xpath = '//iati-organisation'
    organisations = xml.xpath(xpath)
    for organisation in organisations:
        try:
            name = get_text(organisation, 'name')
            try:
                code = organisation.find(
                    'iati-identifier').text
            except AttributeError:
                code = organisation.find(
                    'organisation-identifier').text
        except AttributeError:
            name = get_text(organisation, 'reporting-org')
            code = organisation.find('reporting-org').get('ref')
        for lang, lang_name in name.items():
            data = {
                'lang': lang,
                'name': lang_name,
                'name_en': name.get('en', '') if lang != 'en' else '',
                'code': code,
                'source_url': url,
                'source_dataset': dataset_name,
                'updated_at': datetime.now().isoformat(),
            }
            scraperwiki.sqlite.save(['code', 'lang'], data, 'organisations')
