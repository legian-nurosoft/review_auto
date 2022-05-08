from odoo import api, fields, models, _, exceptions
import logging

_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    ns_asset_id = fields.Char(string="Asset ID", readonly=1, copy=False)

    def validate(self):
        res = super(AccountAsset, self).validate()
        company_id = self.company_id.id
        self.write({'ns_asset_id': self.env['ir.sequence'].generate_sequence('account.asset', company_id)})
        return res
    
    def action_set_to_close(self):
        """ Returns an action opening the asset pause wizard."""
        self.ensure_one()
        new_wizard = self.env['account.asset.sell'].with_context(current_asset=self.id).create({
            'asset_id': self.id,
        })
        return {
            'name': _('Sell Asset'),
            'view_mode': 'form',
            'res_model': 'account.asset.sell',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
        }


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def generate_sequence(self, sequence_code, company_id, sequence_date=None):
        self.check_access_rights('read')
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [company_id, False])],
                              order='company_id')
        if not seq_ids:
            _logger.debug(
                "No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        seq_id = seq_ids[0]
        return seq_id._next(sequence_date=sequence_date)

class AccountAssetSell(models.TransientModel):    
    _inherit = 'account.asset.sell'

    def _compute_currency(self):
        active_id = self._context.get('current_asset')
        if active_id:
            asset = self.env['account.asset'].browse(active_id)
            return asset.currency_id
        else:
            active_id = self._context.get('allowed_company_ids')[0]
            company = self.env['res.company'].browse(active_id)
            return company.currency_id

    def _default_amount(self):
        asset = self.env['account.asset'].browse(self._context.get('current_asset'))
        return asset.book_value

    ns_currency = fields.Many2one('res.currency', string="Currency", default=_compute_currency)
    ns_dispose_difference = fields.Monetary("Dispose Different", compute="_calculate_difference", 
                            currency_field="ns_currency", readonly=True)
    ns_disposal_account = fields.Many2one('account.account', string="Post Difference in", 
                        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", readonly=False)
    ns_label = fields.Char("Label", default="Write-Off")
    ns_dispose_amount = fields.Monetary("Amount", default=_default_amount, currency_field="ns_currency")

    @api.depends('ns_dispose_amount')
    def _calculate_difference(self):
        asset = self.env['account.asset'].browse(self._context.get('active_id'))
        value = asset.book_value - self.ns_dispose_amount
        if value < 0:
            raise exceptions.ValidationError(_('Amount Must Be Smaller Than The Initial Depriciable Value.'))
        self.ns_dispose_difference = value
    
    @api.constrains('ns_dispose_difference')
    def _check_value(self):
        if self.ns_dispose_difference < 0:
            self.dispose_amount = 0
            raise exceptions.ValidationError(_('Enter Value Between 0-100.'))

    def do_action(self):
        self.ensure_one()
        invoice_line = self.env['account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
        amount = self.ns_dispose_difference
        label = self.ns_label
        disposal_account = self.ns_disposal_account.id
        return self.with_context(amount=amount, label=label, disposal_account=disposal_account).asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ns_expenses_journal = fields.Boolean('Expenses Journal', default=False)

    @api.constrains('ns_expenses_journal')
    def _another_expenses_journal(self):
        journals = self.env['account.journal'].search([('company_id', '=', self.company_id.id), ('type', '=', 'purchase'), ('id', '!=', self.id)])
        if self.ns_expenses_journal:
            for journal in journals:
                if journal.ns_expenses_journal:
                    raise exceptions.UserError(_("There is already another registered expenses journal for this company!"))

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('journal_id')
    def _get_expenses_journal(self):
        if self.journal_id.ns_expenses_journal:
            self.ns_have_expenses_journal = True
            return
        self.ns_have_expenses_journal = False

    ns_have_expenses_journal = fields.Boolean(string="have expense", compute=_get_expenses_journal)
    