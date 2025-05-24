from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
from datetime import date, timedelta
from odoo.exceptions import UserError

class SourceInfo(models.Model):

    _name = 'hijama.source.info'
    _description = 'Source of Information'

    name = fields.Char(string="Source of Informtion",required=True) 

class AccountMove(models.Model):
    _inherit = 'account.move'

    hijama_type_id = fields.Many2one(
        'hijama.type',
        string="Hijama Type",
        compute='_compute_hijama_type',
        store=True,
    )

    @api.depends('invoice_line_ids')
    def _compute_hijama_type(self):
        for move in self:
            # Find one cupping session linked to this invoice
            session = self.env['khabir.hijama'].search([('invoice_ids', '=', move.id)], limit=1)
            move.hijama_type_id = session.hijama_type.id if session else False
    cash_amount_paid = fields.Monetary(
        string="Cash Paid", compute='_compute_payment_breakdown',currency_field='currency_id', store=True
    )
    bank_amount_paid = fields.Monetary(
        string="Bank Paid", compute='_compute_payment_breakdown',currency_field='currency_id', store=True
    )
    @api.depends('payment_state', 'line_ids.payment_id.journal_id', 'line_ids.payment_id.amount')
    def _compute_payment_breakdown(self):
        for move in self:
            cash = 0.0
            bank = 0.0
            currency = move.currency_id or move.company_currency_id
            for payment in move._get_reconciled_payments():
                if payment.journal_id.type == 'cash':
                    cash += payment.amount
                elif payment.journal_id.type == 'bank':
                    bank += payment.amount
            move.cash_amount_paid = cash
            move.bank_amount_paid = bank
class HijamaAccountMove(models.Model):
    _inherit = 'account.move'

    hijama_id = fields.Many2one('khabir.hijama', string="Hijama ID", ondelete='set null')

    @api.onchange('partner_id')
    def _onchange_partner_id_remove_tax_saudi(self):
        for move in self:
            if move.partner_id and move.partner_id.country_id.code == 'SA':
                for line in move.invoice_line_ids:
                    line.tax_ids = [(5, 0, 0)]  # Remove all taxes

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.partner_id and move.partner_id.country_id.code == 'SA':
                for line in move.invoice_line_ids:
                    line.tax_ids = [(5, 0, 0)]  # Remove all taxes
        return moves

class KhabirHijama(models.Model):
    _name = 'khabir.hijama'

    name = fields.Char(string="Name",readonly=True)
    hijama_type = fields.Many2one('hijama.type',string="Hijama Type", tracking=True, required=True)
    customer_id = fields.Many2one('res.partner', string="Customer", tracking=True, required=True)
    doctor_id = fields.Many2one('hijama.doctor',string="Doctor", tracking=True)
    doctor_presentage = fields.Integer(string="Doctor Commission", tracking=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today(), tracking=True)
    age = fields.Integer(string="Age", tracking=True, required=True)
    cost = fields.Float(string="Cost", tracking=True, compute="get_cost", store=True, readonly=False)
    nationality = fields.Many2one('res.country',string="Nationality", tracking=True)
    id_number = fields.Char(string="ID", tracking=True)
    mobile = fields.Char(string="Mobile", tracking=True)
    city = fields.Char(string="City", tracking=True)
    neighbor = fields.Char(string="Neighbor", tracking=True)
    contact_name = fields.Char(string="Contact Name", tracking=True)
    contact_mobile = fields.Char(string="Contact Mobile", tracking=True)
    hijama_reasons = fields.Char(string="Hijama Reasons", tracking=True)
    commission_amount = fields.Float(string="Commission Fee", readonly=False, tracking=True)
    used_medicals = fields.Char(string="Used Medicals", tracking=True)
    marital_status = fields.Selection([('married', 'Married'),
                             ('single', 'Single')], string="Marital Status", default='single', tracking=True)
    sex = fields.Selection([('male', 'Male'),
                             ('female', 'Female')], string="Sex", tracking=True)
    job = fields.Selection([('gov', 'Goverment'),
                             ('private', 'Private')], string="Job", tracking=True)
    education = fields.Selection([('middle', 'Middle'),
                             ('high', 'High'),
                             ('diploma', 'Diploma'),
                             ('university', 'University')], string="Education", tracking=True)
    hepatitis = fields.Boolean(string="Hepatitis (C) or (B)", tracking=True)
    aids = fields.Boolean(string="Aida", tracking=True)
    cva = fields.Boolean(string="CVA", tracking=True)
    cancer = fields.Boolean(string="Cancer", tracking=True)
    kidney_diseases = fields.Boolean(string="Kidney Diseases", tracking=True)
    bleeding_disorders = fields.Boolean(string="Bleeding Disorders", tracking=True)
    cardiac_diseases = fields.Boolean(string="Cardiac Diseases", tracking=True)
    pregnancy = fields.Boolean(string="Pregnancy", tracking=True)
    found = fields.Many2one('hijama.source.info',string="How did you know about us?", tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('check', 'Check'),
                             ('confirm', 'Confirm'),
                             ('paid', 'Paid'),
                             ('complete', 'Complete'),
                             ('cancel', 'Cancel')], string="State",default="draft",tracking=True)
    invoice_ids = fields.One2many('account.move', 'hijama_id', string="Invoices")
    is_invoiced = fields.Boolean(string="Is Invoiced", default=False)
    journal_id = fields.Many2one('account.journal', string="Journal")
    commission_created = fields.Boolean(string="Commission Created", default=False)
    show_create_commission_button = fields.Boolean(compute="_compute_show_create_commission_button")
    price_unit = fields.Float(string='Unit Price', compute='_compute_price_unit', store=True)

    @api.depends('invoice_ids')
    def _compute_price_unit(self):
        for rec in self:
            if rec.invoice_ids and rec.invoice_ids.invoice_line_ids:
                rec.price_unit = rec.invoice_ids.invoice_line_ids[0].price_unit
            else:
                rec.price_unit = 0.0
    @api.depends('state', 'doctor_id', 'hijama_type.have_presentage', 'commission_amount', 'commission_created')            
    def _compute_show_create_commission_button(self):
     for rec in self:
        rec.show_create_commission_button = (
            rec.state == 'complete'
            and rec.doctor_id
            and rec.hijama_type.have_presentage
            and rec.commission_amount > 0
            and not rec.commission_created
        )
    @api.depends('state', 'is_invoiced', 'show_create_commission_button')
    def _compute_button_visibility(self):
        for rec in self:
            rec.can_check = (rec.state == 'draft')
            rec.can_invoice = (rec.state == 'check') and not rec.is_invoiced
            rec.can_create_commission = (rec.state == 'complete') and rec.show_create_commission_button
            rec.can_confirm = (rec.state == 'check') and rec.is_invoiced
            rec.can_complete = (rec.state == 'confirm')
            rec.can_cancel = rec.state in ['draft', 'check', 'confirm']
                
    @api.constrains('mobile', 'id_number')
    def _check_mobile_and_id(self):
     for rec in self:
        
        if not re.fullmatch(r'05\d{8}', rec.mobile or ''):
            raise ValidationError("mobile number must be 10 digits starting with 05.")

        
        if not re.fullmatch(r'\d{10}', rec.id_number or ''):
            raise ValidationError("ID number must be exactly 10 digits.")

        
        existing_mobile = self.env['khabir.hijama'].search([
            ('mobile', '=', rec.mobile),
            ('id', '!=', rec.id)
        ], limit=1)
        if existing_mobile:
            raise ValidationError("mobile number is used.")

        
        existing_id = self.env['khabir.hijama'].search([
            ('id_number', '=', rec.id_number),
            ('id', '!=', rec.id)
        ], limit=1)
        if existing_id:
            raise ValidationError("ID number is used.")
    @api.depends('hijama_type')
    def get_cost(self):
        for record in self:
            record.cost = record.hijama_type.product_id.lst_price

    def check(self):
        return self.sudo().write({
            'state': 'check',
        })
    
    def confirm(self):
        for record in self:
            if record.is_invoiced == False:
                raise ValidationError(_("Create invoice first."))
            else:
                return self.sudo().write({
                    'state': 'confirm',
                })
    
    def paid(self):
        for record in self:
            if record.invoice_ids.payment_state == 'paid':
                return self.sudo().write({
                    'state': 'paid',
                })
            else:
                raise ValidationError(_("Pay the invoice first."))
    
    def complete(self):
        return self.sudo().write({
            'state': 'complete',
        })
    
    def cancel(self):
        return self.sudo().write({
            'state': 'cancel',
        })
    
    def invoice(self):
        # for record in self:

            # invoice = self.env['account.move'].create({
            #     'move_type': 'out_invoice',
            #     'partner_id': record.customer_id.id,
            #     'invoice_date': fields.Date.context_today(self),
            #     'hijama_id': record.id,
            #     'invoice_line_ids': [(0, 0, {
            #         'product_id': record.hijama_type.product_id.id,
            #         'quantity': 1,
            #         'price_unit': record.cost,
            #     })],
            # })
            # record.is_invoiced = True
        # return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'journal.selection.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('khabir_hijama.view_journal_selection_wizard').id,
            'target': 'new',  # Open as a modal
            'context': {'default_journal_id': self.journal_id.id},  # Pass current journal to the wizard (optional)
        }

    @api.depends('is_invoiced', 'state')  # Add other conditions as needed
    def _compute_show_invoice_button(self):
        for rec in self:
            rec.show_invoice_button = not rec.is_invoiced and rec.state == 'confirmed'


    show_cancel_button = fields.Boolean(compute="_compute_show_cancel_button")

    @api.depends('state')
    def _compute_show_cancel_button(self):
        for record in self:
            record.show_cancel_button = record.state in ['draft', 'check']
    def action_open_journal_wizard(self):
        # Open the journal selection wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'journal.selection.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('khabir_hijama.view_journal_selection_wizard').id,
            'target': 'new',  # Open as a modal
            'context': {'default_journal_id': self.journal_id.id},  # Pass current journal to the wizard (optional)
        }
    
    def create_commission_button(self):
        if self.commission_created:
            raise UserError("Commission already created.")
        self._check_and_create_commission()
        self.commission_created = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Commission Created"),
                'message': _("Doctor commission created successfully."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'create': False},
            'target': 'current',
        }
    @api.model
    def create(self, values):
        # Generate sequence number
        seq = self.env['ir.sequence'].next_by_code('khabir.hijama') or '/'
        values['name'] = seq

        # Create the record
        record = super(KhabirHijama, self.sudo()).create(values)

        # Check commission after creation
        record._check_commission_vs_price(values)

        return record

    def write(self, values):
        # Check commission on write
        self._check_commission_vs_price(values)
        return super().write(values)

    def _check_commission_vs_price(self, values):
        for record in self:
            # Check if commission_amount is present in the incoming values or already on the record
            commission = values.get('commission_amount', record.commission_amount)
            price_unit = values.get('price_unit', record.price_unit)

            if commission and price_unit and commission > price_unit:
                raise ValidationError(f"Commission ({commission}) cannot exceed the unit price ({price_unit}).")

    @api.depends('commission_ids','commission_ids.date', 'commission_ids.commission_amount', )
    def _check_and_create_commission(self):
     for session in self:
        if (
            session.doctor_id and
            session.hijama_type.have_presentage and
            session.commission_amount > 0 and
            session.invoice_ids
        ):
            invoice = session.invoice_ids[0]
            if invoice.payment_state == 'paid':
                existing = self.env['hijama.doctor.commission'].search([
                    ('hijama_session_id', '=', session.id)
                ], limit=1)
                if not existing:
                    self.env['hijama.doctor.commission'].create({
                        'doctor_id': session.doctor_id.id,
                        'patient_id': session.customer_id.id,
                        'hijama_session_id': session.id,
                        'invoice_id': invoice.id,
                        'commission_amount': session.commission_amount,
                    })

class HijamaTypes(models.Model):
    _name = 'hijama.type'

    name = fields.Char(string="Name")
    have_presentage = fields.Boolean(string="Have Presentage", tracking=True)
    product_id = fields.Many2one('product.product',string="Product", required=True)

class HijamaDoctor(models.Model):
    _name = 'hijama.doctor'

    name = fields.Char(string="Name")
    commission_ids = fields.One2many('hijama.doctor.commission', 'doctor_id', string="Commissions")
    commission_count = fields.Integer(string="Commission Count", compute="_compute_commission_count",)
    total_commission = fields.Monetary(string="Total Commission", compute="_compute_commission_summary", currency_field='currency_id',store=False)        
    day_commission = fields.Monetary(string="Day Commission", compute="_compute_commission_summary", currency_field='currency_id',store=False)
    week_commission = fields.Monetary(string="Week Commission", compute="_compute_commission_summary", currency_field='currency_id',store=False)
    month_commission = fields.Monetary(string="Month Commission", compute="_compute_commission_summary", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    @api.depends('commission_ids')
    def _compute_commission_count(self):
        for rec in self:
            rec.commission_count = len(rec.commission_ids)
    def action_view_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Doctor Commissions',
            'view_mode': 'tree,form',
            'res_model': 'hijama.doctor.commission',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'create': False},
        }
    
    @api.depends('commission_ids','commission_ids.date', 'commission_ids.commission_amount')
    def _compute_commission_summary(self):
        for doctor in self:
            now = date.today()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(weeks=1)
            month_ago = now - timedelta(days=30)
            
            doctor.week_commission = sum(doctor.commission_ids.filtered(lambda c: c.date >= week_ago).mapped('commission_amount'))
            doctor.month_commission = sum(doctor.commission_ids.filtered(lambda c: c.date >= month_ago).mapped('commission_amount'))
            doctor.day_commission = sum(doctor.commission_ids.filtered(lambda c: c.date >= day_ago).mapped('commission_amount'))
            doctor.total_commission = sum(doctor.commission_ids.mapped('commission_amount'))

class HijamaDoctorCommission(models.Model):
    _name = 'hijama.doctor.commission'
    _description = 'Doctor Commission'
    _order = 'date desc'

    doctor_id = fields.Many2one('hijama.doctor', string="Doctor", required=True)
    patient_id = fields.Many2one('res.partner', string="Patient")
    hijama_session_id = fields.Many2one('khabir.hijama', string="Session")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    commission_amount = fields.Monetary(string="Commission Fee", readonly=False)  # editable
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(string="Date", related='hijama_session_id.date', store=True)
    commission_count = fields.Integer(string="Commission Count", compute="_compute_commission_count",)
