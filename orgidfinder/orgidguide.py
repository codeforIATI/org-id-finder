import re

import requests


class InvalidIDError(Exception):
    pass


class OrgIDGuide():
    def __init__(self):
        self._request_cache = {}
        self._org_id_re = re.compile(r'([^-]+-[^-]+)-(.+)')
        self._dac_channel_code_re = re.compile(r'\d{5}')
        self._dac_donor_code_re = re.compile(r'([A-Z]{2})-(\d+)')

    def _cache(var_name):
        def __cache(fn):
            def ___cache(self):
                cached = self._request_cache.get(var_name)
                if cached:
                    return cached
                data = fn(self)
                self._request_cache[var_name] = data
                return data
            return ___cache
        return __cache

    @property
    @_cache('org_id_guide')
    def _org_id_guide(self):
        org_id_guide_url = 'http://org-id.guide/download.json'
        org_id_guide_data = requests.get(org_id_guide_url).json()['lists']
        return {x['code']: x for x in org_id_guide_data}

    @property
    @_cache('dac_channel_codes')
    def _dac_channel_codes(self):
        dac_channels_url = 'https://datahub.io/core/' + \
                           'dac-and-crs-code-lists/r/channel-codes.json'
        dac_channels_data = requests.get(dac_channels_url).json()
        return {x['code']: x for x in dac_channels_data}

    @property
    @_cache('dac_donor_codes')
    def _dac_donor_codes(self):
        dac_donors_url = 'https://datahub.io/core/' + \
                           'dac-and-crs-code-lists/r/dac-members.json'
        dac_donors_data = requests.get(dac_donors_url).json()
        return {x['name_en'].upper(): x for x in dac_donors_data}

    @property
    @_cache('country_codes')
    def _country_codes(self):
        country_codes_url = 'https://datahub.io/core/' + \
                      'country-codes/r/country-codes.json'
        country_codes_url_data = requests.get(country_codes_url).json()
        return {x['ISO3166-1-Alpha-2']: x for x in country_codes_url_data}

    @property
    @_cache('xi_iati_codes')
    def _xi_iati_codes(self):
        xi_iati_url = 'http://iatistandard.org/202/codelists/downloads/' + \
                      'clv2/json/en/IATIOrganisationIdentifier.json'
        xi_iati_data = requests.get(xi_iati_url).json()['data']
        return {x['code']: x for x in xi_iati_data}

    @property
    @_cache('org_types')
    def _org_types(self):
        org_type_url = 'http://iatistandard.org/202/codelists/downloads/' + \
                       'clv2/json/en/OrganisationType.json'
        org_type_data = requests.get(org_type_url).json()['data']
        return {x['code']: x for x in org_type_data}

    def lookup_prefix(self, prefix):
        return self._org_id_guide.get(prefix)

    def is_valid_prefix(self, prefix):
        return self.lookup_prefix(prefix) is not None

    def split_id(self, org_id):
        match = self._org_id_re.match(org_id)
        if not match:
            raise InvalidIDError()
        return match.groups()

    def is_valid_id(self, org_id):
        try:
            pref, suf = self.split_id(org_id)
        except InvalidIDError:
            return False
        return self.is_valid_prefix(pref)

    def get_suggested_id(self, org_id):
        if self.is_valid_id(org_id):
            return org_id

        try:
            # looks a bit like an org ID.
            # Try uppercasing
            pref, suf = self.split_id(org_id)
            if self.is_valid_prefix(pref.upper()):
                return '{pref}-{suf}'.format(pref=pref.upper(), suf=suf)
        except InvalidIDError:
            pass

        if self._dac_channel_code_re.match(org_id):
            # looks like a channel code
            if self._dac_channel_codes.get(org_id):
                return 'XM-DAC-{}'.format(org_id)

        dac_donor_code_match = self._dac_donor_code_re.match(org_id)
        if dac_donor_code_match:
            # looks like a donor code
            country_code, agency_code = dac_donor_code_match.groups()
            country = self._country_codes.get(country_code)
            if country:
                country_name = country['official_name_en'].upper()
                dac_donor = self._dac_donor_codes.get(country_name)
                if dac_donor:
                    return 'XM-DAC-{country}-{agency}'.format(
                        country=dac_donor['code'],
                        agency=agency_code,
                    )

        xi_iati_org_id = 'XI-IATI-{}'.format(org_id)
        if self._xi_iati_codes.get(xi_iati_org_id):
            # I mean this is pretty rare
            return xi_iati_org_id
