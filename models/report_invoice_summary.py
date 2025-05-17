from odoo import models
from collections import defaultdict

class ReportInvoiceSummary(models.AbstractModel):
    _name = 'report.khabir_hijama.report_invoice_summary'
    _description = 'Invoice Summary Report'

    def get_report_values(self, docids, data=None):
        # get account.move records by docids
        docs = self.env['account.move'].browse(docids).filtered(
            lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'
        )
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
        }
def get_report_values(self, docids, data=None):
    docs = self.env['account.move'].browse(docids).filtered(
        lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'
    )
    total_sum = sum(d.amount_total for d in docs)
    return {
        'doc_ids': docids,
        'doc_model': 'account.move',
        'docs': docs,
        'total_sum': total_sum,
    }

class ReportInvoiceSummary(models.AbstractModel):
    _name = 'report.khabir_hijama.report_invoice_summary'
    _description = 'Invoice Summary Report'

    def get_report_values(self, docids, data=None):
        invoices = self.env['account.move'].browse(docids).filtered(
            lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'
        )

        grouped_data = defaultdict(lambda: {
            'invoices': [],
            'total_amount': 0.0,
            'total_cash': 0.0,
            'total_bank': 0.0,
        })

        grand_total = 0.0

        for inv in invoices:
            partner_name = inv.partner_id.name or 'Unknown Customer'
            grouped_data[partner_name]['invoices'].append(inv)
            grouped_data[partner_name]['total_amount'] += inv.amount_total
            grouped_data[partner_name]['total_cash'] += inv.cash_amount_paid
            grouped_data[partner_name]['total_bank'] += inv.bank_amount_paid
            grand_total += inv.amount_total

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'grouped_data': dict(grouped_data),
            'grand_total': grand_total,
        }
