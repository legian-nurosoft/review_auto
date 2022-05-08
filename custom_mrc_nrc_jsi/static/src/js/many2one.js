odoo.define('custom_mrc_nrc_jsi.many2one', function (require) {
"use strict";
	var relational_fields = require('web.relational_fields');
    var session = require('web.session');
    var can_edit = false;
    session.user_has_group('account.group_account_user').then(function(has_group){
        can_edit = has_group;
    });
    var many2one = relational_fields.FieldMany2One.include({
    	init: function (parent, name, record, options) {
            options = options || {};
            this._super.apply(this, arguments);
            var self = this;
            if(this.field.relation == 'res.partner'){
                this.can_create = false;
                this.nodeOptions.no_quick_create = true;
                this.nodeOptions.no_create_edit = true;
                this.can_write = can_edit;
            }            
        }
    });    
});