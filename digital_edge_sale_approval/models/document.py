from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError

class DocumentsFolder(models.Model):
    _inherit = 'documents.folder'

    ns_vendor_bill = fields.Boolean('Vendor Bill')

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        res = super(IrAttachment, self).create(vals)
        if res.res_model == 'account.move' and self.env['account.move'].browse(res.res_id).move_type == 'in_invoice':
            folder_id = self.env['documents.folder'].search([('ns_vendor_bill','=',True)], limit=1)
            if not folder_id:
                raise UserError(_('Please make sure exactly one workspace is defined as Vendor Bill\'s workspace.'))
            self.env['documents.document'].create(
                {
                    'attachment_id': res.id,
                    'folder_id': folder_id.id
                }
            )
        return res