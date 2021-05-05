from . import orgidguide


ns = 'http://www.w3.org/XML/1998/namespace'


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
    default_lang = organisation.etree.attrib.get('{{{}}}lang'.format(ns), 'en')
    try:
        reporting_name = get_text(organisation.etree, 'reporting-org', default_lang)
        reporting_org_id = organisation.etree.find('reporting-org').get('ref')
        org_type_code = organisation.etree.find('reporting-org').get('type')
    except:
        # no reporting org, so we have to assume this is
        # not self reported
        self_reported = False

    try:
        org_name = get_text(organisation.etree, 'name', default_lang)
        org_id = organisation.id
        if not reporting_org_id:
            org_type_code = None
            self_reported = False
        elif org_id != reporting_org_id:
            # reporting org ID and org ID don't match
            org_type_code = None
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
            'org_type_code': org_type_code,
            'self_reported': self_reported,
        })
    return rows


def parse_org_file(dataset):
    all_rows = []
    for organisation in dataset.organisations:
        rows = parse_org(organisation)
        for row in rows:
            row['source_url'] = dataset.metadata['resources'][0]['url']
            row['source_dataset'] = dataset.name
            all_rows.append(row)
    return all_rows


def setup_guide():
    '''
    Factory for OrgIDGuide
    '''
    return orgidguide.OrgIDGuide()
