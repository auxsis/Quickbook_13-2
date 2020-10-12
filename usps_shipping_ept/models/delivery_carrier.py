    # Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import binascii
import re
from datetime import datetime
import math
from math import ceil
import requests
from odoo.addons.usps_shipping_ept.usps_api.usps_response import Response
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning, ValidationError, UserError
import xml.etree.ElementTree as etree
import logging
_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"
    delivery_type = fields.Selection(selection_add=[("usps_ept", "USPS")])

    usps_service_type = fields.Selection([('First Class', 'First Class'),
                                          ('Priority', 'Priority'),
                                          ('Express', 'Express'),
                                          ('PRIORITY EXPRESS', 'PRIORITY EXPRESS'),
                                          ('PARCEL SELECT GROUND', 'PARCEL SELECT GROUND'),
                                          ('LIBRARY', 'LIBRARY'),
                                          ('MEDIA', 'MEDIA'),
                                          ('BPM', 'BPM'),
                                          ('PRIORITY MAIL CUBIC', 'PRIORITY MAIL CUBIC'),], string="Service Type",
                                         help="Shipping Services those are accepted by USPS")
    usps_delivery_nature = fields.Selection([('domestic', 'Domestic'),
                                             ('international', 'International')],
                                            string="Delivery Nature", default='domestic',
                                            help="In delivery nature Domestic indicates the shipment is not outside the country and International indicates the shipment is outside the country.")
    #     usps_container = fields.Selection([('Flat Rate Envelope', 'Flat Rate Envelope'),
    #                                         ('Sm Flat Rate Envelope', 'Small Flat Rate Envelope'),
    #                                         ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
    #                                         ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
    #                                         ('Flat Rate Box', 'Flat Rate Box'),
    #                                         ('Sm Flat Rate Box', 'Small Flat Rate Box'),
    #                                         ('Lg Flat Rate Box', 'Large Flat Rate Box'),
    #                                         ('Md Flat Rate Box', 'Medium Flat Rate Box')],
    #                                        string="Type of USPS regular container", default="Flat Rate Envelope",help="specify special containers or container attributes that may affect postage.")
    usps_content_type = fields.Selection([('SAMPLE', 'Sample'),
                                          ('GIFT', 'Gift'),
                                          ('DOCUMENTS', 'Documents'),
                                          ('RETURN', 'Return'),
                                          ('MERCHANDISE', 'Merchandise')],
                                         default='MERCHANDISE', string="Content Type",
                                         help="Specifies the content of the package or envelope.")
    # help="It indicates the package dimensions. REGULAR means Package dimensions are 12 or less and LARGE means Any package dimension is larger than 12.
    usps_container_size = fields.Selection([('LARGE', 'Large'),
                                            ('REGULAR', 'Regular')], default='REGULAR', store=True,
                                           compute='_compute_size_container')
    usps_evsapi_use = fields.Boolean("Want to use USPS eVS API?",default=False)

    @api.one
    @api.depends('usps_container')
    def _compute_size_container(self):
        if self.usps_container == 'VARIABLE':
            self.usps_container_size = 'REGULAR'
        else:
            self.usps_container_size = 'LARGE'

    usps_container = fields.Selection([('VARIABLE', 'Regular < 12 inch(VARIABLE)'),
                                       ('RECTANGULAR', 'Rectangular'),
                                       ('NONRECTANGULAR', 'Non-rectangular'),
                                       ('FLAT RATE ENVELOPE', 'FLAT RATE ENVELOPE'),
                                       ('LEGAL FLAT RATE ENVELOPE', 'LEGAL FLAT RATE ENVELOPE'),
                                       ('PADDED FLAT RATE ENVELOPE', 'PADDED FLAT RATE ENVELOPE'),
                                       ('GIFT CARD FLAT RATE ENVELOPE', 'GIFT CARD FLAT RATE ENVELOPE'),
                                       ('SM FLAT RATE ENVELOPE', 'SM FLAT RATE ENVELOPE'),
                                       ('WINDOW FLAT RATE ENVELOPE', 'WINDOW FLAT RATE ENVELOPE'),
                                       ('SM FLAT RATE BOX', 'SM FLAT RATE BOX'),
                                       ('MD FLAT RATE BOX', 'MD FLAT RATE BOX'),
                                       ('LG FLAT RATE BOX', 'LG FLAT RATE BOX'),
                                       ('REGIONALRATEBOXA', 'REGIONALRATEBOXA'),
                                       ('REGIONALRATEBOXB', 'REGIONALRATEBOXB'),
                                       ('PACKAGE SERVICE', 'PACKAGE SERVICE'),
                                       ('CUBIC PARCELS', 'CUBIC PARCELS'),
                                       ('CUBIC SOFT PACK', 'CUBIC SOFT PACK'),
                                       ], default='VARIABLE', string="Container",
                                      help="specify special containers or container attributes that may affect postage.")

    usps_default_product_packaging_id = fields.Many2one('product.packaging', string="Package Type")

    usps_machinable = fields.Boolean(string="Machinable",
                                     help="Please check on USPS website to ensure that your package is machinable.")

    usps_firstclass_mail_type = fields.Selection([('LETTER', 'Letter'),
                                                  ('FLAT', 'Flat'),
                                                  ('PARCEL', 'Parcel'),
                                                  ('POSTCARD', 'Postcard'),
                                                  ('PACKAGE SERVICE', 'Package Service')],
                                                 string="USPS First Class Mail Type", default="LETTER",
                                                 help="The First Class MailType is returned only if the ServiceType is First Class.")
    usps_mail_type = fields.Selection([('Package', 'Package'),
                                       ('Envelope', 'Envelope'),
                                       ('Letter', 'Letter'),
                                       ('LargeEnvelope', 'Large Envelope'),
                                       ('FlatRate', 'Flat Rate'),
                                       ('FlatRateBox', 'Flat Rate Box')], default="FlatRateBox",
                                      string="USPS Mail Type",
                                      help="USPS mail type indicates the type of shipment package.")
    usps_label_type = fields.Selection([('PDF', 'PDF'),
                                        ('TIF', 'TIF')],
                                       string="USPS Label Type", default='PDF',
                                       help="Specifies the type of lable formate.")
    usps_label_size = fields.Selection([('BARCODE ONLY','BARCODE ONLY'),
                                        ('CROP','CROP'),
                                        ('4X6LABEL','4X6LABEL'),
                                        ('4X6LABELL','4X6LABELL'),
                                        ('6X4LABEL','6X4LABEL'),
                                        ('4X6LABELP','4X6LABELP'),
                                        ('4X6LABELP PAGE','4X6LABELP PAGE'),
                                        ('SEPARATECONTINUEPAGE','SEPARATECONTINUEPAGE'),
                                        ('4X6LABELZPL','4X6LABELZPL')],string="USPS Lable Size",default='4X6LABEL',help="Specifies the type of lable formate.")

    @api.multi
    def deside_rate_api(self):
        """Deside the which rate API will be used in the USPS request.
            @param: none
            @return: Rate API name and desided API. 
            @author: Jigar v vagadiya on 25 AUG 2017."""
        return "RateV4" if self.usps_delivery_nature == 'domestic' else "IntlRateV2"

    @api.multi
    def deside_conform_api(self):
        """Deside the which API will be used in the USPS request.
            @param: none
            @return: API name and desided API. 
            @author: Jigar v vagadiya on 27 June 2017."""
        if not self.prod_environment:
            if self.usps_evsapi_use:
                if self.usps_delivery_nature == 'domestic':
                    api='eVSCertify'
                else:
                    raise Warning("Currently International shipping is not provided.")
            else:
                if self.usps_delivery_nature == 'domestic':
                    if self.usps_service_type == 'Express':
                        api = 'ExpressMailLabelCertify'
                    else:
                        api = 'DelivConfirmCertifyV4'
                else:
                    api = "%s%s" % (str(self.usps_service_type).replace(" ", ""), 'MailIntlCertify')
        else:
            if self.usps_evsapi_use:
                if self.usps_delivery_nature == 'domestic':
                    api='eVS'
                else:
                    raise Warning("Currently International shipping is not provided.")
            else:
                if self.usps_delivery_nature == 'domestic':
                    if self.usps_service_type == 'Express':
                        api = 'ExpressMailLabel'
                    else:
                        api = 'DeliveryConfirmationV4'
                else:
                    api = "%s%s" % (str(self.usps_service_type).replace(" ", ""), 'MailIntl')
        return api

    @api.multi
    def check_error_response(self, results):
        """Check the API response is valide or not from USPS.
            @param: results
            @return: Check API response.
            @author: Jigar v vagadiya on 28 AUG 2017."""
        res = {'ShippingCharge': 0.0, 'CurrencyCode': False, 'error_message': False}
        international_rate = results.get('IntlRateV2Response', {}).get('Package', {}).get('Error', {})
        if international_rate:
            error_number = international_rate.get('Number')
            error_discription = international_rate.get('Description')
            error_msg = "Error Code : %s - %s" % (error_number, error_discription)
            res['error_message'] = error_msg
            return res
        domestic_rate = results.get('RateV4Response', {}).get('Package', {}).get('Error', {})
        if domestic_rate:
            error_number = domestic_rate.get('Number')
            error_discription = domestic_rate.get('Description')
            error_msg = "Error Code : %s - %s" % (error_number, error_discription)
            res['error_message'] = error_msg
            return res
        lable_error_msg = results.get('Error', {})
        if lable_error_msg:
            error_number = lable_error_msg.get('Number')
            error_discription = lable_error_msg.get('Description')
            error_msg = "Error Code : %s - %s" % (error_number, error_discription)
            raise Warning(error_msg)

    @api.multi
    def call_api(self, api_name, xml_data):
        """Call the rate API from USPS. These method used to calling rate API.
            @param: API name and XML data.
            @return: API response(Give API response.) 
            @author: Jigar v vagadiya on 27 June 2017."""
        if not self.prod_environment:
            url = 'http://testing.shippingapis.com/ShippingAPI.dll?'
        else:
            url = 'http://production.shippingapis.com/ShippingAPI.dll?'
        data1 = {'API': api_name,
                 'xml': xml_data}
        _logger.info("Request Data : %s"%(data1))
        try:
            response_text = requests.post(url=url, data=data1)
            api = Response(response_text)
            result = api.dict()
            _logger.info("Response Data : %s"%(result))
        except Exception as e:
            raise Warning(e)
        return result

    @api.multi
    def call_lable_api(self, api_name, xml_data):
        """Call the API from USPS. These method used to calling label genrating API in USPS. Also use this method for cancel request calling.
            @param: API name and xml data.
            @return: API response(Give API response.) 
            @author: Jigar v vagadiya on 27 June 2017."""
        url = 'https://secure.shippingapis.com/ShippingAPI.dll?'
        data1 = {'API': api_name,
                 'xml': xml_data}
        _logger.info("Request Data : %s"%(data1))
        try:
            response_text = requests.post(url=url, data=data1)
            api = Response(response_text)
            result = api.dict()
            _logger.info("Response Data : %s"%(result))
        except Exception as e:
            raise Warning(e)
        return result

    @api.multi
    def usps_get_shipping_rate(self, shipper_address, recipient_address, total_weight, picking_bulk_weight,
                               packages=False, declared_value=False, \
                               declared_currency=False, ounces=False):
        """ Retrive shipping Rate using this services from the USPS
            @param:
            @return: request parameter 
            @author: Jigar v vagadiya on 26 AUG 2017.
        """
        res = {'ShippingCharge': 0.0, 'CurrencyCode': False, 'error_message': False}
        # built request data
        api_name = self.deside_rate_api()
        #         environment=self.prod_environment
        #         api = self.shipping_instance_id.get_usps_api_object(environment)

        if self.usps_delivery_nature == 'domestic':
            service_root = etree.Element("RateV4Request")
        else:
            service_root = etree.Element("IntlRateV2Request")

        service_root.attrib['USERID'] = "%s" % (self.shipping_instance_id and self.shipping_instance_id.usps_userid)
        etree.SubElement(service_root, "Revision").text = "2"
        package_node = etree.SubElement(service_root, "Package")
        package_node.attrib['ID'] = "PKG1"

        if self.usps_delivery_nature == 'domestic':
            etree.SubElement(package_node, "Service").text = "%s" % (self.usps_service_type or "")

            if self.usps_service_type == "First Class":
                etree.SubElement(package_node, "FirstClassMailType").text = "%s" % (self.usps_firstclass_mail_type)

            etree.SubElement(package_node, "ZipOrigination").text = "%s" % (shipper_address.zip)
            etree.SubElement(package_node, "ZipDestination").text = "%s" % (recipient_address.zip)

        etree.SubElement(package_node, "Pounds").text = "%s" % (int(math.floor(total_weight)))
        etree.SubElement(package_node, "Ounces").text = "%s" % (ounces)

        if self.usps_delivery_nature == 'international':
            etree.SubElement(package_node, "Machinable").text = "%s" % (self.usps_machinable)
            etree.SubElement(package_node, "MailType").text = "%s" % (self.usps_mail_type)
            etree.SubElement(package_node, "ValueOfContents").text = "%s" % (declared_value)
            etree.SubElement(package_node, "Country").text = "%s" % (
            recipient_address.country_id and recipient_address.country_id.name)

        etree.SubElement(package_node, "Container").text = "%s" % (self.usps_container)
        etree.SubElement(package_node, "Size").text = "%s" % (self.usps_container_size)

        etree.SubElement(package_node, "Width").text = "%s" % (self.usps_default_product_packaging_id.width)
        etree.SubElement(package_node, "Length").text = "%s" % (self.usps_default_product_packaging_id.length)
        etree.SubElement(package_node, "Height").text = "%s" % (self.usps_default_product_packaging_id.height)
        etree.SubElement(package_node, "Girth").text = ""

        if self.usps_delivery_nature == 'domestic':
            etree.SubElement(package_node, "Machinable").text = "%s" % (self.usps_machinable)
        try:
            _logger.info("\nRate Request%s"%(etree.tostring(service_root)))
            results = self.call_api(api_name, etree.tostring(service_root))
            _logger.info("\nRate Response%s"%results)
        except Exception as e:
            res['error_message'] = e
            return res
        error_message = self.check_error_response(results)
        if error_message:
            return error_message
        if results.get('IntlRateV2Response', {}):
            package_rate = results.get('IntlRateV2Response', {}).get('Package', {}).get('Service', {})[0].get('Postage')
        else:
            package_rate = results.get('RateV4Response', {}).get('Package', {}).get('Postage', {}).get('Rate')

        if package_rate:
            res.update({'ShippingCharge': package_rate or 0.0,
                        'CurrencyCode': ""})
        else:
            res['error_message'] = (_("Shipping service is not available for this location.!"))
        return res

    @api.multi
    def usps_ept_rate_shipment(self, orders):
        """ Get the Rate of perticular shipping service for USPS
            @param 
            @return: dict of default value of rate
            @author: Jigar v Vagadiya on dated 27-may-2017
        """
        res = []
        for order in orders:
            # check the address validation
            check_value = self.check_required_value_to_ship(order)
            # check the product weight is appropriate to maximum weight.
            if check_value:
                return {'success': False, 'price': 0.0, 'error_message': check_value, 'warning_message': False}
            # check the product weight is appropriate to maximum weight.
            shipment_weight = self.usps_default_product_packaging_id and self.usps_default_product_packaging_id.max_weight or 0.0
            if shipment_weight:
                check_weight = self.check_max_weight(order, shipment_weight)
                if check_weight:
                    return {'success': False, 'price': 0.0, 'error_message': check_weight, 'warning_message': False}

            shipper_address = order.warehouse_id.partner_id
            recipient_address = order.partner_shipping_id
            # convet weight in to the delivery method's weight UOM
            total_weight = self.convert_weight(order.company_id and order.company_id.weight_unit_of_measurement_id,
                                               self.weight_uom_id, sum(
                    [(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if
                     not line.is_delivery]))
            ounces = round((total_weight) * 16, 3)
            # ounces = self.convert_weight("OZ", sum([(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if not line.is_delivery]))
            #             pounds = int(math.floor(total_weight))
            #             ounces = round((total_weight - pounds) * 16, 3)

            declared_value = round(order.amount_untaxed, 2)
            declared_currency = order.currency_id.name

            shipping_dict = self.usps_get_shipping_rate(shipper_address, recipient_address, total_weight,
                                                        packages=False, picking_bulk_weight=False,
                                                        declared_value=declared_value, \
                                                        declared_currency=declared_currency, ounces=ounces)

            if shipping_dict['error_message']:
                return {'success': False, 'price': 0.0, 'error_message': shipping_dict['error_message'],
                        'warning_message': False}

            currency_code = shipping_dict.get('CurrencyCode')
            shipping_charge = shipping_dict.get('ShippingCharge')
            rate_currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
            price = rate_currency.compute(float(shipping_charge), order.currency_id)
            res += [float(price)]
        return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}

    @api.model
    def usps_ept_send_shipping(self, pickings):
        """ Genrate the Lable of perticular shipping service for USPS
            @param : picking
            @return: Lable(final data pass in to USPS, Confoirm The Request.)
            @author: Jigar v Vagadiya on dated 28 AUG 2017.
        """
        response = []
        for picking in pickings:
            total_weight = self.convert_weight(picking.weight_uom_id, self.weight_uom_id, picking.shipping_weight)
            total_bulk_weight = self.convert_weight(picking.weight_uom_id, self.weight_uom_id, picking.weight_bulk)
            # ounces = self.convert_weight("OZ",picking.shipping_weight)
            total_value = sum([(line.product_uom_qty * line.product_id.list_price) for line in pickings.move_lines])
            ounces = round((total_weight) * 16, 3)
            to_address = picking.partner_id
            from_address = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
            api_name = self.deside_conform_api()
            express_mail = False

            if not self.prod_environment:
                if self.usps_evsapi_use:
                    if self.usps_delivery_nature == 'domestic':
                        service_root = etree.Element("eVSCertifyRequest")
                    else:
                        raise Warning("Currently International shipping is not provided.")
                else:
                    if self.usps_delivery_nature == 'domestic':
                        if self.usps_service_type in ['Priority', 'First Class']:
                            service_root = etree.Element("DelivConfirmCertifyV4.0Request")
                        else:
                            service_root = etree.Element("ExpressMailLabelCertifyRequest")
                            express_mail = True
                    else:
                        if self.usps_service_type == 'Priority':
                            service_root = etree.Element("PriorityMailIntlCertifyRequest")
                        if self.usps_service_type == 'Express':
                            service_root = etree.Element("ExpressMailIntlCertifyRequest")
                        if self.usps_service_type == 'First Class':
                            service_root = etree.Element("FirstClassMailIntlCertifyRequest")
            else:
                if self.usps_evsapi_use:
                    if self.usps_delivery_nature == 'domestic':
                        service_root = etree.Element("eVSRequest")
                    else:
                        raise Warning("International shipment is not provided in this module!")
                else:
                    if self.usps_delivery_nature == 'domestic':
                        if self.usps_service_type in ['Priority', 'First Class']:
                            service_root = etree.Element("DeliveryConfirmationV4.0Request")
                        else:
                            service_root = etree.Element("ExpressMailLabelRequest")
                            express_mail = True
                    else:
                        if self.usps_service_type == 'Priority':
                            service_root = etree.Element("PriorityMailIntlRequest")
                        if self.usps_service_type == 'Express':
                            service_root = etree.Element("ExpressMailIntlRequest")
                        if self.usps_service_type == 'First Class':
                            service_root = etree.Element("FirstClassMailIntlRequest")

            service_root.attrib['USERID'] = "%s" % (
            self.shipping_instance_id and self.shipping_instance_id.usps_userid or "")
            etree.SubElement(service_root, "Option").text = ""
            etree.SubElement(service_root, "Revision").text = "2"

            if express_mail:
                # Just Define Because future use for this parameter in USPS.
                etree.SubElement(service_root, "EMCAAccount").text = ""
                etree.SubElement(service_root, "EMCAPassword").text = ""
            if self.usps_evsapi_use:
                ImageParameters = etree.SubElement(service_root, "ImageParameters")
                etree.SubElement(ImageParameters,"ImageParameter").text = self.usps_label_size or ""
            if self.usps_delivery_nature == 'domestic' and self.usps_service_type in ['Priority', 'First Class'] or self.usps_evsapi_use:
                etree.SubElement(service_root, "FromName").text = "%s" % (from_address.name or "")
            else:
                etree.SubElement(service_root, "ImageParameters").text = ""
                etree.SubElement(service_root, "FromFirstName").text = ""
                etree.SubElement(service_root, "FromLastName").text = ""
            etree.SubElement(service_root, "FromFirm").text = "%s" % (from_address.name or "USPS")
            etree.SubElement(service_root, "FromAddress1").text = "%s" % (from_address.street or "")
            etree.SubElement(service_root, "FromAddress2").text = "%s" % (from_address.street2 or from_address.street or "")
            etree.SubElement(service_root, "FromCity").text = "%s" % (from_address.city or "")
            etree.SubElement(service_root, "FromState").text = "%s" % (
            from_address.state_id and from_address.state_id.code or "")
            etree.SubElement(service_root, "FromZip5").text = "%s" % (from_address.zip or "")
            etree.SubElement(service_root, "FromZip4").text = "%s" % (from_address.zip[:4] or "")
            if self.usps_evsapi_use:
                etree.SubElement(service_root, "FromPhone").text = "%s" % (re.sub('[^A-Za-z0-9]+', '', from_address.phone) or "")
            if self.usps_delivery_nature == 'domestic' and self.usps_service_type in ['Priority', 'First Class'] or self.usps_evsapi_use:
                etree.SubElement(service_root, "ToName").text = "%s" % (to_address.name or "")
            else:
                etree.SubElement(service_root, "FromPhone").text = "%s" % (re.sub('[^A-Za-z0-9]+', '', from_address.phone) or "")
                if not self.usps_evsapi_use:
                    etree.SubElement(service_root, "ToFirstName").text = ""
                    etree.SubElement(service_root, "ToLastName").text = ""
            
            etree.SubElement(service_root, "ToFirm").text = "%s" % (to_address.name or "")
            etree.SubElement(service_root, "ToAddress1").text = "%s" % (to_address.street or "")
            etree.SubElement(service_root, "ToAddress2").text = "%s" % (to_address.street2 or to_address.street or "")
            etree.SubElement(service_root, "ToCity").text = "%s" % (to_address.city or "")

            if self.usps_delivery_nature == 'domestic':
                etree.SubElement(service_root, "ToState").text = "%s" % (
                to_address.state_id and to_address.state_id.code or "")
                etree.SubElement(service_root, "ToZip5").text = "%s" % (to_address.zip or "")
                etree.SubElement(service_root, "ToZip4").text = "%s" % (to_address.zip[:4] or "")
            else:
                etree.SubElement(service_root, "ToCountry").text = "%s" % (
                to_address.country_id and to_address.country_id.name)
                etree.SubElement(service_root, "ToPostalCode").text = "%s" % (to_address.zip or "")
                etree.SubElement(service_root, "ToPOBoxFlag").text = "N"
            if self.usps_delivery_nature == 'domestic':
                if self.usps_service_type not in ['Priority', 'First Class'] or self.usps_evsapi_use:
                    etree.SubElement(service_root, "ToPhone").text = "%s" % (re.sub('[^A-Za-z0-9]+', '', str(to_address.phone)) or "")
            else:
                etree.SubElement(service_root, "ToPhone").text = "%s" % (re.sub('[^A-Za-z0-9]+', '', to_address.phone) or "")

            if self.usps_delivery_nature == 'domestic':
                etree.SubElement(service_root, "WeightInOunces").text = "%s" % (ounces or "")

            if self.usps_delivery_nature == 'domestic':
                if self.usps_service_type in ['Priority', 'First Class'] or self.usps_evsapi_use:
                    etree.SubElement(service_root, "ServiceType").text = "%s" % (self.usps_service_type or "")
                else:
                    # ZIP Code of Post Office or collection box where item is mailed. May be different than From ZIP Code.
                    etree.SubElement(service_root, "POZipCode").text = ""

            if self.usps_delivery_nature == 'international' and self.usps_service_type in ['Priority', 'Express'] or self.usps_evsapi_use:
                etree.SubElement(service_root, "Container").text = "%s" % (self.usps_container or "")

            if self.usps_delivery_nature == 'international':
                if self.usps_service_type == 'First Class':
                    etree.SubElement(service_root, "FirstClassMailType").text = "%s" % (
                    self.usps_firstclass_mail_type or "")
                shipment_content = etree.SubElement(service_root, "ShippingContents")
                for line in picking.move_lines:
                    item_detail = etree.SubElement(shipment_content, "ItemDetail")
                    etree.SubElement(item_detail, "Description").text = "%s" % (
                    line.product_id and line.product_id.name)
                    etree.SubElement(item_detail, "Quantity").text = "%s" % (int(line.product_uom_qty))

                    value = line.product_uom_qty * line.product_id.list_price
                    total_pound_weight = self.convert_weight(picking.weight_uom_id, self.weight_uom_id,
                                                             line.product_id.weight)
                    pound = int(math.floor(total_pound_weight))
                    ounce = round((total_pound_weight) * 16, 3)

                    etree.SubElement(item_detail, "Value").text = "%s" % (value)
                    etree.SubElement(item_detail, "NetPounds").text = "%s" % (pound)
                    etree.SubElement(item_detail, "NetOunces").text = "%s" % (ounce)
                    etree.SubElement(item_detail, "HSTariffNumber").text = ""
                    etree.SubElement(item_detail, "CountryOfOrigin").text = ""
                etree.SubElement(service_root, "GrossPounds").text = "%s" % (int(ceil(total_weight)))
                etree.SubElement(service_root, "GrossOunces").text = "%s" % (int(ounces))
                etree.SubElement(service_root, "ContentType").text = "%s" % (self.usps_content_type)
                etree.SubElement(service_root, "Agreement").text = "Y"
            if not self.usps_evsapi_use:
                etree.SubElement(service_root, "ImageType").text = "%s" % (self.usps_label_type)

#             if self.usps_delivery_nature == 'international' and self.usps_service_type not in ['Priority', 'Express'] or self.usps_evsapi_use:
#                 etree.SubElement(service_root, "Container").text = "%s" % (self.usps_container)
            if not self.usps_evsapi_use:
                etree.SubElement(service_root, "Size").text = "%s" % (self.usps_container_size)
            if self.usps_delivery_nature == 'domestic':
                etree.SubElement(service_root, "Width").text = "%s" % (
                self.usps_default_product_packaging_id.width or "")
                etree.SubElement(service_root, "Length").text = "%s" % (
                self.usps_default_product_packaging_id.length or "")
            else:
                etree.SubElement(service_root, "Length").text = "%s" % (
                self.usps_default_product_packaging_id.length or "")
                etree.SubElement(service_root, "Width").text = "%s" % (
                self.usps_default_product_packaging_id.width or "")

            etree.SubElement(service_root, "Height").text = "%s" % (self.usps_default_product_packaging_id.height or "")
            if not self.usps_evsapi_use:
                etree.SubElement(service_root, "Girth").text = ""

            if self.usps_delivery_nature == 'domestic':
                if self.usps_service_type in ['Priority', 'First Class']:
                    etree.SubElement(service_root, "Machinable").text = "%s" % (self.usps_machinable)
            if self.usps_evsapi_use:
                etree.SubElement(service_root, "ImageType").text = "%s" % (self.usps_label_type)
            # Important Note:call the first rate request because when rate genrate then conform API call
            shipping_dict = self.usps_get_shipping_rate(from_address, to_address, total_weight, packages=False,
                                                        picking_bulk_weight=False, declared_value=total_value, \
                                                        declared_currency=False, ounces=ounces)
            try:
                _logger.info("\nShippment Request%s"%(etree.tostring(service_root)))
                results = self.call_lable_api(api_name, etree.tostring(service_root))
                _logger.info("\nShippment Response%s"%(results))
            except Exception as e:
                raise Warning(e)
            self.check_error_response(results)
            if not self.prod_environment:
                if results.get('eVSCertifyResponse',{}):
                    binary_data = results.get('eVSCertifyResponse', {}).get('LabelImage',{})
                    tracking_no = results.get('eVSCertifyResponse', {}).get('BarcodeNumber',{})
                if results.get('DelivConfirmCertifyV4.0Response', {}):
                    binary_data = results.get('DelivConfirmCertifyV4.0Response', {}).get('DeliveryConfirmationLabel',{})
                    tracking_no = results.get('DelivConfirmCertifyV4.0Response', {}).get('DeliveryConfirmationNumber',{})
                if results.get('ExpressMailLabelCertifyResponse', {}):
                    binary_data = results.get('ExpressMailLabelCertifyResponse', {}).get('EMLabel', {})
                    tracking_no = results.get('ExpressMailLabelCertifyResponse', {}).get('EMConfirmationNumber', {})
                if results.get('PriorityMailIntlCertifyResponse', {}):
                    binary_data = results.get('PriorityMailIntlCertifyResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('PriorityMailIntlCertifyResponse', {}).get('BarcodeNumber', {})
                if results.get('ExpressMailIntlCertifyResponse', {}):
                    binary_data = results.get('ExpressMailIntlCertifyResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('ExpressMailIntlCertifyResponse', {}).get('BarcodeNumber', {})
                if results.get('FirstClassMailIntlCertifyResponse', {}):
                    binary_data = results.get('FirstClassMailIntlCertifyResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('FirstClassMailIntlCertifyResponse', {}).get('BarcodeNumber', {})
            else:
                if results.get('eVSResponse',{}):
                    binary_data = results.get('eVSResponse', {}).get('LabelImage',{})
                    tracking_no = results.get('eVSResponse', {}).get('BarcodeNumber',{})
                if results.get('DelivConfirmV4.0Response', {}):
                    binary_data = results.get('DelivConfirmV4.0Response', {}).get('DeliveryConfirmationLabel', {})
                    tracking_no = results.get('DelivConfirmV4.0Response', {}).get('DeliveryConfirmationNumber', {})
                if results.get('ExpressMailLabelResponse', {}):
                    binary_data = results.get('ExpressMailLabelResponse', {}).get('EMLabel', {})
                    tracking_no = results.get('ExpressMailLabelResponse', {}).get('EMConfirmationNumber', {})
                if results.get('PriorityMailIntlResponse', {}):
                    binary_data = results.get('PriorityMailIntlResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('PriorityMailIntlResponse', {}).get('BarcodeNumber', {})
                if results.get('ExpressMailIntlResponse', {}):
                    binary_data = results.get('ExpressMailIntlResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('ExpressMailIntlResponse', {}).get('BarcodeNumber', {})
                if results.get('FirstClassMailIntlResponse', {}):
                    binary_data = results.get('FirstClassMailIntlResponse', {}).get('LabelImage', {})
                    tracking_no = results.get('FirstClassMailIntlResponse', {}).get('BarcodeNumber', {})
                #raise Warning("Test Warning...")
            label_binary_data = binascii.a2b_base64(str(binary_data))
            logmessage = (_("Shipment created!<br/> <b>Shipment Tracking Number : </b>%s") % (tracking_no))
            picking.message_post(body=logmessage, attachments=[
                ('USPS Label-%s.%s' % (tracking_no, self.usps_label_type), label_binary_data)])
            if self.usps_evsapi_use:
                if not self.prod_environment:
                    if results.get('eVSCertifyResponse',{}):
                        receipt_binary_data = results.get('eVSCertifyResponse', {}).get('ReceiptImage',{})
                else:
                    if results.get('eVSResponse',{}):
                        receipt_binary_data = results.get('eVSResponse', {}).get('ReceiptImage',{})
                receipt_binary_data = binascii.a2b_base64(str(receipt_binary_data))
                logmessage = (_("ReceiptImage created!<br/> "))
                picking.message_post(body=logmessage, attachments=[
                    ('USPS ReceiptImageLabel-%s.%s' % (tracking_no, self.usps_label_type), receipt_binary_data)])
            exact_price = shipping_dict.get('ShippingCharge', {})
            shipping_data = {
                'exact_price': exact_price,
                'tracking_number': tracking_no}
            response += [shipping_data]
        return response
    @api.multi
    def usps_ept_get_tracking_link(self, pickings):
        """ Tracking the shipment from USPS
            @param: Picking Detail
            @return: Redirect from USPS site
            @author: Jigar v vagadiya
        """
        res = ""
        for picking in pickings:
            link = self.shipping_instance_id and self.shipping_instance_id.tracking_link or "https://tools.usps.com/go/TrackConfirmAction?tLabels="
            #Tracking Link = https://tools.usps.com/go/TrackConfirmAction?tLabels=
            res = '%s %s' % (link, picking.carrier_tracking_ref)
        return res
    @api.multi
    def usps_ept_cancel_shipment(self, picking):
        tracking_nos = picking.carrier_tracking_ref.split()
        for trcking_no in tracking_nos:
            if not self.usps_evsapi_use:
                service_root = etree.Element("CarrierPickupCancelRequest")
                service_root.attrib['USERID'] = "%s" % (self.shipping_instance_id and self.shipping_instance_id.usps_userid or "")
                partner_id=picking.partner_id
                etree.SubElement(service_root, "FirmName").text="%s"%(partner_id and partner_id.name or "")
                etree.SubElement(service_root, "SuiteOrApt").text = ""
                etree.SubElement(service_root, "Address2").text = "%s"%(partner_id and partner_id.street or "")
                etree.SubElement(service_root, "Urbanization").text = ""
                etree.SubElement(service_root, "City").text = "%s"%(partner_id and partner_id.city)
                etree.SubElement(service_root, "State").text = "%s"%(partner_id and partner_id.state_id and partner_id.state_id.code)
                etree.SubElement(service_root, "ZIP5").text = "%s"%(partner_id and partner_id.zip)
                etree.SubElement(service_root, "ZIP4").text = ""
                etree.SubElement(service_root, "ConfirmationNumber").text = "%s"%(trcking_no)
                try:
                    _logger.info("\nCarrierPickupCancel Request%s"%(etree.tostring(service_root)))
                    results = self.call_lable_api("CarrierPickupCancel", etree.tostring(service_root))
                    _logger.info("\nCarrierPickupCancel Response%s"%(results))
                except Exception as e:
                    raise Warning(e)
                self.check_error_response(results)
                   # results={"CarrierPickupCancelResponse":{
                #     "FirmName": "ABC Corp.",
                #     "SuiteOrApt": "Suite 777",
                #     "Address2": "1390 Market Street",
                #     "Urbanization": [],
                #     "City": "Houston",
                #     "State": "TX",
                #     "ZIP5": "77058",
                #     "ZIP4": "1234",
                #     "ConfirmationNumber": "ABC12345",
                #     "Status": "Your pickup request was cancelled."
                # }}
                if results.get('CarrierPickupCancelResponse') and results.get('CarrierPickupCancelResponse').get('ConfirmationNumber'):
                    confirmation_number=results.get('CarrierPickupCancelResponse').get('ConfirmationNumber')
                    status_message=results.get('CarrierPickupCancelResponse').get('Status')
                    picking.message_post(body=_(u'%s - %s' %(confirmation_number,status_message)))
                else:
                    raise Warning(results)
            else:
                service_root = etree.Element("eVSCancelRequest")
                service_root.attrib['USERID'] = "%s" % (self.shipping_instance_id and self.shipping_instance_id.usps_userid or "")
                etree.SubElement(service_root,"BarcodeNumber").text = "%s"%(trcking_no)
                try:
                    _logger.info("\neVSCancel Request%s"%(etree.tostring(service_root)))
                    results = self.call_lable_api("eVSCancel", etree.tostring(service_root))
                    _logger.info("\neVSCancel Response%s"%results)
                except Exception as e:
                    raise Warning(results)
                if results.get('eVSCancelResponse') and results.get('eVSCancelResponse').get('Status',False):
                    if results.get('eVSCancelResponse').get('Status',False)== 'Not Cancelled':
                        raise Warning(results.get('eVSCancelResponse').get('Reason'))
                    else:
                        picking.carrier_tracking_ref = ''
                        picking.message_post(body=_(u'%s - %s' %(results.get('eVSCancelResponse') and results.get('eVSCancelResponse').get('BarcodeNumber'),results.get('eVSCancelResponse').get('Reason'))))
                else:
                    raise Warning(results.get('Error',False).get('Description',False))
        return True