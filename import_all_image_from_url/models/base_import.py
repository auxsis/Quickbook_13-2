from odoo import models,api
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import base64
import requests
from .local_file_adapter import LocalFileAdapter
import logging
_logger = logging.getLogger(__name__)

request_header = {
                "Accept-Language":"en-US,en;q=0.8",
                "User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36",
                "Connection":"keep-alive",
                }

class Import(models.TransientModel):

    _inherit = 'base_import.import'
    
    @api.multi
    def _parse_import_data(self, data, import_fields, options):
        all_fields = self.env[self.res_model].fields_get()
        for name, field in all_fields.items():
            if field['type'] in ('binary') and name in import_fields:
                index = import_fields.index(name)
                for line in data:
                    val = line[index]
                    if not val:
                        continue
                    parsed_url = urlparse(val)
                    if parsed_url.scheme:
                        try:
                            if parsed_url.scheme=='file':
                                requests_session = requests.session()
                                requests_session.mount('file://', LocalFileAdapter())
                                content = base64.b64encode(requests_session.get(val).content)
                                content= content.decode()
                            else:
                                content = base64.b64encode(requests.get(val,headers=request_header).content)
                                content= content.decode()
                        except Exception as e:
                            _logger.error(str(e))
                            content = ''
                            pass
                        line[index] = content

        data = super(Import,self)._parse_import_data(data, import_fields, options)
        return data

