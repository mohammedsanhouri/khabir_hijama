from odoo import models, fields, api


class JournalSelectionWizard(models.TransientModel):
    _name = 'journal.selection.wizard'
    _description = 'Journal Selection Wizard'

    journal_id = fields.Many2one('account.journal', string="Select Journal")

    def action_select_journal(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'khabir.hijama':
            custom_model = self.env[active_model].browse(active_id)
            custom_model.journal_id = self.journal_id
            is_saudi = False
            if custom_model.id_number and custom_model.id_number.startswith('1'):
                is_saudi = True
            elif custom_model.customer_id.country_id.code == 'SA':
                is_saudi = True
        
            tax_ids = []
            if not is_saudi:
                tax_ids = custom_model.hijama_type.product_id.taxes_id.ids
              
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': custom_model.customer_id.id,
                'invoice_date': fields.Date.context_today(self),
                'hijama_id': custom_model.id,
                'journal_id': self.journal_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': custom_model.hijama_type.product_id.id,
                    'quantity': 1,
                    'price_unit': custom_model.cost,
                    'tax_ids': [(6, 0, tax_ids)],
                })],
            })
            custom_model.is_invoiced = True
        return {'type': 'ir.actions.act_window_close'}
