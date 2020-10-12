# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal, pager as portal_pager

from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):


    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        notes = request.env['note.note']
        notes_count = notes.sudo().search_count([
            ('user_id', 'child_of', [request.env.user.id]), ('is_task', '=', True)
        ])
        values.update({
        'notes_count': notes_count,
        })
        return values

    @http.route(['/my/notes', '/my/notes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_note(self, page=1,date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        response = super(CustomerPortal, self)
        values = self._prepare_portal_layout_values()
        notes = request.env['note.note']
        domain = [
            ('user_id', 'child_of', [request.env.user.id]), ('is_task', '=', True)
        ]

        # count for pager
        notes_count = notes.sudo().search_count(domain)

        # pager
        pager = portal_pager(
            url="/my/notes",
            total=notes_count,
            page=page,
            step=self._items_per_page
        )
        # sorting,searching
        searchbar_sortings = {
            'note': {'label': _('Order by Notes'), 'order': 'write_date desc'},
            'date': {'label': _('Order by Project'), 'order': 'project_id desc'},
            'name': {'label': _('Order by Task'), 'order': 'task_id desc'},
            'tag': {'label': _('Order by Tags'), 'order': 'tag_ids'},
            
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_inputs = {
            'note': {'input': 'note', 'label': _('Search in Notes')},
            'project_id': {'input': 'project_id', 'label': _('Search in Project')},
            'task_id': {'input': 'task_id', 'label': _('Search in Task')},
            'tag': {'input': 'tag', 'label': _('Search in Tags')},
        }

        # default sort by value
        
        if not sortby:
            sortby = 'note'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('note', 'all'):
                search_domain = OR([search_domain, [('memo', 'ilike', search)]])
            if search_in in ('project_id', 'all'):
                search_domain = OR([search_domain, [('project_id', 'ilike', search)]])
            if search_in in ('task_id', 'all'):
                search_domain = OR([search_domain, [('task_id', 'ilike', search)]])
            if search_in in ('tag', 'all'):
                search_domain = OR([search_domain, [('tag_ids', 'ilike', search)]])
            domain += search_domain

        # content according to pager and archive selected
        note_list = notes.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'notes': note_list,
            'page_name': 'notes',
            'pager': pager,
            'default_url': '/my/notes',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("project_notes_mobile_tablet.display_notes", values)

    @http.route(['/my/add_notes'], type='http', auth="user", website=True)
    def portal_add_note(self, page=1, date_begin=None, date_end=None, project=False, task=False, **kw):
        project_ids = request.env['project.project'].search([])
        task_ids = request.env['project.task'].search([('project_id', 'in', project_ids.ids)])
        values={
            'project_ids': project_ids,
            'projects':project,
            'task_ids':task_ids,
            'tasks': task,
        }
        return request.render("project_notes_mobile_tablet.add_new_notes", values)

    @http.route(['/my/create_new_note'], type='http', auth="user", website=True)
    def create_new_note(self, **kwargs):
        valse ={
            'user_id': request.env.user.id,
            'is_task': True,
        }
        if kwargs.get('project_id'):
            valse.update({'project_id': int(kwargs.get('project_id'))})
        if kwargs.get('task_id'):
            valse.update({'task_id': int(kwargs.get('task_id'))})
        if kwargs.get('content'):
            valse.update({'memo': kwargs.get('content')})
        request.env['note.note'].sudo().create(valse)
        return request.render("project_notes_mobile_tablet.user_thanks_note")

    @http.route(['/my/note/<int:note>'], type='http', auth="user", website=True)
    def edit_note(self, note=None, **kw):
        note = request.env['note.note'].sudo().browse(note)
        values={
            'note': note,
            
        }
        return request.render("project_notes_mobile_tablet.edit_note", values)

    @http.route(['/my/update_note'], type='http', auth="user", website=True)
    def update_note(self, **kwargs):
        valse = {}
        if kwargs.get('project_id'):
            valse.update({'project_id': int(kwargs.get('project_id'))})
        if kwargs.get('task_id'):
            valse.update({'task_id': int(kwargs.get('task_id'))})
        if kwargs.get('content'):
            valse.update({'memo': kwargs.get('content')})
        if kwargs.get('note_id'):
            note_id = request.env['note.note'].sudo().browse(int(kwargs.get('note_id')))
        if note_id:
            note_id.sudo().write(valse)
            return request.render("project_notes_mobile_tablet.update_successfully_note")

    @http.route(['/my/note/delete/<int:note>'], type='http', auth="user", website=True)
    def delete_note(self, note=None, **kw):
        note = request.env['note.note'].sudo().browse(note)
        try:
            note.sudo().unlink()
        except:
            return request.render("project_notes_mobile_tablet.not_allowed_note")
        return request.render("project_notes_mobile_tablet.delet_successfully_note")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
