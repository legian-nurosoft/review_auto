odoo.define('nrs_de_edit_access_right.form_controller', function (require) {
"use strict";
	var FormController = require('web.FormController');

    var session = require('web.session');
        
    var FormControllerInherit = FormController.include({
    	_getPagingInfo: function () {
            var self = this;
            if(self.modelName == 'sale.order' || self.modelName == 'crm.lead'){
                var record = this.model.get(this.handle);
                if(!record['data']['ns_can_edit']){
                    if(self.$buttons){
                        self.$buttons.find(".o_form_button_edit").addClass('o_hidden');
                    } 
                }else{
                    if(self.is_action_enabled('edit')){
                        if(self.$buttons){
                            self.$buttons.find(".o_form_button_edit").removeClass('o_hidden');       
                        }                        
                    }                    
                }
            }else{
                if(self.is_action_enabled('edit')){
                    if(self.$buttons){
                        self.$buttons.find(".o_form_button_edit").removeClass('o_hidden');        
                    }                    
                }
            }
            return this._super.apply(this, arguments);
        }
    });  
});