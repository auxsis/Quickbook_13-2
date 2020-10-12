# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict

import base64
from odoo import http, _
from odoo.http import request
from odoo import models,registry, SUPERUSER_ID
# from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager

from odoo.osv.expression import OR

class ConstructionIssue(http.Controller):

    @http.route(['/construction_contracting/ticket_submitted'], type='http', auth="public", methods=['POST'], website=True)
    def ticket_submitted(self, **post):
        
        cr, uid, context, pool = http.request.cr, http.request.uid, http.request.context, request.env
        Partner = request.env['res.partner'].sudo().search([('email', '=', post['email'])], limit=1)
        
        if Partner:
            team_obj = http.request.env['construction.team']
            team_match = team_obj.sudo().search([('is_team','=', True)], limit=1)
            construction_id = pool['construction.ticket'].sudo().create({
                                                            'subject': post['subject'],
                                                            'team_id' :team_match.id,
                                                            #'partner_id' :team_match.leader_id.id,
                                                            'user_id' :team_match.leader_id.id,
                                                            'team_leader_id': team_match.leader_id.id,
                                                            'email': post['email'],
                                                            'phone': post['phone'],
                                                            'category': post['category'],
                                                            'description': post['description'],
                                                            'priority': post['priority'],
                                                            'partner_id': Partner.id,
                                                             })
            
            values = {
                'construction_id':construction_id,
            }
            
            attachment_list = request.httprequest.files.getlist('attachment')
            for image in attachment_list:
                if post.get('attachment'):
                    attachments = {
                               'res_name': image.filename,
                               'res_model': 'construction.ticket',
                               'res_id': construction_id,
                               'datas': base64.encodestring(image.read()),
                               'type': 'binary',
                               'datas_fname': image.filename,
                               'name': image.filename,
                           }
                    attachment_obj = http.request.env['ir.attachment']
                    attach = attachment_obj.sudo().create(attachments)
            if len(attachment_list) > 0:
                group_msg = 'Customer has sent %s attachments to this Issue. Name of attachments are: ' % (len(attachment_list))
                for attach in attachment_list:
                    group_msg = group_msg + '\n' + attach.filename
                group_msg = group_msg + '\n'  +  '. You can see top attachment menu to download attachments.'
                construction_id.sudo().message_post(body=_(group_msg),message_type='comment')
                    
            return request.render('construction_contracting_issue_tracking.thanks_mail_send', values)
        else:
            return request.render('construction_contracting_issue_tracking.construction_mail_invalid',{})
       
    @http.route(['/website_helpdesk_support_ticket/invite'], auth='public', website=True, methods=['POST'])
    def index_user_invite(self, **kw):
        email = kw.get('email')
        name = kw.get('name')
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        user = request.env['res.users'].browse(request.uid)
        user_exist = request.env['res.users'].sudo().search([('login','=',str(email))])
        vals = {
                  'user_id':user_exist,
                }
        if user_exist:
            return http.request.render('website_helpdesk_support_ticket.user_alredy_exist', vals)
        value={
              'name': name,
              'email': email,
              'invitation_date':datetime.date.today(),
              'referrer_user_id':user.id,
              }
        user_info_id = self.create_history(value)
        base_url = http.request.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069') + '/page/website_helpdesk_support_ticket.user_thanks'
        url = "%s?user_info=%s" %(base_url, user_info_id.id)
        reject_url = http.request.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069') + '/page/website_helpdesk_support_ticket.user_thanks_reject'
        rejected_url = "%s?user_info=%s" %(reject_url, user_info_id.id)
        local_context = http.request.env.context.copy()
        issue_template = http.request.env.ref('website_helpdesk_support_ticket.email_template_helpdesk_ticket')
        local_context.update({'user_email': email, 'url': url, 'name':name,'rejected_url':rejected_url})
        issue_template.sudo().with_context(local_context).send_mail(request.uid, force_send=True)
       
    @http.route(['/construction_email/feedback/<int:ticket_id>'], type='http', auth='public', website=True)
    def feedback_email(self, ticket_id, **kw):
        values = {}
        values.update({'ticket_id': ticket_id})
        return request.render("construction_contracting_issue_tracking.construction_feedback", values) 
       
    @http.route(['/construction/feedback'],
                type='http', auth='public', website=True)
    def start_rating(self, **kw):
        partner_id = kw['partner_id']
        user_id = kw['ticket_id']
        ticket_obj = request.env['construction.ticket'].browse(int(user_id))
        #if partner_id == UserInput.partner_id.id:
        vals = {
              'rating':kw['star'],
              'comment':kw['comment'],
            }
        ticket_obj.sudo().write(vals)
        customer_msg = _(ticket_obj.partner_id.name + 'has send this feedback rating is %s and comment is %s') % (kw['star'],kw['comment'],)
        ticket_obj.sudo().message_post(body=customer_msg)
        return http.request.render("construction_contracting_issue_tracking.successful_construction_feedback")
            
# class website_account(website_account):

class CustomerPortal(CustomerPortal):
    
#     @http.route()
#     def account(self, **kw):
#         """ Add ticket documents to main account page """
#         response = super(CustomerPortal, self).account(**kw)
#         partner = request.env.user.partner_id
#         ticket = request.env['helpdesk.support']
#         ticket_count = ticket.sudo().search_count([
#         ('partner_id', 'child_of', [partner.commercial_partner_id.id])
#           ])
#         response.qcontext.update({
#         'ticket_count': ticket_count,
#         })
#         return response
    _items_per_page = 20

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ticket = request.env['construction.ticket']
        ticket_count = ticket.sudo().search_count([
        ('partner_id', 'child_of', [partner.commercial_partner_id.id])
          ])
        values.update({
            'construction_count': ticket_count,
        })
        return values
    
    
    @http.route(['/my/construction_tickets', '/my/construction_tickets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_ticket(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        construction_obj = http.request.env['construction.ticket']
        domain = [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id])
        ]
        # count for pager
        construction_count = construction_obj.sudo().search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/construction_tickets",
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
            'construction_tickets': tickets,
            'page_name': 'ticket',
            'pager': pager,
            'default_url': '/my/construction_tickets',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("construction_contracting_issue_tracking.display_construction_tickets", values)
       
    @http.route(['/my/construction_ticket/<model("construction.ticket"):ticket>'], type='http', auth="user", website=True)
    def my_ticket(self, ticket=None, **kw):
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
                                            author_id=construction_obj.partner_id.id
                                            )
            customer_msg = _('%s') % (kw.get('ticket_comment'))
            construction_obj.sudo().message_post(body=customer_msg,
                                            message_type='comment',
                                            subtype="mt_comment",
                                            author_id=construction_obj.partner_id.id)
            return http.request.render('construction_contracting_issue_tracking.successful_construction_ticket_send',{
            })
        if kw.get('ticket_comment'):
            customer_msg = _('%s') % (kw.get('ticket_comment'))
            construction_obj.sudo().message_post(body=customer_msg,
                                            message_type='comment',
                                            subtype="mt_comment",
                                            author_id=construction_obj.partner_id.id)
            return http.request.render('construction_contracting_issue_tracking.successful_construction_ticket_send',{
            })
        return request.render("construction_contracting_issue_tracking.display_construction_ticket", {'ticket': ticket, 'user': request.env.user})
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
