import time

import requests
from lxml import etree

from . import orgidguide


ns = 'http://www.w3.org/XML/1998/namespace'


class FetchError(Exception):
    pass


class ParseError(Exception):
    pass


def fetch(url):
    print('Fetching: {}'.format(url))
    try:
        r = requests.get(url)
        time.sleep(0.5)
    except requests.exceptions.SSLError:
        r = requests.get(url, verify=False)
        time.sleep(0.5)
    return r


def fetch_org_datasets_from_registry():
    rows = 1000
    tmpl = 'https://iatiregistry.org/api/3/action/package_search?' + \
           'q=extras_filetype:organisation&start={{}}&rows={}'.format(rows)
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

    orgs = []
    for d in data:
        if len(d['resources']) == 0:
            continue
        orgs.append((d['name'], d['resources'][0]['url']))

    return orgs


def get_text(el, path, default_lang):
    text = {}
    narratives = el.xpath('{}/narrative'.format(path))
    if narratives != []:
        for narrative in narratives:
            lang = narrative.attrib.get('{{{}}}lang'.format(ns), default_lang)
            # this is a silly hack to prefer the first occurrence
            # of a string for a given language, rather than the last
            if lang not in text:
                text[lang] = narrative.text
    else:
        text[default_lang] = el.find(path).text
    return text


def parse_org(organisation):
    self_reported = True
    reporting_name = None
    reporting_org_id = None
    default_lang = organisation.attrib.get('{{{}}}lang'.format(ns), 'en')
    try:
        reporting_name = get_text(organisation, 'reporting-org', default_lang)
        reporting_org_id = organisation.find('reporting-org').get('ref')
    except:
        # no reporting org, so we have to assume this is
        # not self reported
        self_reported = False

    try:
        org_name = get_text(organisation, 'name', default_lang)
        try:
            # v1.0x
            org_id = organisation.find(
                'iati-identifier').text
        except AttributeError:
            # v2.0x
            org_id = organisation.find(
                'organisation-identifier').text
        if reporting_org_id and org_id != reporting_org_id:
            # reporting org ID and org ID don't match
            self_reported = False
    except AttributeError:
        # couldn't find an org name, so just use reporting-org
        if reporting_name and reporting_org_id:
            org_name = reporting_name
            org_id = reporting_org_id
        else:
            return []

    rows = []
    for lang, lang_name in org_name.items():
        rows.append({
            'lang': lang,
            'name': lang_name,
            'name_en': org_name.get('en', ''),
            'org_id': org_id,
            'self_reported': self_reported,
        })
    return rows


def parse_org_file(dataset_name, url):
    try:
        r = fetch(url)
    except requests.exceptions.ConnectionError:
        err = 'Error! Failed to fetch: {}'.format(url)
        raise FetchError(err)
    try:
        xml = etree.fromstring(r.content)
    except etree.XMLSyntaxError:
        err = 'Error! Failed to parse: {}'.format(url)
        raise ParseError(err)
    xpath = '//iati-organisation'
    organisations = xml.xpath(xpath)

    all_rows = []
    for organisation in organisations:
        rows = parse_org(organisation)
        for row in rows:
            row['source_url'] = url
            row['source_dataset'] = dataset_name
            all_rows.append(row)
    return all_rows


def setup_guide():
    '''
    Factory for OrgIDGuide
    '''
    return orgidguide.OrgIDGuide()
