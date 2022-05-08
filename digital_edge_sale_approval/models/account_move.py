from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute')

    ns_move_journal_type = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ], related='move_id.journal_id.type')
    ns_serial_number = fields.Char('Serial Number')

class AccountMove(models.Model):
    _inherit = "account.move"

    document_count = fields.Integer('Document Count', compute='_compute_document_count')

    def _compute_document_count(self):
        for record in self:
            record.document_count = len(self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', 'in', self.ids)]))
            
    def action_see_documents(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'account.move'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'account.move', 'default_res_id': self.id}
        return res
