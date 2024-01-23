from odoo import models, fields, api, _, exceptions
import json


class OnlineBookingLinemany(models.Model):
    _name = 'vendor.rfq'
    _description = 'Online Booking Line'
    _rec_name = 'name_seq'

    name_seq = fields.Char(string='RFQ Code', required=True, copy=False, readonly=True,
                           index=True, default=lambda self: _('New'))
    booking_lines = fields.One2many('vendor.rfq.lines', 'online_booking_id', string='Booking Lines')
    vendor_id = fields.Many2one('res.partner', string="Vendor name", domain=[('supplier', '=', 'True')])
    rfq_lines = fields.Many2one('vendor.rfq.lines', string="Vendor name")

    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)
    link_field = fields.Char(string='Link Field')  # Add this line for the new field
    color_field = fields.Selection([('green', 'Green'), ('red', 'Red')], 'Color', compute="compute_color")
    location_id = fields.Many2one('stock.warehouse', string='Warehouse Location', readonly=True,
                                  default=lambda self: self.env['stock.warehouse'].search(
                                      [('name', '=', 'Out Patient Store')]).id)

    @api.multi
    def create_quotation(self):
        self.ensure_one()
        # Create sale order lines from the current record's booking lines
        sale_order_lines = [(0, 0, {
            'name': line.product_id.id,
            'product_id': line.product_id.id,
            'date_planned': fields.Date.today(),
            'product_qty': line.quantity_id,
            'price_unit': line.price_id,
            'product_uom': line.uom_id.id,
        }) for line in self.booking_lines]

        # Create a sale order (quotation)
        sale_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'warehouse_id': self.location_id.id,
            'order_line': sale_order_lines,
            'order_policy': 'manual',
        })
        return {
            'name': _('Quotation Created'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': sale_order.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.depends('total_price')
    def compute_color(self):
        lowest_price_record = self.search([], order='total_price', limit=1)
        for record in self:
            if record == lowest_price_record:
                record.color_field = 'green'
            else:
                record.color_field = 'red'

    @api.depends('booking_lines.price_id')
    def _compute_total_price(self):
        for record in self:
            for total in record.booking_lines:
                record.total_price += total.quantity_id * total.price_id

    def open_google_link(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://localhost:8069/Request_For_Quotation/rfq',
            # 'url': 'Request_For_Quotation/rfq',
            'target': 'new',
        }

    @api.multi
    def open_vendor_link(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.link_field,
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('vendor.rfq.sequence') or _('New')
        result = super(OnlineBookingLinemany, self).create(vals)
        result.compute_color()

        return result


class OnlineBookingsendrfq(models.Model):
    _name = 'vendor.send.rfq'
    _description = 'Online Booking Line'
    _rec_name = 'vendor_id'

    vendor_id = fields.Many2one('res.partner', string="Vendor name")

    link_field = fields.Char(string='Link Field')

    computed_field_link = fields.Html(string='Link', compute='_compute_field_link')

    def _compute_field_link(self):
        for record in self:
            record.computed_field_link = '<a href="%s" target="_blank">%s</a>' % (record.link_field, record.link_field)

    def open_google_link(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://localhost:8069/Request_For_Quotation/rfq',
            # 'url': 'Request_For_Quotation/rfq',
            'target': 'new',
        }

    @api.multi
    def open_vendor_link(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.link_field,
            'target': 'new',
        }


class OnlineBookingLine(models.Model):
    _name = 'vendor.rfq.lines'
    _description = 'Online Booking Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'online_booking_id'

    online_booking_id = fields.Many2one('vendor.rfq', string='Online Booking')
    product_id = fields.Many2one('product.product', string='product')

    quantity_id = fields.Integer(string='Quantity')
    price_id = fields.Float(string='Price')
    uom_id = fields.Many2one('uom.uom', string=' Unit of Measure', related='product_id.product_tmpl_id.uom_id',
                             readonly=False)
    location_id = fields.Many2one('stock.warehouse', string='Warehouse Location', readonly=True,
                                  default=lambda self: self.env['stock.warehouse'].search(
                                      [('name', '=', 'Out Patient Store')]).id)
    vendor_id = fields.Many2one('res.partner', string="Vendor name")

    # uom_domain = fields.Char(compute='get_uom_s', readonly=True, invisible='1')

    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    vendor_reference = fields.Text(string='Vendor Reference')

    best_price = fields.Boolean(string='Best Price', compute='_compute_best_price')
    color_field = fields.Selection([('green', 'Green'), ('red', 'Red')], 'Color', compute="compute_color")

    @api.depends('price_id', 'product_id')
    def compute_color(self):
        # Dictionary to store the lowest price for each product
        lowest_prices = {}
        for line in self.sorted(key=lambda r: (r.product_id.name, r.date, r.price_id)):
            if line.product_id:
                product_key = line.product_id.name
                if product_key not in lowest_prices or line.price_id < lowest_prices[product_key].price_id:
                    lowest_prices[product_key] = line

        for line in self:
            line.color_field = 'green' if line == lowest_prices.get(line.product_id.name, None) else 'red'

    @api.depends('price_id', 'product_id')
    def _compute_best_price(self):
        # Dictionary to store the lowest price for each product
        lowest_prices = {}

        for line in self.sorted(key=lambda r: (r.product_id.name, r.date, r.price_id)):
            if line.product_id:
                product_key = line.product_id.name
                if product_key not in lowest_prices or line.price_id < lowest_prices[product_key].price_id:
                    lowest_prices[product_key] = line

        for line in self:
            line.best_price = line == lowest_prices.get(line.product_id.name, None)
            line.color_field = 'green' if line.best_price else 'red'
            if line.best_price:
                line.notify_best_price()

    _order = 'product_id, date DESC, price_id ASC'

    def notify_best_price(self):
        for line in self:
            # You can customize the notification message here
            message = "New best price determined for {}!".format(self.product_id.name)

            # Notify the responsible user
            self.env.user.notify_info(message, title="Best Price Notification")

            action = {
                'name': 'Best Price Record',
                'type': 'ir.actions.act_window',
                'res_model': 'vendor.rfq.lines',  # Adjust the model name accordingly
                'view_mode': 'form',
                'res_id': line.id,
            }

            # Trigger the client action to open the record
            return action

    # @api.onchange('product_id')
    # def get_uom_s(self):
    #     for rec in self:
    #         if rec.product_id:
    #             rec.uom_domain = json.dumps([('id', 'in', [rec.product_id.uom_id.id, rec.product_id.uom_po_id.id])])
    #         else:
    #             rec.uom_domain = json.dumps([('id', 'in', [])])
