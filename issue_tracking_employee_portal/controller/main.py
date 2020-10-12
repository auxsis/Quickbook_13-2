# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict

import base64

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo.osv.expression import OR

class CustomerPortal(CustomerPortal):
    _items_per_page = 20

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ticket = request.env['construction.ticket']
        issue_count = ticket.sudo().search_count([
        ('user_id', '=', request.env.user.id)
          ])
        values.update({
            'issue_count': issue_count,
        })
        return values

    @http.route(['/your/issue_tickets', '/your/issue_tickets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_your_ticket(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        construction_obj = http.request.env['construction.ticket']
        domain = [
            ('user_id', '=', request.env.user.id)
        ]
        # count for pager
        construction_count = construction_obj.sudo().search_count(domain)
        # pager
        pager = request.website.pager(
            url="/your/issue_tickets",
            total=construction_count,
            page=page,
            step=self._items_per_page
        )
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'subject'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_inputs = {
            'title': {'input': 'title', 'label': _('Search <span class="nolabel"> (in Title)</span>')},
            'issue_no': {'input': 'issue_no', 'label': _('Search in Issue Number')},
            'date': {'input': 'request_date', 'label': _('Search in date')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('project.task', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('title', 'all'):
                search_domain = OR([search_domain, [('subject', 'ilike', search)]])
            if search_in in ('issue_no', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('request_date', 'all'):
                search_domain = OR([search_domain, [('request_date', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        # content according to pager and archive selected
        tickets = construction_obj.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'issue_tickets': tickets,
            'page_name': 'issue',
            'pager': pager,
            'default_url': '/your/issue_tickets',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("issue_tracking_employee_portal.display_issue_tickets", values)
    
    @http.route(['/your/issue_ticket/<model("construction.ticket"):ticket>'], type='http', auth="user", website=True)
    def your_ticket(self, ticket=None, **kw):
        attachment_list = request.httprequest.files.getlist('attachment')
        construction_obj = http.request.env['construction.ticket'].sudo().browse(ticket.id)
        for image in attachment_list:
            if kw.get('attachment'):
                attachments = {
                           'res_name': image.filename,
                           'res_model': 'construction.ticket',
                           'res_id': ticket.id,
                           'datas': base64.encodestring(image.read()),
                           'type': 'binary',
                           'datas_fname': image.filename,
                           'name': image.filename,
                       }
                attachment_obj = http.request.env['ir.attachment']
                attachment_obj.sudo().create(attachments)
                if len(attachment_list) > 0:
                    group_msg = 'Customer has sent %s attachments to this Construction ticket. Name of attachments are: ' % (len(attachment_list))
                    for attach in attachment_list:
                        group_msg = group_msg + '\n' + attach.filename
                    group_msg = group_msg + '\n'  +  '. You can see top attachment menu to download attachments.'
                    construction_obj.sudo().message_post(body=_(group_msg),
                                                    message_type='comment',
                                                    subtype="mt_comment",
                                                    author_id=request.env.user.partner_id.id
                                                    )
                    customer_msg = _('%s') % (kw.get('ticket_comment'))
                    construction_obj.sudo().message_post(body=customer_msg,
                                                    message_type='comment',
                                                    subtype="mt_comment",
                                                    author_id=request.env.user.partner_id.id)
                    return http.request.render('construction_contracting_issue_tracking.successful_construction_ticket_send',{
                    })

            if kw.get('ticket_comment'):
                customer_msg = _('%s') % (kw.get('ticket_comment'))
                construction_obj.sudo().message_post(body=customer_msg,
                                                message_type='comment',
                                                subtype="mt_comment",
                                                author_id=request.env.user.partner_id.id)
                return http.request.render('construction_contracting_issue_tracking.successful_construction_ticket_send',{
                })
        return request.render("issue_tracking_employee_portal.display_issue_ticket", {'issue': ticket, 'user': request.env.user})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
