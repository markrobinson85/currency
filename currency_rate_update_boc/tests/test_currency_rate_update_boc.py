# Copyright 2019 Mark Robinson (https://www.canzonia.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta
from io import StringIO
from unittest import mock

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common

_module_ns = 'odoo.addons.currency_rate_update_boc'
_provider_class = (
    _module_ns
    + '.models.res_currency_rate_provider_boc'
    + '.ResCurrencyRateProviderBOC'
)


class TestResCurrencyRateProviderBOC(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.Company = self.env['res.company']
        self.CurrencyRate = self.env['res.currency.rate']
        self.CurrencyRateProvider = self.env['res.currency.rate.provider']

        self.today = fields.Date.today()
        self.eur_currency = self.env.ref('base.EUR')
        self.boc_provider = self.CurrencyRateProvider.create({
            'service': 'BOC',
            'currency_ids': [
                (4, self.eur_currency.id),
            ],
        })
        self.CurrencyRate.search([]).unlink()

    def test_update(self):
        date = self.today - relativedelta(days=1)
        mocked_response = (
            """
{
    "terms": {
        "url": "https://www.bankofcanada.ca/terms/"
    },
    "seriesDetail": {
        "FXCADEUR": {
            "label": "CAD/EUR",
            "description": "Canadian dollar to European euro daily exchange rate",
            "dimension": {
                "key": "d",
                "name": "date"
            }
        }
    },
    "observations": [
        {
            "d": "%(date)s",
            "FXCADEUR": {
                "v": "0.6870"
            }
        }
    ]
}""" % {
                'date': str(date),
            })
        with mock.patch(
            _provider_class + '._boc_provider_urlopen',
            return_value=StringIO(mocked_response),
        ):
            self.boc_provider._update(date, date)

        rates = self.CurrencyRate.search([
            ('currency_id', '=', self.eur_currency.id),
        ], limit=1)
        self.assertTrue(rates)

        self.CurrencyRate.search([
            ('currency_id', '=', self.eur_currency.id),
        ]).unlink()

