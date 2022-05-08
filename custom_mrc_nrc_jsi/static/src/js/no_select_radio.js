odoo.define('custom_mrc_nrc_jsi.no_select_radio', function (require) {
"use strict";
	var relational_fields = require('web.relational_fields');
    var registry = require('web.field_registry');
    var core = require('web.core');
    var qweb = core.qweb;

    var no_select_radio = relational_fields.FieldRadio.extend({
    	 _renderEdit: function () {
            var self = this;
            var currentValue;
            var can_edit = 'disabled_select_radio' in self.record.context ? false : true;
            
            if (this.field.type === 'many2one') {
                currentValue = this.value && this.value.data.id;
            } else {
                currentValue = this.value;
            }
            this.$el.empty();
            this.$el.attr('role', 'radiogroup')
                .attr('aria-label', this.string);
            _.each(this.values, function (value, index) {
                self.$el.append(qweb.render('FieldRadio.button_no_select', {
                    checked: value[0] === currentValue,
                    id: self.unique_id + '_' + value[0],
                    index: index,
                    name: self.unique_id,
                    value: value,
                    can_edit: can_edit
                }));
            });
        },
    });

    var no_contact_radio = relational_fields.FieldRadio.extend({
         _renderEdit: function () {
        var self = this;
        var currentValue;
        if (this.field.type === 'many2one') {
            currentValue = this.value && this.value.data.id;
        } else {
            currentValue = this.value;
        }
        this.$el.empty();
        this.$el.attr('role', 'radiogroup')
            .attr('aria-label', this.string);
        _.each(this.values, function (value, index) {
            if(value[0] != 'contact'){
                self.$el.append(qweb.render('FieldRadio.button', {
                    checked: value[0] === currentValue,
                    id: self.unique_id + '_' + value[0],
                    index: index,
                    name: self.unique_id,
                    value: value,
                }));
            }            
        });
    },
    });

    registry
        .add('no_contact_radio', no_contact_radio)
        .add('no_select_radio', no_select_radio);
});