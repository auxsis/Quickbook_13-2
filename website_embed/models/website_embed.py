# © 2018 Nedas Žilinskas <nedas.zilinskas@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
try:
    from ..tools.sanitize import html_sanitize
except (ImportError, IOError) as err:
    pass


class WebsiteEmbed(models.Model):

    _name = 'website.embed'
    _description = 'Embed HTML Templates'

    name = fields.Char(
        required=True,
    )

    html_text = fields.Text(
        string="HTML",
        required=True,
        compute='_compute_html_text',
        inverse='_inverse_html_text',
    )

    html = fields.Html(
        string="HTML",
        sanitize=False,
    )

    @api.multi
    def _compute_html_text(self):
        for rec in self:
            rec.html_text = rec.html

    @api.multi
    def _inverse_html_text(self):
        for rec in self:
            rec.html = html_sanitize(rec.html_text)
