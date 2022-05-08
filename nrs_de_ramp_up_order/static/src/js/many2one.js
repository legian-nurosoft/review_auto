odoo.define('nrs_de_ramp_up_order.many2one', function (require) {
"use strict";
	var relational_fields = require('web.relational_fields');
    var dialogs = require('web.view_dialogs');
    var core = require('web.core');
    
    var _t = core._t;
    
    var many2one = relational_fields.FieldMany2One.include({
        _open_ns_pop_up: function () {
            if (!this.value) {
                this.activate();
                return;
            }
            var self = this;
            var context = this.record.getContext(this.recordParams);
            this._rpc({
                    model: this.field.relation,
                    method: 'get_formview_id',
                    args: [[this.value.res_id]],
                    context: context,
                })
                .then(function (view_id) {
                    new dialogs.FormViewDialog(self, {
                        res_model: self.field.relation,
                        res_id: self.value.res_id,
                        context: context,
                        title: _t("Open: ") + self.string,
                        view_id: view_id,
                        readonly: true
                    }).open();
                });
        },
    	_onClick: function (event) {
            var self = this;
            if (this.mode === 'readonly' && !this.noOpen) {
                event.preventDefault();
                event.stopPropagation();
                var context = this.record.getContext(this.recordParams);
                if('ns_open_pop_up' in context){
                    self._open_ns_pop_up();
                }else{
                    self._super.apply(this, arguments);
                }
                
            }
        },
    });    
});