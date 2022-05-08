from odoo import api, models, api, exceptions, fields

class SettingPeriod(models.TransientModel):
	_inherit = 'res.config.settings'

	nrs_period13 = fields.Boolean('Period 13')
	
	@api.model
	def get_values(self):
		res = super(SettingPeriod, self).get_values()
		res.update(
			nrs_period13 = self.env['ir.config_parameter'].sudo().get_param('nrs_de_period_13.nrs_period13')
		)
		return res
	

	def set_values(self):
		super(SettingPeriod, self).set_values()
		param = self.env['ir.config_parameter'].sudo()
		
		field1 = self.nrs_period13 or False
		
		param.set_param('nrs_de_period_13.nrs_period13', field1)

 