odoo.define('custom_mrc_nrc_jsi.form_list_controller', function (require) {
"use strict";
	var FormController = require('web.FormController');
    var ListController = require('web.ListController');
    var KanbanController = require('web.KanbanController');

    var session = require('web.session');
    var can_edit = false;
    session.user_has_group('account.group_account_user').then(function(has_group){
        can_edit = has_group;
    });
    
    var FormControllerInherit = FormController.include({
    	init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            var self = this;
            if(this.modelName == 'res.partner'){
                var can_create = 'disabled_select_radio' in this.model.loadParams.context ? true : false;
                if(!can_create){
                    this.activeActions.create = false;
                    this.activeActions.delete = false;
                    this.activeActions.duplicate = false;
                    this.activeActions.edit = can_edit;
                    
                }
            }
        }
    }); 

    var ListControllerInherit = ListController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            var self = this;
            if(this.modelName == 'res.partner'){
                var can_create = 'disabled_select_radio' in this.model.loadParams.context ? true : false;
                if(!can_create){
                    this.activeActions.create = false;
                    this.activeActions.delete = false;
                    this.activeActions.duplicate = false;
                    this.activeActions.edit = can_edit;
                    
                }
            }
        }
    }); 

    var KanbanControllerInherit = KanbanController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            var self = this;
            if(this.modelName == 'res.partner'){
                var can_create = 'disabled_select_radio' in this.model.loadParams.context ? true : false;
                if(!can_create){
                    this.activeActions.create = false;
                    this.activeActions.delete = false;
                    this.activeActions.duplicate = false;
                    this.activeActions.edit = can_edit;
                    
                }
            }
        }
    });    
});