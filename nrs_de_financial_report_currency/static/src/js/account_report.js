odoo.define('nrs_de_financial_report_currency.account_report', function (require) {
'use strict';
	var account_report = require('account_reports.account_report');
	var core = require('web.core');
	var QWeb = core.qweb;
	var _t = core._t;

	account_report.include({
		unfold: function(line) {
			var self = this;			
			var parent_result = this._super.apply(this, arguments);
			var line_id = line.data('id');
	        this.$el.find('tr[data-parent-id="'+$.escapeSelector(String(line_id))+'"]').each(function(){
	        	var current_id = $(this).find('td').data('id');
	        	$('tr[data-parent-id="'+$.escapeSelector(String(current_id))+'"]').each(function(){
	        		var child_id = $(this).find('td').data('id');
	        		if(child_id && child_id.indexOf('ns_analytic_account_id_') >= 0){
	        			$(this).show();
	        		}
	        	})
	        })

	        return parent_result;
		}
	});
});