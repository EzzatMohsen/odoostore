import datetime
from odoo import fields
from odoo import http
from odoo.http import request
import base64
import werkzeug
from werkzeug import url_encode
from odoo import _, SUPERUSER_ID
from odoo.tools import config
import json
import datetime
from datetime import datetime, timedelta
import yaml
from odoo.exceptions import UserError


################################### RFQ Form for Vendors ################################################

class OnlineBookingtest(http.Controller):

    @http.route('/Request_For_Quotation/rfq', type='http', auth='public', methods=['GET'], csrf=False)
    def input_page(self, **kw):
        db_name = request.session.db

        username = kw.get('username', 'admin')
        password = kw.get('password', 'admin')

        # Authenticate the user dynamically
        uid = request.session.authenticate(db_name, username, password)

        partners_domain = [('supplier', '=', 'true')]
        partners = request.env['res.partner'].search(partners_domain)
        product_domain = [('type', '=', 'product')]
        product_name = request.env['product.product'].search(product_domain)
        selected_product_id = int(kw.get('product_id_1', 0))
        product_uoms = request.env['uom.uom'].search([])
        selected_uom_id = int(kw.get('uom_id_1', 0))
        return http.request.render('Request_For_Quotation.vendor_rfq', {
            'partners': partners,
            'product_names': product_name,
            'selected_product_id': selected_product_id,
            'product_uoms': product_uoms,
            'selected_uom_id': selected_uom_id,
        })

    @http.route('/agial/uom_options/', type='http', auth='public', methods=['GET'], csrf=False)
    def uomOptions(self, **kw):
        uom_list = []
        product_id = int(kw.get('product_id'))

        # Fetch UOM options based on the selected product
        uom_recs = request.env['product.product'].sudo().browse(product_id).uom_id | request.env[
            'product.product'].sudo().browse(product_id).uom_po_id
        if len(uom_recs) > 0:
            for uom in uom_recs:
                uom_list.append({'id': uom.id, 'name': uom.name})

        return json.dumps({
            'uoms': uom_list
        })

    @http.route('/Request_For_Quotation/meet_booking/rfq', type='http', auth='public', methods=['GET'], csrf=False)
    def online_booking(self, **kw):
        db_name = request.session.db

        username = kw.get('username', 'admin')
        password = kw.get('password', 'admin')

        # Authenticate the user dynamically
        uid = request.session.authenticate(db_name, username, password)

        num_lines = int(kw.get('num_lines', 1))
        product_data = []

        for i in range(1, num_lines + 1):
            product_id = int(kw.get('product_id_{}'.format(i), 0))
            quantity = kw.get('quantity_{}'.format(i))
            uom_id = int(kw.get('uom_id_{}'.format(i), 0))
            price = kw.get('price_{}'.format(i))

            product = request.env['product.product'].browse(product_id)
            uom = request.env['uom.uom'].browse(uom_id)

            product_data.append({
                'product_name': product.name,
                'quantity': quantity,
                'uom_id': uom.name,
                'price': price,
            })

        generated_link = kw.get('generated_link')
        partner_id = kw.get('partner_id')
        vendor_notes = kw.get('notes')
        online_booking = request.env['vendor.send.rfq'].create({
            'vendor_id': partner_id,
            'link_field': generated_link,
            'vendor_reference': vendor_notes,

        })

        selected_product_id = int(kw.get('product_id_1', 0))
        selected_uom_id = int(kw.get('uom_id_1', 0))

        product_options = request.env['product.product'].search([('id', '=', selected_product_id)])
        uom_options = request.env['uom.uom'].search([('id', '=', selected_uom_id)])

        return http.request.render('Request_For_Quotation.online_rfq', {
            'product_data': product_data,
            'num_lines': num_lines,
            'partner_id': partner_id,
            'product_options': product_options,
            'uom_options': uom_options,
            'notes': vendor_notes,
        })

    @http.route('/Request_For_Quotation/meet_booking/rfq/Thanks/', type='http', auth='public', methods=['GET'],
                csrf=False)
    def thanks(self, **kw):
        db_name = request.session.db

        username = kw.get('username', 'admin')
        password = kw.get('password', 'admin')

        # Authenticate the user dynamically
        uid = request.session.authenticate(db_name, username, password)

        num_lines = int(kw.get('num_lines', 1))
        product_data = []

        for i in range(1, num_lines + 1):
            product_name = kw.get('product_name_{}'.format(i))
            quantity = kw.get('quantity_{}'.format(i))
            uom = kw.get('uom_id_{}'.format(i))
            price = kw.get('price_{}'.format(i))

            product_data.append({
                'product_name': product_name,
                'quantity': quantity,
                'uom': uom,
                'price': price,
            })

        partner_id = kw.get('partner_id')
        current_url = kw.get('current_url')
        vendor_notes = kw.get('notes')

        online_booking = request.env['vendor.rfq'].create({
            'vendor_id': partner_id,
            'link_field': current_url,
            'vendor_reference': vendor_notes,

        })

        for product in product_data:
            product_id = request.env['product.product'].search([('name', '=', product['product_name'])], limit=1)
            uom_id = request.env['uom.uom'].search([('name', '=', product['uom'])], limit=1)

            if product_id and uom_id:
                request.env['vendor.rfq.lines'].create({
                    'online_booking_id': online_booking.id,
                    'product_id': product_id.id,
                    'quantity_id': product['quantity'],
                    'uom_id': uom_id.id,
                    'price_id': product['price'],
                    'vendor_reference': vendor_notes,

                })
        return http.request.render('Request_For_Quotation.Request_For_Quotation_rfq_thanks', {})
