# -*- coding: utf-8 -*-

import base64
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager

class RequestInformation(http.Controller):

    @http.route(['/request_submited'], type='http', auth="public", methods=['POST'], website=True)
    def request_information_submitted(self, **post):
        cr, uid, context, pool = http.request.cr, http.request.uid, http.request.context, request.env
        Partner = request.env['res.partner'].sudo().search([('email', '=', post['email'])], limit=1)
        print('===============================dddddddddddddddddd==================')
        if Partner:
            team_obj = http.request.env['request.information.team']
            team_match = team_obj.sudo().search([('is_team','=', True)], limit=1)
            request_information = pool['request.information'].sudo().create({
                'subject': post['subject'],
                'team_id' :team_match.id,
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
                'request_information':request_information
            }

            attachment_list = request.httprequest.files.getlist('attachment')
            for image in attachment_list:
                if post.get('attachment'):
                    attachments = {
                               'res_name': image.filename,
                               'res_model': 'request.information',
                               'res_id': request_information,
                               'datas': base64.encodestring(image.read()),
                               'type': 'binary',
                               'datas_fname': image.filename,
                               'name': image.filename,
                           }
                    attachment_obj = http.request.env['ir.attachment']
                    attach = attachment_obj.sudo().create(attachments)
            if len(attachment_list) > 0:
                group_msg = 'Customer has sent %s attachments to this Request Information. Name of attachments are: ' % (len(attachment_list))
                for attach in attachment_list:
                    group_msg = group_msg + '\n' + attach.filename
                group_msg = group_msg + '\n'  +  '. You can see top attachment menu to download attachments.'
                request_information.sudo().message_post(body=_(group_msg),message_type='comment')
                    
            return request.render('project_request_for_information.thanks_mail_send', values)
        else:
            return request.render('project_request_for_information.support_invalid',{})

    @http.route(['/request_information_email/feedback/<int:order_id>'], type='http', auth='public', website=True)
    def feedback_email(self, order_id, **kw):
        values = {}
        values.update({'request_information_id': order_id})
        return request.render("project_request_for_information.request_information_feedback", values) 
       
    @http.route(['/request/feedback/success'],
                type='http', auth='public', website=True)
    def start_rating(self, **kw):
        partner_id = kw['partner_id']
        kw_request_information = kw['request_information_id']
        request_information_id = request.env['request.information'].browse(int(kw_request_information))

        vals = {
              'rating':kw['star'],
              'comment':kw['comment'],
            }

        request_information_id.sudo().write(vals)
        customer_msg = _(request_information_id.partner_id.name + 'has send this feedback rating is %s and comment is %s') % (kw['star'],kw['comment'],)
        request_information_id.sudo().message_post(body=customer_msg)
        return http.request.render("project_request_for_information.successful_feedback")

class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        request_information = request.env['request.information']
        request_information_count = request_information.sudo().search_count([
        ('partner_id', 'child_of', [partner.commercial_partner_id.id])
          ])
        values.update({
            'request_information_count': request_information_count,
        })
        return values

    @http.route(['/my/request_informations', '/my/request_informations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_request(self, page=1, **kw):
        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        support_obj = http.request.env['request.information']
        domain = [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id])
        ]
        request_informations_count = support_obj.sudo().search_count(domain)
        pager = request.website.pager(
            url="/my/request_informations",
            total=request_informations_count,
            page=page,
            step=self._items_per_page
        )
        request_informations = support_obj.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'request_informations': request_informations,
            'page_name': 'Project Requests',
            'pager': pager,
            'default_url': '/my/request_informations',
        })
        return request.render("project_request_for_information.display_request_informations", values)

    @http.route(['/my/request_information/<model("request.information"):request_information>'], type='http', auth="user", website=True)
    def my_ticket(self, request_information=None, **kw):
        attachment_list = request.httprequest.files.getlist('attachment')
        request_informations_obj = http.request.env['request.information'].sudo().browse(request_information.id)
        for image in attachment_list:
            if kw.get('attachment'):
                attachments = {
                           'res_name': image.filename,
                           'res_model': 'request.information',
                           'res_id': request_information.id,
                           'datas': base64.encodestring(image.read()),
                           'type': 'binary',
                           'datas_fname': image.filename,
                           'name': image.filename,
                       }
                attachment_obj = http.request.env['ir.attachment']
                attachment_obj.sudo().create(attachments)
        if len(attachment_list) > 0:
            group_msg = 'Customer has sent %s attachments to this Request Information. Name of attachments are: ' % (len(attachment_list))
            for attach in attachment_list:
                group_msg = group_msg + '\n' + attach.filename
            group_msg = group_msg + '\n'  +  '. You can see top attachment menu to download attachments.'
            request_informations_obj.sudo().message_post(body=_(group_msg),
                                            message_type='comment',
                                            subtype="mt_comment",
                                            author_id=request_informations_obj.partner_id.id
                                            )
            customer_msg = _('%s') % (kw.get('ticket_comment'))
            request_informations_obj.sudo().message_post(body=customer_msg,
                                            message_type='comment',
                                            subtype="mt_comment",
                                            author_id=request_informations_obj.partner_id.id)
            return http.request.render('project_request_for_information.successful_ticket_send',{
            })
        if kw.get('ticket_comment'):
            customer_msg = _('%s') % (kw.get('ticket_comment'))
            request_informations_obj.sudo().message_post(body=customer_msg,
                                            message_type='comment',
                                            subtype="mt_comment",
                                            author_id=request_informations_obj.partner_id.id)
            return http.request.render('project_request_for_information.successful_ticket_send',{
            })
        return request.render("project_request_for_information.display_request_information", {'request_information': request_information, 'user': request.env.user})
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
