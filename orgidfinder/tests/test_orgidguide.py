from unittest import TestCase, mock

from orgidfinder.orgidguide import OrgIDGuide


class TestOrgIDGuide(TestCase):
    def setUp(self):
        self.guide = OrgIDGuide()

    @mock.patch('orgidfinder.orgidguide.OrgIDGuide._org_id_guide',
                new_callable=mock.PropertyMock)
    def test_is_valid_prefix(self, mock):
        mock.return_value = {'GB-CHC': {}}
        result = self.guide.is_valid_prefix('GB-CHC')
        assert result is True

    @mock.patch('orgidfinder.orgidguide.OrgIDGuide._org_id_guide',
                new_callable=mock.PropertyMock)
    def test_is_invalid_prefix(self, mock):
        mock.return_value = {'GB-CHC': {}}
        result = self.guide.is_valid_prefix('XY-ZZZ')
        assert result is False
