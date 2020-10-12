# -*- coding: utf-8 -*-

import base64
from odoo import http, _
from odoo.http import request
# from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.portal.controllers.portal import CustomerPortal as website_account

class website_account(website_account):

    def _prepare_portal_layout_values(self):
        values = super(website_account, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        joborder_count = request.env['project.task'].sudo().search_count([('job_partner_id','=', partner.id)])
        values.update({
            'joborder_count': joborder_count,
        })
        return values

    @http.route(['/page/job_workorder'], type='http', auth="public", website=True)
    def open_job_workorder(self, **post):
        return request.render("job_workorder_website_request.job_workorder")

    @http.route(['/job_order/workorder_submitted'], type='http', auth="public", methods=['POST'], website=True)
    def workorder_submitted(self, **post):
        vale = {
            'name': post.get('name'),
            'job_partner_name': post.get('your_name'),
            'job_partner_email': post.get('email'),
            'job_partner_phone': post.get('phone'),
            'description': post.get('description'),
            'priority': post.get('priority'),
        }
        if post.get('job_category') != 'Select category':
            vale.update({'job_category': post.get('job_category')})
        partner_id = request.env['res.partner'].sudo().search([('email', '=', post.get('email'))])
        if partner_id:
            vale.update({
                'job_partner_id': partner_id.id,
            })
        project_id = request.env['project.project'].sudo().search([('custom_code', '=', post.get('project_code'))], limit=1)
        if project_id:
            vale.update({
                'project_id': project_id.id,
            })
        workorder_id = request.env['project.task'].sudo().create(vale)
        local_context = http.request.env.context.copy()
        local_context.update({
            'partner_name':  post.get('your_name'),
            'email': post.get('email'),
            'subject': workorder_id.name,
            'job_number': workorder_id.job_number,
        })
        issue_template = http.request.env.ref('job_workorder_website_request.email_template_job_order')
        issue_template.sudo().with_context(local_context).send_mail(request.uid, force_send=False)
        attachment_list = request.httprequest.files.getlist('attachment')
        if workorder_id and attachment_list:
            for image in attachment_list:
                if post.get('attachment'):
                    attachments = {
                               'res_name': image.filename,
                               'res_model': 'project.task',
                               'res_id': workorder_id,
                               'datas': base64.encodestring(image.read()),
                               'type': 'binary',
                               'datas_fname': image.filename,
                               'name': image.filename,
                           }
                    attachment_obj = http.request.env['ir.attachment']
                    attach = attachment_obj.sudo().create(attachments)
        if len(attachment_list) > 0:
            group_msg = _('Customer has sent %s attachments to this joborder. Name of attachments are: ') % (len(attachment_list))
            for attach in attachment_list:
                group_msg = group_msg + '\n' + attach.filename
            group_msg = group_msg + '\n'  +  '. You can see top attachment menu to download attachments.'
            workorder_id.sudo().message_post(body=group_msg,message_type='comment')
        values = {
            'order':workorder_id
        }
        return request.render('job_workorder_website_request.thanks_mail_send', values)

    @http.route(['/my/joborders', '/my/joborders/page/<int:page>'], type='http', auth="user", website=True)
    def my_joborders(self, page=1, date_begin=None, date_end=None, joborder=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        pager = request.website.pager(
            url="/my/joborder",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=values['joborder_count'],
            page=page,
            step=self._items_per_page
        )
        domain = [('job_partner_id','=', partner.id)]
        job_order_ids = request.env['project.task'].sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'sortby': sortby,
            'job_orders': job_order_ids,
            'page_name': 'portal_joborder',
            'default_url': '/my/joborder',
            'pager': pager
        })
        return request.render("job_workorder_website_request.my_portal_job_order", values)
