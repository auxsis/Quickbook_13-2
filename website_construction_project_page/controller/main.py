# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

PPG = 20
PPR = 4

class TableCompute(object):

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=PPG):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % PPR, pos // PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // PPR) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos // PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos // PPR) + y2][(pos % PPR) + x2] = False
            self.table[pos // PPR][pos % PPR] = {
                'category': p, 'x': x, 'y': y,
#                'class': " ".join(x.html_class for x in p.website_style_ids if x.html_class)
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos // PPR))
            index += 1

        # Format table according to HTML needs
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]

        return rows


class WebsiteProject(http.Controller):

    @http.route('/project', auth='public', website=True)
    def website_project(self, **kw):
        project_obj = request.env['project.project'].sudo()
        category_ids = request.env['project.category'].sudo().search([])
        project_count_dict = {}
        for category in category_ids:
            project_count = project_obj.search_count([('project_category_id','=',category.id)])
            project_count_dict.update({category.id:project_count})
        values = {
            'category_ids': category_ids,
            'bins': TableCompute().process(category_ids, PPG),
            'project_count':project_count_dict,
            'default_url': '/website_project',
        }
        return request.render('website_construction_project_page.project_categ', values)

    @http.route(['/project/category'], type='http', auth="public", website=True)
    def project_category(self, **kw):
        domain = []
        project_obj = request.env['project.project'].sudo()
        project_category_obj = request.env['project.category'].sudo()
        category_ids = project_category_obj.search([])
        values = {
                  'project_ids':project_obj,
                  'category_ids': category_ids,
        }
        if kw.get('search', False) and kw.get('category_id'):
            search = str(kw['search'])
            domain += [
                ('project_category_id', '=', int(kw.get("category_id"))),
                ('name', 'ilike', search),
            ]
            project_ids = project_obj.search(domain)
            values['project_ids'] = project_ids
        if kw.get("category_id"):
            domain += [('project_category_id', '=', int(kw.get("category_id")))]
            project_ids = project_obj.search(domain)
            values['project_ids'] = project_ids
            category_id = project_category_obj.browse(int(kw.get("category_id")))
            values.update({'currnet_category_id': category_id})
        values.update({'default_url': '/website_project',})
        return request.render('website_construction_project_page.project_categary', values)
    
    @http.route(['/project/details'], type='http', auth="public", website=True)
    def project_details(self, **kw):
        project_obj = request.env['project.project'].sudo()
        values = {
                  'project_id':project_obj,
                  'selection':'specification',
                  'bins': TableCompute().process(project_obj, PPG),
        }
        if kw.get("project_id"):
            project_id = project_obj.browse(int(kw.get("project_id")))
            values['project_id'] = project_id
            gallary_ids = project_id.project_gallary_ids
            values.update({'gallary_ids': gallary_ids})
            values['bins'] = TableCompute().process(gallary_ids, PPG)
        
        values.update({'default_url': '/website_project',})
        return request.render('website_construction_project_page.project_description_full', values)
        
    @http.route(['/project_nav_select'], type='http', auth="public", website=True)
    def project_nav_select(self, **kw):
        project_obj = request.env['project.project']
        values = {
                  'project_id':project_obj,
#                  'row':[1],
        }
        if kw.get("project_id"):
            project_id = project_obj.browse(int(kw.get("project_id")))
            values['project_id'] = project_id
        
        values.update({'default_url': '/website_project',})
        if kw.get("selection") and kw.get("selection") == 'features':
            values.update({'selection':'features'})
        elif kw.get("selection") and kw.get("selection") == 'specification':
            values.update({'selection':'specification'})
        elif kw.get("selection") and kw.get("selection") == 'gallary':
            values.update({'selection':'gallary'})
#            if values['project_id'] and values['project_id'].project_image_ids:
        elif kw.get("selection") and kw.get("selection") == 'brochure':
            values.update({'selection':'brochure'})
        elif kw.get("selection") and kw.get("selection") == 'floor_plan':
            values.update({'selection':'floor_plan'})
        elif kw.get("selection") and kw.get("selection") == 'location_plan':
            values.update({'selection':'location_plan'})
        return request.render('website_construction_project_page.project_description_full', values)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
