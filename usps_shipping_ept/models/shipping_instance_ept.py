# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api,_

class ShippingInstanceEpt(models.Model):
    _inherit = "shipping.instance.ept"
    provider = fields.Selection(selection_add=[('usps_ept', 'USPS')])
    
    usps_userid = fields.Char("USPS UserId",copy=False)
    _sql_constraints = [('user_unique', 'unique(usps_userid)', 'User already exists.')]
 
    # @api.model
    # def get_usps_api_object(self,environment):
    #     api = USPS_API(environment, timeout=500)
    #     return api
    
    @api.one
    def usps_ept_retrive_shipping_services(self,to_add):
        """ Retrive shipping services from the USPS
            @param:
            @return: list of dictionaries with shipping service
            @author: Jigar Vagadiya on dated 27-May-2017
        """
        services_name={'First Class':'First Class',
                'Priority':'Priority',
                'Express':'Express',
                'PRIORITY EXPRESS': 'PRIORITY EXPRESS',
                'PARCEL SELECT GROUND': 'PARCEL SELECT GROUND',
                'LIBRARY': 'LIBRARY',
                'MEDIA': 'MEDIA',
                'BPM': 'BPM',
                'PRIORITY MAIL CUBIC': 'PRIORITY MAIL CUBIC'}
        
        shipping_services_obj = self.env['shipping.services.ept']
        services = shipping_services_obj.search([('shipping_instance_id','=',self.id)])
        services.unlink()
        
        #Display Services 
        for company in self.company_ids:
            for service in services_name:
                global_code_condition=self.env['shipping.services.ept'].search([('service_code','=',service),('shipping_instance_id','=',self.id)])
                if global_code_condition:
                    if self.env['shipping.services.ept'].search([('company_ids','=',company.id) , ('service_code','=',service),('shipping_instance_id','=',self.id)]):
                        return
                    else:
                        global_code_condition.write({'company_ids':[(4,company.id)]})
                else:
                    vals = {'shipping_instance_id': self.id,'service_code':service, 'service_name':service,'company_ids':[(4,company.id)]}
                    self.env['shipping.services.ept'].create(vals)
                
                   
    @api.model
    def usps_ept_quick_add_shipping_services(self, service_type,service_name):
        """ Allow you to get the default shipping services value while creating quick 
            record from the Shipping Service for USPS
            @param service_type: Service type of USPS
            @return: dict of default value set
            @author: Jigar Vagadiya on dated 27-may-2017
        """
        return {'default_usps_service_type':service_type,
                'default_name':service_name}
