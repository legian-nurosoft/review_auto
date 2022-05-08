odoo.define('nrs_de_portal.web_contact', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var utils = require('web.utils');
    var core = require('web.core');
    var qweb = core.qweb;


    publicWidget.registry.deContact = publicWidget.Widget.extend({
        selector: ".de-web-contact",
        events: {
            'click .de-search-close': 'refreshContact',
            'keydown .de-search-input': 'updateContact'         
        },
        xmlDependencies: [
            '/nrs_de_portal/static/src/xml/contact.xml'
        ],
        start: function () {
            this._super.apply(this, arguments);
            var self = this;

            this._rpc({
                route: '/address/operation-site',
                params: {
                    no_login: true
                }
            }).then(function(result){
                self.$el.find(".de-portal-content").append($(qweb.render("nrs_de_portal.de_contact_container",result)));                 

                $(".de-map-marker-box").click(function(e){
                    var id = $(e.currentTarget).data("c-id");
                    var name = $(e.currentTarget).children("text").attr('id');
                    $(".de-search-input").val(name)
                    self._rpc({
                        route: '/search/operation-site',
                        params: {
                            country: id,
                            no_login: true
                        }
                    }).then(function(result){
                        $(".de-contact-list").empty();
                        $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
                    });
                });
            });
        },
        updateContact: function(e){
        	if(e.which == 13){
        		var self = this;
	            self._rpc({
	                route: '/search/operation-site',
	                params: {
	                    keyword: $(".de-search-input").val(),
                        no_login: true
	                }
	            }).then(function(result){
	                $(".de-contact-list").empty();
	                $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
	            });
        	}            
        },
        refreshContact: function(){
        	var self = this;
        	this.$el.find(".de-search-input").val("");
        	self._rpc({
	                route: '/search/operation-site',
	                params: {
	                    keyword: $(".de-search-input").val(),
                        no_login: true
	                }
	            }).then(function(result){
	                $(".de-contact-list").empty();
	                $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
	            });
        }
    });
});