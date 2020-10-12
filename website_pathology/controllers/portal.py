# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
import logging
_logger = logging.getLogger(__name__)

class PortalAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalAccount, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        my_testreq_count = request.env['patho.testrequest'].search_count([
            ('customer_id', '=', partner.id),
        ])
        values['my_testreq_count'] = my_testreq_count
        return values

    # ------------------------------------------------------------
    # My Pathology TestRequests
    # ------------------------------------------------------------

    def _patho_testrequests_check_access(self, patho_testreq_id, access_token=None):
        patho_testrequests = request.env['patho.testrequest'].browse([patho_testreq_id])
        patho_testrequests_sudo = patho_testrequests.sudo()
        try:
            patho_testrequests.check_access_rights('read')
            patho_testrequests.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(patho_testrequests_sudo.access_token, access_token):
                raise
        return patho_testrequests_sudo

    def _testrequests_get_page_view_values(self, patho_testrequest, access_token, **kwargs):
        values = {
            'page_name': 'patho_testreq_mgmt',
            'patho_testrequest': patho_testrequest,
        }
        if access_token:
            values['no_breadcrumbs'] = True
        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_patho_testrequests_history', [])
        values.update(get_records_pager(history, patho_testrequest))
        values.update(request.env['payment.acquirer']._get_available_payment_input(patho_testrequest.customer_id, patho_testrequest.customer_id.company_id))
        return values

    @http.route(['/my/testrequests', '/my/testrequests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_patho_testrequests(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PathoTestRequestsObj = request.env['patho.testrequest']

        domain = [
            ('customer_id', '=', partner.id),
        ]

        searchbar_sortings = {
            'create_date': {'label': _('Create Date'), 'order': 'create_date asc'},
            'test_date': {'label': _('Test Request Date'), 'order': 'test_date asc'},
            'name': {'label': _('Test Request Id'), 'order': 'name asc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'create_date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('patho.testrequest', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        testrequests_count = PathoTestRequestsObj.search_count(domain)

        # make pager
        pager = request.website.pager(
            url="/my/testrequests",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=testrequests_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        testrequests = PathoTestRequestsObj.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_testrequests_history'] = testrequests.ids[:100]

        values.update({
            'date': date_begin,
            'testreq_obj': testrequests.sudo(),
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/testrequests',
            'page_name': 'patho_testreq_mgmt',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_pathology.portal_my_testrequests", values)


    @http.route(['/my/testrequests/<int:testreq_id>'], type='http', auth="user", website=True)
    def portal_my_testrequests_detail(self, testreq_id=None, access_token=None, **kw):
        try:
            testrequests_sudo = self._patho_testrequests_check_access(testreq_id, access_token)
        except AccessError:
            return request.redirect('/my')
        values = self._testrequests_get_page_view_values(testrequests_sudo, access_token, **kw)
        return request.render("website_pathology.portal_my_testrequests_page", values)


    @http.route(['/my/testrequests/pdf/<int:testreq_id>'], type='http', auth="public", website=True)
    def portal_my_testreq_report(self, testreq_id, access_token=None, **kw):
        try:
            testrequests_sudo = self._patho_testrequests_check_access(testreq_id, access_token)
        except AccessError:
            return request.redirect('/my')

        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('wk_pathology_management.patho_mgmt_testreq_report').sudo().render_qweb_pdf([testrequests_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/testrequests/report/pdf/<int:testreq_id>'], type='http', auth="public", website=True)
    def portal_my_patient_report(self, testreq_id, access_token=None, **kw):
        test = request.env['patho.testrequest'].browse([testreq_id])
        if not test.exists():
            return request.render('website.404')
        try:
            testrequests_sudo = self._patho_testrequests_check_access(testreq_id, access_token)
        except AccessError:
            return request.redirect('/my')

        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('wk_pathology_management.patho_mgmt_patient_report').sudo().render_qweb_pdf([testrequests_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
