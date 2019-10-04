# Copyright 2019 Mark Robinson (https://www.canzonia.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
import json
import urllib.parse
import urllib.request

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResCurrencyRateProviderBOC(models.Model):
    _inherit = 'res.currency.rate.provider'

    service = fields.Selection(
        selection_add=[('BOC', 'Bank of Canada')],
    )

    @api.multi
    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != 'BOC':
            return super()._get_supported_currencies()

        # List of currencies supported by Bank of Canada
        return \
            [
                'CAD', 'AUD', 'BRL', 'CNY', 'EUR', 'HKD', 'INR', 'JPY',
                'MYR', 'MXN', 'NZD', 'NOK', 'PEN', 'RUB', 'SAR', 'SGD',
                'ZAR', 'KRW', 'SEK', 'CHF', 'TWD', 'THB', 'TRY', 'GBP',
                'USD', 'VND'
            ]

    @api.multi
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != 'BOC':
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)

        if base_currency != 'CAD':
            raise UserError(_(
                'Bank of Canada is suitable only for companies '
                'with CAD as base currency!'
            ))

        content = defaultdict(dict)

        for cur in currencies:
            if cur == base_currency:
                continue

            fx_pair = "FX%(from)s%(to)s" % { 'from': base_currency, 'to': cur,}
            url = """https://www.bankofcanada.ca/valet/observations/%(fx_pair)s/json?start_date=%(date_from)s&end_date=%(date_to)s""" % {
                      'fx_pair': fx_pair,
                      'date_from': str(date_from),
                      'date_to': str(date_to),
                }

            data = json.loads(self._boc_provider_retrieve(url))

            if 'observations' not in data and data['message']:
                raise UserError(data['message'])

            if 'observations' in data:
                for obs in data['observations']:
                    date_content = content[obs['d']]
                    date_content[cur] = obs[fx_pair]['v']

        return content

    @api.multi
    def _boc_provider_retrieve(self, url):
        self.ensure_one()
        with self._boc_provider_urlopen(url) as response:
            content = response.read().decode(
                response.headers.get_content_charset()
            )
        return content

    @api.multi
    def _boc_provider_urlopen(self, url):
        self.ensure_one()

        parsed_url = urllib.parse.urlparse(url)
        parsed_query = urllib.parse.parse_qs(parsed_url.query)
        parsed_url = parsed_url._replace(query=urllib.parse.urlencode(
            parsed_query,
            doseq=True,
            quote_via=urllib.parse.quote,
        ))

        url = urllib.parse.urlunparse(parsed_url)

        request = urllib.request.Request(url)

        return urllib.request.urlopen(request)

