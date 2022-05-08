odoo.define('nrs_de_portal.dashboard', function (require) {
    'use strict';
    
        var publicWidget = require('web.public.widget');
        var crashManagerWeb = require('web.CrashManager').CrashManager;
        var ErrorDialog = require('web.CrashManager').ErrorDialog;
        var emojis = require('nrs_de_portal.emojis');
        var ErrorDialogRegistry = require('web.ErrorDialogRegistry');
        var utils = require('web.utils');
        var core = require('web.core');
        var _t = core._t;
        var _lt = core._lt;
        var qweb = core.qweb;
        var session = require('web.session');
        var user = session
        var active =true ;

        // override web.crash manager for modify pop up error massage
        var CrashManagerWeb = crashManagerWeb.include({
            show_error: function (error) {
                var self =this
              
                
                error.traceback = error.data.debug;
                var dialogClass = error.data.context && ErrorDialogRegistry.get(error.data.context.exception_class) || ErrorDialog;
                var dialog = new dialogClass(this, {
                    title: _.str.capitalize(error.type) || _t("Odoo Error"),
                }, error);
              
        
                // When the dialog opens, initialize the copy feature and destroy it when the dialog is closed
                var $clipboardBtn;
                var clipboard;
                dialog.opened(function () {
                    // When the full traceback is shown, scroll it to the end (useful for better python error reporting)
                    dialog.$(".o_error_detail").on("shown.bs.collapse", function (e) {
                        e.target.scrollTop = e.target.scrollHeight;
                    });
        
                    $clipboardBtn = dialog.$(".o_clipboard_button");
                    $clipboardBtn.tooltip({title: _t("Copied !"), trigger: "manual", placement: "left"});
                    clipboard = new window.ClipboardJS($clipboardBtn[0], {
                        text: function () {
                            return (_t("Error") + ":\n" + error.message + "\n\n" + error.data.debug).trim();
                        },
                        // Container added because of Bootstrap modal that give the focus to another element.
                        // We need to give to correct focus to ClipboardJS (see in ClipboardJS doc)
                        // https://github.com/zenorocha/clipboard.js/issues/155
                        container: dialog.el,
                    });
                    clipboard.on("success", function (e) {
                        _.defer(function () {
                            $clipboardBtn.tooltip("show");
                            _.delay(function () {
                                $clipboardBtn.tooltip("hide");
                            }, 800);
                        });
                    });
                });
                dialog.on("closed", this, function () {
                    $clipboardBtn.tooltip('dispose');
                    clipboard.destroy();
                });
        
              return  this._rpc({
                    route: '/check/user/type'
                }).then(function(res){
                    if (!res.result) {
                        return  self._displayWarning('An error occurred, please contact IOC for help', 'Warning Errors');
                    }
                    return dialog.open();
                });
              
            },
        
        });

        var TRANSLATE_TERM = {
            empty_a_side_service_id : _lt('A-Side Service ID is a required field. Please select the A-Side Service ID.'),
            empty_fault_type : _lt('Type of Fault is a required field. Please select the Type of Fault.'),
            empty_osite : _lt('Operation Site is a required field. Please select the Operation Site.'),
            empty_service_id : _lt('Service ID is a required field. Please select the Service ID.'),
            empty_ticket_id : _lt('Ticket Type is a required field. Please select the Ticket Type.'),
            empty_z_side_service_id : _lt('Z-Side Service ID is a required field. Please enter the Z-Side Service ID.'),
            empty_visit_type : _lt('Visit Type is a required field. Please select the Visit Type.'),
            empty_visitor_name : _lt(`Visitor's Name is a required field. Please enter the Visitor's Name.`),
            empty_shipping_type: _lt('Shipping Type is a required field. Please select the Shipping Type.'),
            invalid_date_format : _lt('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.'),
            handling_instruction_service_area : _lt('(Please make sure these items can fit into your service area; otherwise, special handling charges may apply or your items can be returned to sender at your expenses.)'),
            handling_instruction_temporary_storage: _lt('(Please confirm with operations for availability and maximum free storage days. Your items can be returned to sender at your expenses or storage fees can apply.)'),
            invalid_z_side_service_id : _lt('Invalid Service ID. Please enter valid Z-Side Service ID.'),
            tooltip_fault_report_visitor_name: _lt(`Please write down the visitor's name as is written in ID document that they will bring on the visit date`),
            label_curency_cny : _lt('CNY'),
            label_curency_idr : _lt('IDR'),
            label_curency_jpy : _lt('JPY'),
            label_curency_krw : _lt('KRW'),
            label_curency_usd : _lt('USD'),
            label_interconnect : _lt('Interconnect'),
            label_managed_services : _lt('Managed Services'),
            label_power : _lt('Power'),
            label_price_cny_per_hour : _lt('CNY / HOUR'),
            label_price_idr_per_hour : _lt('IDR / HOUR'),
            label_price_jpy_per_hour : _lt('JPY / HOUR'),
            label_price_krw_per_hour : _lt('KRW / HOUR'),
            label_price_usd_per_hour : _lt('USD / HOUR'),
            label_space : _lt('Space'),
            mrc_product_unavailable : _lt('The MRC Product is not available. Please ensure you have selected the correct Service and Media Type'),
            nrc_product_unavailable : _lt('The NRC Product is not available. Please ensure you have selected the correct Service and Media Type'),
            status_ticket_approved_inbound: _lt('Approved (Inbound)'),
            status_ticket_approved_outbound: _lt('Approved (Outbound)'),
            status_ticket_approved: _lt('Approved'),
            status_ticket_arrived: _lt('Arrived'),
            status_ticket_cancelled: _lt('Cancelled'),
            status_ticket_closed: _lt('Closed'),
            status_ticket_completed : _lt('Completed'),
            status_ticket_declined: _lt('Declined'),
            status_ticket_dispatched: _lt('Dispatched'),
            status_ticket_escalate: _lt('Escalate'),
            status_ticket_fix: _lt('Fix'),
            status_ticket_in_progress : _lt('In Progress'),
            status_ticket_new: _lt('New'),
            status_ticket_pending_customer : _lt('Pending Customer'),
            status_ticket_resolved: _lt('Resolved'),
            status_ticket_scheduled : _lt('Scheduled'),
            status_ticket_unassigned : _lt('Unassigned'),
            success_submit_ticket : _lt(`Your ticket "_t_ticket_name" was submitted successfully and we will be in touch with you soon.`),
        }
    
        publicWidget.registry.dePortal = publicWidget.Widget.extend({
            selector: ".de-portal",
            events: {
                'click .de-menu-parent': 'showChildMenu',
                'click .de-menu-item': 'actionMenuItem',
                'click .de-user-burger': 'showUserOption',
                'click .de-dialog-close': 'closeDialog',
                'click .de-dialog-btn-confirm': 'confirmDialog',
                'click .de-show-company': 'showCompany',
                'click .de-show-language': 'showLanguage',
                'click .de-select-language': 'changeLanguage',
                'click .de-user-company': 'updateCompanySelection',
                'click .de-btn-edit-user': 'loadEditUserView',
                'click .de-master-user-row': 'showSelectedUser',
                'click .de-btn-cancel': 'actionCancelForm',
                'click .de-btn-save': 'actionSaveForm',
                'click .de-btn-resolved': 'actionResolved',
                'click .de-btn-reset-new': 'actionReset',
                'click .de-btn-delete': 'actionDeleteForm',
                'click .de-access-right-item': 'changeUserAccessRight',
                'click .de-portal-order': 'actionOrderListView',
                'click .de-search-close': 'actionRemoveKeyword',
                'click .de-chip-delete': 'deleteChip',
                'click .de-trigger-selector': 'triggerSelector',
                'click .de-selector-item': 'selectSelectorItem',
                'click .de-portal-download': 'actionDownloadFile',
                'click .de-ticket-list-box, .de-ticket-list-table-tr': 'openTicket',
                'click .de-btn-edit': 'openFormEdit',
                'click .de-installed-new-ticket': 'actionShowTicketButton',
                'click .de-intalled-new-fault-ticket': 'actionNewFaultReport',
                'click .de-intalled-new-shipment': 'actionNewShipment',
                'click .de-intalled-new-remote-hands': 'actionNewRemoteHands',
                'click .de-show-password': 'showPassword',
                'click .de-notification-minimize': 'minimizeNotificationBox',
                'click .de-message-document a': 'openDocument',
                'click .de-notification-hide': 'hideNotificationBox',
                'click .de-message-hide': 'hideMessageBox',
                'click .de-ticket-log-chat-button': 'replyTicketMessage', 
                'click .de-ticket-log-file-delete': 'deleteTicketFile',
                'click .de-ticket-log-file-emoji': 'showEmoji',   
                'click .de-emoji': 'selectEmoji',        
                'click .de-faq-header': 'updateAccordionView',
                'click .de-2fa-button': 'action2FA',
                'click .de-portal-logout': 'actionLogout',
                'change .de-image-input': 'updateUserPhoto',
                // 'change .de-partner-id': 'partnerIDChanged',
                'change .de-osite': 'operationSiteChanged',
                'change .de-service-id': 'serviceIDChanged',
                'change .de-service-id-z, .de-service-id-z-select': 'serviceIDZChanged',
                'change .de-ticket-log-file': 'selectTicketAttachment',
                'change input': 'updateInputColor',
                'change select': 'updateInputColor',
                'change textarea': 'updateInputColor',
                'input .datetimepicker-input': 'updateInputColor',
                'keydown .de-search-input': 'actionSearchListView',                
                'click .add-visitor-btn': 'addVisitorInput',        
                'click .remove-visitor-btn': 'removeVisitorInput',        
                'click .de-pagination-prev': 'actionPaginationPrev',           
                'click .de-pagination-next': 'actionPaginationNext',     
                'click .de-service-selection-popup-table-tr': 'servicePopupSelect',     
                'click .de-service-z-selection-popup-table-tr': 'serviceZPopupSelect',     
                'click .de-agreement-icon-edit': 'changePrivacyPolicyAgreement',     
                'click .de-btn-filter-inactive-user': 'masterUserFilterInactive',  
                'click .de-table-add-line': 'addTableLine',
                'click .de-remove-table-line': 'removeTableLine',
                'change .detail-weight-id': 'uomChanged',
                'click .de-uom-selection-popup-table-tr': 'uomPopupSelect',
            },
            xmlDependencies: [
                '/nrs_de_portal/static/src/xml/dashboard.xml',
                '/nrs_de_portal/static/src/xml/order.xml',
                '/nrs_de_portal/static/src/xml/ticket.xml',
                '/nrs_de_portal/static/src/xml/user.xml',
                '/nrs_de_portal/static/src/xml/invoice.xml',
                '/nrs_de_portal/static/src/xml/contact.xml',
                '/nrs_de_portal/static/src/xml/documents.xml',
            ],
            route: {},
            activeRoute: {},
            start: function () {
                this._super.apply(this, arguments);
                var self = this;
                self.updateCompanyName();
                var new_cookies = [];
                $(document.body).click( function() {
                    
                    if(!$(".de-user-menu-box").hasClass("de-hide")){
                        $(".de-user-menu-box").addClass("de-hide");
                    }
                    $(".de-selector-container").addClass("de-hide");
                    $(".de-trigger-selector").removeClass("de-user-gray-no-border");
                   
                });  
                var check_window =  function(e){
                    var window_width = $(window).outerWidth() 

                    if (window_width < 768){ 
                        if(!$(".de-user-company-box-mobile span").length ){                   
                            $(".de-user-company-box").children().appendTo('.de-user-company-box-mobile')
                        }
                    }else{
                        if($(".de-user-company-box-mobile span").length){
                            $(".de-user-company-box-mobile").children().appendTo('.de-user-company-box')
                        }
                    }
                }

                $(window).on('resize', check_window)

                check_window()
                                   
                $(".de-company-active").each(function(){
                    if(!$(this).hasClass("de-hide")){
                        new_cookies.push($(this).parent().data(("company-id")));
                    }
                });
                
                utils.set_cookie('acids',new_cookies.join(","));
                this._rpc({
                    route: '/portal/update-acids'
                }).then(function(result){
                    $(".de-language-name").text(result['selected_language']);
                });

                this._rpc({
                    route: '/user/route'
                }).then(function(result){
                    self.route = result;
                    console.log("result")
                    console.log(result)

                    self.updateMainView(); 
                });
                   
                self._rpc({
                    route: '/user/prepare-2fa-popup',
                }).then(function(result){
                    if(result['display_message']){                  
                        self.closeDialog();
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_2fa_wizard_popup",{'data': result})));
                        $(".de-tooltips-popover").popover({
                            'container': $('.de-user-info-box'),
                            'content' : 'The portal is compatible with any TOTP capable client such as Google Authenticator or Microsoft Authenticator. Password managers also commonly include FA support. Please follow the instructions on screen to register your authenticator client with the system. <a href="/customer-portal-user-guide?page=3" target="_blank">Read More...</a>',
                            'html': true,
                            'animation': false
                        }).on("mouseenter", function() {
                            var _this = this;
                            $(this).popover("show");
                            $(".popover").on("mouseleave", function() {
                                $(_this).popover('hide');
                            });
                        }).on("mouseleave", function() {
                            var _this = this;
                            setTimeout(function() {
                                if (!$(".popover:hover").length) {
                                $(_this).popover("hide");
                                }
                            }, 300);
                        });
                        $(".de-close-2fa-popup").click(function(e){
                            var dont_show_message = $('#dont_show_message_2fa').prop('checked')
                            if (dont_show_message){                                    
                                self._rpc({
                                    route: '/user/disable-message-2fa-popup'
                                })
                            }
                        })                      
                        
                    }
                });
                
    
                $(document.body).on('click', function(e){ if (!$(e.target).is('.de-show-company,.de-show-language') && !$(e.target).closest('.de-show-company,.de-show-language').length) $('.de-selected-company, .de-language-selected').click(); });
                
                $('.de-trigger-sidebar').on('click', function() {
                    $('.de-portal-sidebar').toggleClass("show");
                });
                
                $('.de-portal-sidebar-backdrop').on('click', function() {
                    $('.de-portal-sidebar').removeClass("show");
                });

                $('.carousel').carousel()
                
                // $(".load-logo").attr("src", "/nrs_de_portal/static/src/img/portal_logo.png");
                //chuanjun website
                // this._rpc({
                //     route: '/get-url-settings'
                // }).then(function(result){
                //     console.log('result => ', result)
                //     var chuanjun_domain = result['chuanjun_domain']
                //     if (chuanjun_domain && chuanjun_domain != ''){
                //         $(".load-logo").attr("src", "nrs_de_portal/static/src/img/chuanjun_logo.png");
                //     }else{
                //         $(".load-logo").attr("src", "nrs_de_portal/static/src/img/portal_logo.png");
                //     }
                // });              
            },
            updateCompanyName: function(){
                var firstCompany = _t('Select Company');
                var count = 0;
                var default_company = ''
                var is_default_company_selected = false
    
                this._rpc({
                    route: '/user'
                }).then(function(result){
                    default_company = result.company_name
                    $(".de-company-active").each(function(){
                        if(!$(this).hasClass("de-hide")){
                            if(count == 0){
                                firstCompany = $(this).parent().data(("company-name"));
                            }
                            if ($(this).parent().data(("company-name")) == default_company){
                                is_default_company_selected = true
                            }
                            count += 1;
                        }
                    });                
    
                    if(count > 1){
                        firstCompany += ' + ' + (count -1) + _t(' more')
                        default_company += ' + ' + (count -1) + _t(' more')
                    }
    
                    if(is_default_company_selected){
                        $(".de-company-name").text(default_company);
                    }else{
                        $(".de-company-name").text(firstCompany);
                    }
                });
            },
            updateMainView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let menu_id = urlParams.get('menu_id') || 'dashboard';
                if(!this.route[menu_id]){
                    menu_id = 'dashboard';
                    window.location.hash = '#menu_id=dashboard';
                }            
                this.activeRoute =  this.route[menu_id];
                this.$el.find(".de-portal-title h1").text(_t(this.activeRoute.title));

                console.log("_t(this.route[menu_id].title)")
                console.log(_t(this.route[menu_id].title))

                console.log("_t(this.activeRoute.title)")
                console.log(_t(this.activeRoute.title))
    
                this.$el.find(".de-breadcrumb-box").empty();
                var breadcrums = this.activeRoute.breadcumb;
                for(var i = 0; i < breadcrums.length; i++){
                    breadcrums[i] = _t(breadcrums[i]);
                }
                this.$el.find(".de-breadcrumb-box").append($(qweb.render("nrs_de_portal.de_breadcrumb",{'breadcrums': breadcrums})));
    
                // this.$el.find(".de-portal-content").empty();
                this.$el.find(".de-portal-content").html(`<div class="loader"></div>`);
                this[this.activeRoute.action]();
                this.updateActiveMenu();
    
            },
            updateActiveMenu: function(){
                var self = this;
                $(".de-menu-level-1").removeClass("de-menu-active");
                $(".de-menu-level-2").removeClass("de-menu-active"); 
                $(".de-menu-level-3").removeClass("de-menu-active");    
                this.$el.find(".de-menu-item").each(function(){
                    if($(this).data('menu-id') == self.activeRoute.menu_id){
                        $(this).addClass("de-menu-active");
                        if($(this).hasClass("de-menu-level-2")){
                            $(this).parent().parent().prev().addClass("de-menu-active");
                            $(this).parent().parent().removeClass("de-hide");
                        }
                        if($(this).hasClass("de-menu-level-3")){
                            $(this).parent().parent().prev().addClass("de-menu-active");
                            $(this).parent().parent().removeClass("de-hide");
                            $(this).parent().parent().parent().parent().prev().addClass("de-menu-active");
                            $(this).parent().parent().parent().parent().removeClass("de-hide");
                        }
                    }else{
                        $(this).removeClass("de-menu-active");                    
                    }
                });
    
                this.updateParentMenuIcon();

                $(".de-tooltips-popover-navbar").popover({
                    'container': $('.de-user-box'),
                    'content' : 'If you are not seeing something you expect to see, please check if the correct company is selected in the User Profile menu. <a href="/customer-portal-user-guide?page=5" target="_blank">Read More...</a>',
                    'html': true,
                    'animation': false
                }).on("mouseenter", function() {
                    var _this = this;
                    $(this).popover("show");
                    $(".popover").on("mouseleave", function() {
                        $(_this).popover('hide');
                    });
                }).on("mouseleave", function() {
                    var _this = this;
                    setTimeout(function() {
                        if (!$(".popover:hover").length) {
                        $(_this).popover("hide");
                        }
                    }, 300);
                });

                $(".de-close-2fa-popup").click(function(e){
                    var dont_show_message = $('#dont_show_message_2fa').prop('checked')
                    if (dont_show_message){                                    
                        self._rpc({
                            route: '/user/disable-message-2fa-popup'
                        })
                    }
                })
                
            },
            showPassword: function(e){
                if($(e.currentTarget).hasClass('de-ic-eyes-slash')){
                    $(e.currentTarget).prev(".de-password").prop('type','text');
                    $(e.currentTarget).removeClass('fa-eye-slash');
                    $(e.currentTarget).addClass('fa-eye');
                }else{
                    $(e.currentTarget).prev(".de-password").prop('type','password');
                    $(e.currentTarget).removeClass('fa-eye');
                    $(e.currentTarget).addClass('fa-eye-slash');
                }
            },
            showUserOption: function(e){
                e.stopPropagation();
                if($(".de-user-menu-box").hasClass("de-hide")){
                    $(".de-user-menu-box").removeClass("de-hide");
                }else{
                    $(".de-user-menu-box").addClass("de-hide");
                    $(".de-user-show-company").removeClass("de-select-company");
                    if(!$(".de-user-company-box").hasClass("de-hide")){
                        $(".de-user-company-box").addClass("de-hide");
                    }
                }
            },
            showCompany: function(e){
                if($(".de-show-company").hasClass("de-selected-company")){
                    $(".de-show-company").removeClass("de-selected-company");
                    $(".de-user-company-box").addClass("de-hide");
                }else{
                    $(".de-show-company").addClass("de-selected-company");
                    $(".de-user-company-box").removeClass("de-hide");
                    if($(".de-show-language").hasClass("de-language-selected")){
                        $(".de-show-language").removeClass("de-language-selected");
                        $(".de-language-box").addClass("de-hide");
                    }
                }
            },
            showLanguage: function(e){
                if($(".de-show-language").hasClass("de-language-selected")){
                    $(".de-show-language").removeClass("de-language-selected");
                    $(".de-language-box").addClass("de-hide");
                }else{
                    $(".de-show-language").addClass("de-language-selected");
                    $(".de-language-box").removeClass("de-hide");
                    if($(".de-show-company").hasClass("de-selected-company")){
                        $(".de-show-company").removeClass("de-selected-company");
                        $(".de-user-company-box").addClass("de-hide");
                    }
                }
            },
            changeLanguage: function(e){
                var lang = $(e.currentTarget).data("lang-code");
                window.location = '/' + lang + '/portal' + window.location.hash;
            },
            updateCompanySelection: function(e){
                var self = this;
                
                var active_companies = utils.get_cookie('acids').split(",");
                for(var i = 0; i < active_companies.length; i++){
                    active_companies[i] = parseInt(active_companies[i])
                }
                
                if(active_companies.indexOf($(e.currentTarget).data("company-id")) >= 0){
                    $(e.currentTarget).children(".de-company-active").addClass("de-hide");
                }else{
                    $(e.currentTarget).children(".de-company-active").removeClass("de-hide");
                }
                var new_cookies = [];
                $(".de-company-active").each(function(){
                    if(!$(this).hasClass("de-hide")){
                        new_cookies.push($(this).parent().data(("company-id")));
                    }
                });
                
                utils.set_cookie('acids',new_cookies.join(","));
                this._rpc({
                    route: '/portal/update-acids'
                }).then(function(result){
                    self.updateMainView();
                });
    
                self.updateCompanyName();
            },
            updateParentMenuIcon: function(){
                $(".de-menu-chevron").each(function(){
                    if(!$(this).parent().next().hasClass("de-hide")){
                        $(this).removeClass("fa-chevron-right");
                        $(this).removeClass("fa-chevron-down");
                        $(this).addClass("fa-chevron-down");
                    }else{
                        $(this).removeClass("fa-chevron-right");
                        $(this).removeClass("fa-chevron-down");
                        $(this).addClass("fa-chevron-right");
                    }
                });
                this.closeDropdowns();
            },
            closeSidebar: function(){
                $('.de-portal-sidebar').removeClass('show');
            },
            closeDropdowns: function(){
                $('.de-user-gray-no-border').click();
                $('.de-selected-company, .de-language-selected').click();
            },
            closeDialog: function(e){
                var self = this;                                    
                $(".de-dialog-container").remove();                
            },
            confirmDialog: function(e){
                var self = this;
                if($(e.currentTarget).data("action") == "enable-2fa-popup"){
                    var password = $(".de-user-password").val();
                    var wizard = $(e.currentTarget).data("wizard-id");
                    self._rpc({
                        route: '/user/enable-2fa',
                        params: {to_check: password, wizard_id: wizard}
                    }).then(function(result){
                        self.closeDialog();
                        if(result['status'] == 'allowed'){  
                            self.updateMainView();                      
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }else{                    
                    if(self.activeRoute['menu_id'] == 'user-profile'){
                        var action = $(e.currentTarget).data("action");
                        var password = $(".de-user-password").val();
                        var wizard = $(e.currentTarget).data("wizard-id");
                        if(action == 'enable'){
                            self._rpc({
                                route: '/user/prepare-2fa',
                                params: {to_check: password}
                            }).then(function(result){
                                self.closeDialog();
                                if(result['status'] == 'allowed'){                        
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_2fa_wizard",{'data': result['data']})));                                    
                                    $(".de-tooltips-popover").popover({
                                        'container': $('.de-user-info-box'),
                                        'content' : 'The portal is compatible with any TOTP capable client such as Google Authenticator or Microsoft Authenticator. Password managers also commonly include FA support. Please follow the instructions on screen to register your authenticator client with the system. <a href="/customer-portal-user-guide?page=3" target="_blank">Read More...</a>',
                                        'html': true,
                                        'animation': false
                                    }).on("mouseenter", function() {
                                        var _this = this;
                                        $(this).popover("show");
                                        $(".popover").on("mouseleave", function() {
                                            $(_this).popover('hide');
                                        });
                                    }).on("mouseleave", function() {
                                        var _this = this;
                                        setTimeout(function() {
                                            if (!$(".popover:hover").length) {
                                            $(_this).popover("hide");
                                            }
                                        }, 300);
                                    });

                                    $(".de-close-2fa-popup").click(function(e){
                                        var dont_show_message = $('#dont_show_message_2fa').prop('checked')
                                        if (dont_show_message){                                    
                                            self._rpc({
                                                route: '/user/disable-message-2fa-popup'
                                            })
                                        }
                                    })
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        }else if(action == 'disable'){
                            self._rpc({
                                route: '/user/disable-2fa',
                                params: {to_check: password}
                            }).then(function(result){
                                self.closeDialog();
                                if(result['status'] == 'allowed'){  
                                    self.updateMainView();                      
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        }else if(action == 'confirm'){
                            self._rpc({
                                route: '/user/enable-2fa',
                                params: {to_check: password, wizard_id: wizard}
                            }).then(function(result){
                                self.closeDialog();
                                if(result['status'] == 'allowed'){  
                                    self.updateMainView();                      
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        }              
                        
                    }            
                    if(self.activeRoute['menu_id'] == 'master-user'){
                        if(self.activeRoute['master_user_show_inactive']){
                            self.closeDialog();
                            var partner_id = $(".de-btn-edit-user").data("partner-id");
                            self._rpc({
                                route: '/user/activate',
                                params: {partner_id: partner_id}
                            }).then(function(result){
                                if(result['status'] == 'allowed'){                        
                                    self._rpc({
                                        route: '/user/associated',
                                        params: {
                                            show_inactive: self.activeRoute['master_user_show_inactive']
                                        }
                                    }).then(function(result){
                    
                                        self.$el.find(".de-master-user-left").empty()
                    
                                        var first_partner = result['data']['associated_company'][Object.keys(result['data']['associated_company'])[0]];
                                        self.$el.find(".de-master-user-left").append($(qweb.render("nrs_de_portal.de_portal_user_profile",first_partner)));
                    
                                        self.$el.find(".de_portal_master_user_body").replaceWith($(qweb.render("nrs_de_portal.de_portal_table_master_user_body",result['data'])));
                                        
                                        self.activeRoute['data'] = result['data'];
                                        self.activeRoute['old_data'] = JSON.parse(JSON.stringify(result['data']));
                                    })
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        }else{
                            self.closeDialog();
                            var partner_id = $(".de-btn-edit-user").data("partner-id");
                            self._rpc({
                                route: '/user/delete',
                                params: {partner_id: partner_id}
                            }).then(function(result){
                                if(result['status'] == 'allowed'){                        
                                    self.updateMainView();
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        }
                    }
                }
            },
            actionOrderListView: function(e){
                var self = this;
                var dataOrder = $(e.currentTarget).data('order');
                if($(e.currentTarget).hasClass('fa-chevron-down')){
                    $('.de-portal-order').removeClass('fa-chevron-down');
                    $('.de-portal-order').removeClass('fa-chevron-up');
                    $('.de-portal-order').addClass('fa-chevron-down');
    
                    $(e.currentTarget).removeClass('fa-chevron-down');                
                    $(e.currentTarget).addClass('fa-chevron-up');
    
                    this.activeRoute.order = dataOrder + " DESC";
                }else{
                    $('.de-portal-order').removeClass('fa-chevron-down');
                    $('.de-portal-order').removeClass('fa-chevron-up');
                    $('.de-portal-order').addClass('fa-chevron-down');
    
                    $(e.currentTarget).removeClass('fa-chevron-down'); 
                    $(e.currentTarget).addClass('fa-chevron-down');
                    
                    this.activeRoute.order = dataOrder + " ASC";
                }
    
                this[this.activeRoute.actionListView]();
            },
            actionDownloadFile: function(){
                this[this.activeRoute.actionDownload]();
            },
            actionSearchListView: function(e){
                if(e.which == 13){
                    this.activeRoute.keyword = this.$el.find(".de-search-input").val();
                    this[this.activeRoute.actionListView]();
                }
            },
            actionSetSearchTerm: function(value){
                this.activeRoute.searchTerm = value
                this[this.activeRoute.actionListView]();
            },
            actionRemoveKeyword: function(){
                this.$el.find(".de-search-input").val("");
                this.activeRoute.keyword = "";
                this[this.activeRoute.actionListView]();
            },
            deleteChip: function(e){
                e.preventDefault();
                e.stopPropagation();
                var value = $(e.currentTarget).parent().data("value-id");            
                var trigger = $(e.currentTarget).parent().parent().data("trigger-selector");
                $(trigger + " .de-selector-item").each(function(){
                    if($(this).data("value-id") == value){
                        $(this).removeClass("de-hide");
                    }
                });
    
                $(e.currentTarget).parent().remove();
                if($(".de-chip").length <= 0){
                    $(".de-chip-input").removeClass("de-hide");
                }
            },
            triggerSelector: function(e){
                e.stopPropagation();
                var trigger = $(e.currentTarget).data("trigger-selector");
                $(".de-selector-container").addClass("de-hide");
                $(".de-trigger-selector").removeClass("de-user-gray-no-border");
                if($(trigger).hasClass("de-hide")){
                    $(trigger).removeClass("de-hide");
                    $(e.currentTarget).addClass("de-user-gray-no-border");
                }else{
                    $(trigger).addClass("de-hide");
                    $(e.currentTarget).removeClass("de-user-gray-no-border");
                }
            },
            selectSelectorItem: function(e){
                var trigger = $(e.currentTarget).data("trigger-selector");
                $(e.currentTarget).parent().parent().addClass("de-hide");
                $(trigger).removeClass("de-user-gray-no-border");            
    
                if($(e.currentTarget).hasClass("de-chip-selector-item")){
                    var data = {
                        'id': $(e.currentTarget).data("value-id"), 
                        'name': $(e.currentTarget).text()
                    };
                    $(trigger).append($(qweb.render("nrs_de_portal.de_chip",data)));
                    $(e.currentTarget).addClass("de-hide");
                    $(trigger).children(".de-chip-input").addClass("de-hide");
                }else{
                    $(trigger).children(".de-selector-label").text($(e.currentTarget).text());
                    $(trigger).children(".de-selector-input").val($(e.currentTarget).data("value-id"));
                }            
            },
            actionShowTicketButton: function(e){
                e.preventDefault();
                e.stopPropagation();            
    
                if($(e.currentTarget).next().hasClass("de-hide")){
                    $(e.currentTarget).next().removeClass('de-hide');
                }else{
                    $(e.currentTarget).next().addClass('de-hide');
                }
    
                $(".de-intalled-ticket-box").each(function(){
                    if(!$(this).hasClass("de-hide")){
                        if($(e.currentTarget).data("project-id") != $(this).prev().data("project-id")){
                            $(this).addClass("de-hide");
                        }                    
                    }
                });           
            },
            actionMenuItem: function(e){
                e.preventDefault();
                e.stopPropagation();
    
                let menu_id = $(e.currentTarget).data('menu-id');
                let parent_menu = $(e.currentTarget).data('parent-menu') || false;
                
                if(menu_id in this.route){
                    window.location.hash = '#menu_id=' + menu_id;
                }else{
                    window.location.hash = '#menu_id=dashboard';
                }

                console.log("parent_menu", parent_menu)

                if(parent_menu){
                    this.showChildMenu(e);
                }
    
                this.updateMainView()
                this.closeSidebar();
            },
            showChildMenu: function(e){
                e.preventDefault();
                e.stopPropagation();
    
                if($(e.currentTarget).next(".de-submenu-box").hasClass("de-hide")){
                    $(e.currentTarget).next(".de-submenu-box").removeClass("de-hide");                
                }else{
                    $(e.currentTarget).next(".de-submenu-box").addClass("de-hide");
                    // test
                }
    
                this.updateParentMenuIcon();
                
            },
            arrayToJSON: function(data){
                var temp = {};
                for(var i = 0; i < data.length; i++){
                    temp[data[i]['name']] = data[i]['value']
                }
                return temp;
            },
            loadDashboardView: function(){        
                var self = this;            
                this._rpc({
                    route: '/dashboard'
                }).then(function(result){
                    console.log("result['translated_term']")
                    console.log(result['translated_term'])
                    console.log("_t('Actions')")
                    console.log(_t('Actions'))
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_portal_dashboard",result)));                    
                    // //chuanjun website
                    // $(".load-company").text("Digital Edge");
                    // if (window.location.hostname == "nervous-penguin-39.telebit.io"){
                    //     $(".load-company").text("Chuanjun");
                    // }
                });
            },
            loadUserProfileView: function(){
                var self = this;
                this._rpc({
                    route: '/user'
                }).then(function(result){
                    result['is_user_profile'] = true
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_portal_user_profile",result)));
                    
                    $(".de-tooltips-popover-user-pin-code").popover({
                        'container': $('.de-portal-content-box'),
                        'content' : 'You will require this PIN to request services via non-authenticated channels (e.g. Live chat, Calling into our helpdesk). You may change this PIN to another number or passphrase by clicking Edit. <a href="/customer-portal-user-guide?page=4" target="_blank">Read More...</a>',
                        'html': true,
                        'animation': false
                    }).on("mouseenter", function() {
                        var _this = this;
                        $(this).popover("show");
                        $(".popover").on("mouseleave", function() {
                            $(_this).popover('hide');
                        });
                    }).on("mouseleave", function() {
                        var _this = this;
                        setTimeout(function() {
                            if (!$(".popover:hover").length) {
                            $(_this).popover("hide");
                            }
                        }, 300);
                    });
                    if(result['is_admin']){
                        $(".de-tooltips-popover-user-paa").popover({
                            'container': $('.de-portal-content-box'),
                            'content' : 'Brings up the Access Configuration Screen. <a href="/customer-portal-user-guide?page=7" target="_blank">Read More...</a>',
                            'html': true,
                            'animation': false
                        }).on("mouseenter", function() {
                            var _this = this;
                            $(this).popover("show");
                            $(".popover").on("mouseleave", function() {
                                $(_this).popover('hide');
                            });
                        }).on("mouseleave", function() {
                            var _this = this;
                            setTimeout(function() {
                                if (!$(".popover:hover").length) {
                                $(_this).popover("hide");
                                }
                            }, 300);
                        });
                    }
                });            
            },
            loadMasterUserView: function(){
                var self = this;
                this._rpc({
                    route: '/user/associated',
                    params: {
                        show_inactive: self.activeRoute['master_user_show_inactive']
                    }
                }).then(function(result){
                    if(result['status'] == 'allowed'){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_portal_master_user",{})));
    
                        
                        var first_partner = result['data']['associated_company'][Object.keys(result['data']['associated_company'])[0]];
                        self.$el.find(".de-master-user-left").append($(qweb.render("nrs_de_portal.de_portal_user_profile",first_partner)));
    
                        self.$el.find(".de-master-user-right").append($(qweb.render("nrs_de_portal.de_portal_table_master_user",result['data'])));
                        
                        self.activeRoute['data'] = result['data'];
                        self.activeRoute['old_data'] = JSON.parse(JSON.stringify(result['data']));
                        
                        $('#de-search-input-tags').tagsInput({
                            'onAddTag': function(input, value) {
                                var search_term = []
                                $(".de-search-tag-keyword").each(function() {
                                    var column = $(this).children( ".de-search-tag-column" ).text()
                                    var value = $(this).children( ".de-search-tag-value" ).text()
                                    if (column == "User Name"){
                                        search_term.push('name' + '->' + value)
                                    }else if(column == "Position"){
                                        search_term.push('function' + '->' + value)
                                    }else if(column == "Company"){
                                        search_term.push('parent_id.name' + '->' + value)
                                    }else if(column == "Associated Entities"){
                                        search_term.push('x_studio_associated_company' + '->' + value)
                                    }
                                });
                                self._rpc({
                                    route: '/user/associated',
                                    params: {
                                        search_term: search_term.length > 0 ? search_term.join('|') : false,
                                        show_inactive: self.activeRoute['master_user_show_inactive']
                                    }
                                }).then(function(result){
                                    self.$el.find(".de_portal_master_user_body").replaceWith($(qweb.render("nrs_de_portal.de_portal_table_master_user_body",result['data'])));
                                })
                            },
                            'onRemoveTag': function(input, value) {
                                var search_term = []
                                $(".de-search-tag-keyword").each(function() {
                                    var column = $(this).children( ".de-search-tag-column" ).text()
                                    var value = $(this).children( ".de-search-tag-value" ).text()
                                    if (column == "User Name"){
                                        search_term.push('name' + '->' + value)
                                    }else if(column == "Position"){
                                        search_term.push('function' + '->' + value)
                                    }else if(column == "Company"){
                                        search_term.push('parent_id.name' + '->' + value)
                                    }else if(column == "Associated Entities"){
                                        search_term.push('x_studio_associated_company' + '->' + value)
                                    }
                                });
                                self._rpc({
                                    route: '/user/associated',
                                    params: {
                                        search_term: search_term.length > 0 ? search_term.join('|') : false,
                                        show_inactive: self.activeRoute['master_user_show_inactive']
                                    }
                                }).then(function(result){
                                    self.$el.find(".de_portal_master_user_body").replaceWith($(qweb.render("nrs_de_portal.de_portal_table_master_user_body",result['data'])));
                                })
                                // self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                            },
                            'searchCategory': {
                                source: [
                                    'User Name',
                                    'Position',
                                    'Company',                            
                                    'Associated Entities'
                                ]
                            },
                            'placeholder': _t('search')
                        });
                        
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                    }
                });
            },
            loadAddUserView: function(e){
                var self = this;
                this._rpc({
                    route: '/user/prepare-add'
                }).then(function(result){
                    if(result['status'] == 'allowed'){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_portal_user_add",result['data'])));
                        // $("body").on("DOMSubtreeModified", ".de-trigger-o-site", function() {
                        //     if ( $(this).children().length > 0 ) {
                        //         $(".de-user-id-form").show();
                        //     }else{
                        //         $(".de-user-id-form").hide();
                        //     }
                        // });
                        var temp_pin = "";
                        var possible_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz0123456789";
    
                        for (var i = 0; i < 6; i++)
                            temp_pin += possible_char.charAt(Math.floor(Math.random() * possible_char.length));
    
                        $(".de-user-pin-code-form").val(temp_pin)
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                    }
                });
            },
            showSelectedUser: function(e){
                e.preventDefault();
                e.stopPropagation();
                var self = this;
                $('.selected').removeClass('selected');
                $(e.currentTarget).parent().addClass("selected").siblings().removeClass('selected');
                var partner_id = $(e.currentTarget).parent().data("partner-id");
                for(var i = 0; i < self.activeRoute['data']['associated_company'].length; i++){
                    if(self.activeRoute['data']['associated_company'][i]['partner_id'] == partner_id){
                        self.$el.find(".de-master-user-left").empty();
                        self.$el.find(".de-master-user-left").append($(qweb.render("nrs_de_portal.de_portal_user_profile",self.activeRoute['data']['associated_company'][i])));
                    }
                }
            },
            changeUserAccessRight: function(e){
                e.preventDefault();
                e.stopPropagation();
                var self = this;
                var partner_id = $(e.currentTarget).parent().parent().data("partner-id");
                var access_right = $(e.currentTarget).data("access-right-id");
                if(access_right != "admin"){
                    for(var i = 0; i < self.activeRoute['data']['associated_company'].length; i++){
                        if(self.activeRoute['data']['associated_company'][i]['partner_id'] == partner_id){
                            var can_edit = true;
                            if(self.activeRoute['data']['associated_company'][i]["admin"]){
                                if(!self.activeRoute['data']['associated_company'][i]["active_user"]){
                                    can_edit = false;
                                }
                            }
    
                            if(can_edit){
                                if(self.activeRoute['data']['associated_company'][i][access_right]){
                                    $(e.currentTarget).removeClass("de-access-right-active");
                                    $(e.currentTarget).addClass("de-access-right-inactive");
                                }else{
                                    $(e.currentTarget).removeClass("de-access-right-inactive");
                                    $(e.currentTarget).addClass("de-access-right-active");
                                }
                                self.activeRoute['data']['associated_company'][i][access_right] = !self.activeRoute['data']['associated_company'][i][access_right];
                            }else{
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': "You can not edit the Primary Access Administrator user"})));
                            }
                        }
                    }
                }else{
                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': "You can not edit the Primary Access Administrator access right"})));
                }           
            },
            actionCancelForm: function(e){
                var self = this;
                if(self.activeRoute['menu_id'] == 'master-user'){
                    self.activeRoute['data'] = JSON.parse(JSON.stringify(self.activeRoute['old_data']));
                    self.$el.find(".de-master-user-right").empty();
                    self.$el.find(".de-master-user-right").append($(qweb.render("nrs_de_portal.de_portal_table_master_user",self.activeRoute['old_data'])));
                }else if(self.activeRoute['menu_id'] == 'edit-user-profile'){
                    if($(".de-same-user").val() == 1){
                        window.location.hash = '#menu_id=user-profile';
                    }else{
                        window.location.hash = '#menu_id=master-user';
                    }                
                    self.updateMainView();
                }else if(self.activeRoute['menu_id'] == 'add-user'){
                    window.location.hash = '#menu_id=master-user';
                    self.updateMainView();
                }else if(self.activeRoute['menu_id'] == 'new-fault-report-ticket'){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    window.location.hash = '#menu_id=new-fault-report-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(self.activeRoute['menu_id'] == 'remote-hands'){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    window.location.hash = '#menu_id=remote-hands&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(self.activeRoute['menu_id'] == 'new-site-access-ticket'){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    window.location.hash = '#menu_id=new-site-access-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(self.activeRoute['menu_id'] == 'new-shipment-ticket'){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    window.location.hash = '#menu_id=new-shipment-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }
            },
            actionSaveForm: function(e){
                var self = this;
                self.$el.find(".de-portal-content").append($(qweb.render("nrs_de_portal.de_loading_submit_form")));
                if(self.activeRoute['menu_id'] == 'master-user'){
                    self._rpc({
                        route: '/user/save-associated',
                        params: self.activeRoute['data']
                    }).then(function(result){                        
                        $(".de-loader-dialog").remove();
                        if(result['status'] == 'allowed'){                        
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'edit-user-profile'){
                    var data = $(".de-portal-form").serializeArray();            
                    data = self.arrayToJSON(data);
                    data['companies'] = []
                    data['sites'] = []
    
                    $(".de-trigger-a-company .de-chip").each(function(){
                        data['companies'].push($(this).data("value-id"));
                    });
    
                    $(".de-trigger-o-site .de-chip").each(function(){
                        data['sites'].push($(this).data("value-id"));
                    });
                    
                    this._rpc({
                        route: '/user/save-edit',
                        params: data
                    }).then(function(result){                        
                        $(".de-loader-dialog").remove();
                        if(result['status'] == 'allowed'){
                            if(result['data']['same_user']){
                                var src = $(".de-user-photo img").attr("src");
                                $(".de-user-photo img").attr("src","");
                                $(".de-user-photo img").attr("src",src);                                              
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                
                                if(result['data']['need_login']){
                                    setTimeout(function(){
                                        window.location = '/web/session/logout?redirect=/web/login';
                                    },3000)
                                }else{
                                    window.location.hash = '#menu_id=user-profile';  
                                    self.updateMainView();
                                }
                            }else{
                                window.location.hash = '#menu_id=master-user';  
                                self.updateMainView();
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            }
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'add-user'){
                    var data = $(".de-portal-form").serializeArray();            
                    data = self.arrayToJSON(data);
                    data['companies'] = []
                    data['sites'] = []
    
                    $(".de-trigger-a-company .de-chip").each(function(){
                        data['companies'].push($(this).data("value-id"));
                    });
    
                    $(".de-trigger-o-site .de-chip").each(function(){
                        data['sites'].push($(this).data("value-id"));
                    });
                    
                    this._rpc({
                        route: '/user/save-add',
                        params: data
                    }).then(function(result){                        
                        $(".de-loader-dialog").remove();
                        if(result['status'] == 'allowed'){
                            window.location.hash = '#menu_id=master-user';
                            self.updateMainView();
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'remote-hands'){                    
                    $(".de-order-form-term-dialog").remove();
                    var data = $(".de-portal-form").serializeArray();            
                    data = this.arrayToJSON(data);
                    var ticket_type = $(".de-ticket-type-id").find('option:selected').text();
                    if (ticket_type.trim() == "Regular Remote Hands"){
                        if(data['x_studio_requested_service_date'] == '' || data['x_studio_requested_service_date'] == null){
                            $("#requestdatepicker").click()
                            var now = new Date($("#requestdatepicker").val());
                            now.setHours( now.getHours() + 4 );
                            var addZero = (i) => {
                                if (i < 10) {
                                    i = "0" + i;
                                }
                                return i;
                            }
                            var cur_date = new Date(now);
                            var cur_date_string = cur_date.toISOString().substring(0, 10) + " " + addZero(cur_date.getHours()) + ":" + addZero(cur_date.getMinutes());
                            data['default_requested_date'] = cur_date_string;
                        }
                    }
                    this._rpc({
                        route: '/remote-hands/save',
                        params: data
                    }).then(function(result){
                        $(".de-loader-dialog").remove();
                        if(result['status'] == 'success'){
                            if(data['ticket_id'] > 0){
                                window.location.hash = '#menu_id=remote-hands&action=read&ticket_id=' + data['ticket_id'];
                                self.updateMainView();
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            }else{
                                $(".de-portal-form").find("input[type=text]").val("");
                                $(".de-portal-form").find("textarea").val("");
                                $(".de-portal-form").find("option").prop("selected",false);
                                // $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': TRANSLATE_TERM[result['message']].toString().replace('_t_ticket_name', result['ticket_name'])})));
                                self.getTicketList();
                                $(".de-service-price").text("0 " + _t("USD / Hour"));
                            }                        
                        }else{
                            var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'new-fault-report-ticket'){
                    var data = $(".de-portal-form").serializeArray();            
                    data = this.arrayToJSON(data);
                    this._rpc({
                        route: '/fault-report/save',
                        params: data
                    }).then(function(result){              
                        $(".de-loader-dialog").remove();      
                        if(result['status'] == 'success'){
                            if(data['ticket_id'] > 0){
                                window.location.hash = '#menu_id=new-fault-report-ticket&action=read&ticket_id=' + data['ticket_id'];
                                self.updateMainView();
                                // $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            }else{
                                $(".de-portal-form").find("input[type=text]").val("");
                                $(".de-portal-form").find("textarea").val("");
                                $(".de-portal-form").find("option").prop("selected",false);
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                $(".de-chip-delete").click();
                                self.getTicketList();
                            }
                        }else{
                            var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'new-site-access-ticket'){
                    var data = $(".de-portal-form").serializeArray();            
                    data = this.arrayToJSON(data);
                    data['visit_area'] = []
                    var visitor_name_array = []
                    $(".de-form-input-visitor").each(function(i,e){
                        var visitor_name = $(e).val()
                        if (visitor_name != null && visitor_name != ''){
                            visitor_name_array.push(visitor_name)
                        }
                    })
                    data['x_studio_requested_visitor'] = visitor_name_array.join(", ")
                    $(".de-chip").each(function(){
                        data['visit_area'].push($(this).data("value-id"));
                    });
                    this._rpc({
                        route: '/site-access/save',
                        params: data
                    }).then(function(result){
                        $(".de-loader-dialog").remove();
                        if(result['status'] == 'success'){
                            if(data['ticket_id'] > 0){
                                window.location.hash = '#menu_id=new-site-access-ticket&action=read&ticket_id=' + data['ticket_id'];
                                self.updateMainView();
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            }else{
                                $(".de-portal-form").find("input[type=text]").val("");
                                $(".de-portal-form").find("textarea").val("");
                                $(".de-portal-form").find("option").prop("selected",false);
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                $(".de-chip-delete").click();
                                self.getTicketList();
                            }
                        }else{
                            var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'new-shipment-ticket'){
                    var data = $(".de-portal-form").serializeArray();            
                    data = this.arrayToJSON(data);

                    var temp_shipment_detail = []

                    var invalid_shipment_detail = false

                    $(".shipment-detail-table-row").each(function(i, obj) {

                        var detail_id = $(obj).attr('data-shipment-detail-id')
                        var item_number = 0
                        var dimension = '0'
                        var weight = 0
                        var tracking_number = ''
                        var weight_id = 0

                        var item_number_element = $(obj).find(".detail-item-number")
                        var dimension_element = $(obj).find(".detail-dimension")
                        var weight_element = $(obj).find(".detail-weight")
                        var weight_element_id = $(obj).find(".detail-weight-id")
                        var tracking_number_element = $(obj).find(".detail-tracking-number")

                        if(item_number_element.val() == 0){
                            invalid_shipment_detail = true
                            item_number_element.css("border-color","red")
                        }else{
                            item_number_element.css("border-color","#F0F0F0")
                        }
                        if(dimension_element.val() == ''){
                            invalid_shipment_detail = true
                            dimension_element.css("border-color","red")
                        }else{
                            dimension_element.css("border-color","#F0F0F0")
                        }
                        if(weight_element.val() == 0){
                            invalid_shipment_detail = true
                            weight_element.css("border-color","red")
                        }else{
                            weight_element.css("border-color","#F0F0F0")
                        }
                        if(weight_element_id.val() == ''){
                            invalid_shipment_detail = true
                            weight_element_id.css("border-color","red")
                        }else{
                            weight_element_id.css("border-color","#F0F0F0")
                        }
                        if(tracking_number_element.val() == ''){
                            invalid_shipment_detail = true
                            tracking_number_element.css("border-color","red")
                        }else{
                            tracking_number_element.css("border-color","#F0F0F0")
                        }
                        
                        item_number = item_number_element.val() || 0
                        dimension = dimension_element.val() || ''
                        weight = weight_element.val() || 0
                        weight_id = weight_element_id.val() || 0
                        tracking_number = tracking_number_element.val() || '' 

                        temp_shipment_detail.push({
                            detail_id : detail_id,
                            detail_data : {
                                ns_shipment_detail_item_number: item_number,
                                ns_shipment_detail_dimension: dimension,
                                ns_shipment_detail_weight : weight,
                                ns_shipment_detail_tracking_number: tracking_number,
                                ns_shipment_detail_dispatched : false,
                                ns_uom:parseInt(weight_id),
                                ns_shipment_detail_storage_location : null
                            }
                        })
                    });
                   
                    // if (invalid_shipment_detail){
                    //     $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Invalid shipment detail!')})));
                    // }else if (temp_shipment_detail.length < 1){
                    //     $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Shipment detail must have at least one item!')})));
                    // }else{
                        data['invalid_shipment_detail'] = invalid_shipment_detail
                        data['shipment_detail'] = temp_shipment_detail
                        data['deleted_shipment_detail'] = this.activeRoute['deleted_shipment_detail']
                        this._rpc({
                            route: '/shipment/save',
                            params: data
                        }).then(function(result){
                            $(".de-loader-dialog").remove(); 
                            if(result['status'] == 'success'){
                                if(data['ticket_id'] > 0){
                                    window.location.hash = '#menu_id=new-shipment-ticket&action=read&ticket_id=' + data['ticket_id'];
                                    self.updateMainView();
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }else{
                                    $(".de-portal-form").find("input[type=text]").val("");
                                    $(".de-portal-form").find("textarea").val("");
                                    $(".de-portal-form").find("input[type=number]").val("");
                                    $(".de-portal-form").find("option").prop("selected",false);
                                    $(".de-portal-form").find("input[type=checkbox]").prop("checked",false);
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                    self.getTicketList();
                                }
                            }else{
                                var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                            }
                        });
                }else if(self.activeRoute['menu_id'] == 'interconnection-services'){
                    $(".de-order-form-term-dialog").remove();
                    var data = $(".de-portal-form").serializeArray();
                    data = this.arrayToJSON(data); 

                    this._rpc({
                        route: '/interconnection-service/save',
                        params: data
                    }).then(function(result){
                        $(".de-loader-dialog").remove(); 
                        if(result['status'] == 'success'){
                            $(".de-portal-form").find("input[type=text]").val("");
                            $(".de-portal-form").find("input[type=hidden]").val("");
                            $(".de-portal-form").find("input[type=file]").val("");
                            $(".de-portal-form").find("option").prop("selected",false);
                            $(".de-portal-form").find("input[type=checkbox]").prop("checked",false);
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            $(".de-service-price").text("MRC 0 USD / NRC 0 USD");
                        }else{
                            var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                        }
                    });
                }else if(self.activeRoute['menu_id'] == 'colocation-accessories'){
                    var data = $(".de-portal-form").serializeArray();
                    data = this.arrayToJSON(data);                              
    
                    this._rpc({
                        route: '/colocation_accessories/save',
                        params: data
                    }).then(function(result){
                        $(".de-loader-dialog").remove(); 
                        if(result['status'] == 'success'){
                            $(".de-portal-form").find("input[type=text]").val("");
                            $(".de-portal-form").find("input[type=number]").val("");
                            $(".de-portal-form").find("option").prop("selected",false);
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            $(".de-service-price").text("0 USD / Units");
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }
            },
            actionResolved: function(e){
                var self = this;
                var ticketRoute = [
                    'new-fault-report-ticket',
                    'new-site-access-ticket',
                    'new-shipment-ticket',
                    'remote-hands',
                ];
                if(ticketRoute.indexOf(self.activeRoute['menu_id']) >= 0){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    this._rpc({
                        route: '/ticket/resolved',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'success'){
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            self.getTicketList();

                            if(self.activeRoute['menu_id'] == 'new-fault-report-ticket'){
                                window.location.hash = '#menu_id=new-fault-report-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'remote-hands'){
                                window.location.hash = '#menu_id=remote-hands&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'new-site-access-ticket'){
                                window.location.hash = '#menu_id=new-site-access-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'new-shipment-ticket'){
                                window.location.hash = '#menu_id=new-shipment-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }

                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }
            },
            actionReset: function(e){
                var self = this;
                var ticketRoute = [
                    'new-fault-report-ticket',
                    'new-site-access-ticket',
                    'new-shipment-ticket',
                    'remote-hands',
                ];
                if(ticketRoute.indexOf(self.activeRoute['menu_id']) >= 0){
                    var ticket_id = $(e.currentTarget).data("ticket-id");
                    this._rpc({
                        route: '/ticket/reset',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'success'){
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                            self.getTicketList();

                            if(self.activeRoute['menu_id'] == 'new-fault-report-ticket'){
                                window.location.hash = '#menu_id=new-fault-report-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'remote-hands'){
                                window.location.hash = '#menu_id=remote-hands&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'new-site-access-ticket'){
                                window.location.hash = '#menu_id=new-site-access-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }else if(self.activeRoute['menu_id'] == 'new-shipment-ticket'){
                                window.location.hash = '#menu_id=new-shipment-ticket&action=read&ticket_id=' + ticket_id;
                                self.updateMainView();
                            }

                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    });
                }
            },
            actionDeleteForm: function(e){
                var self = this;
                if(self.activeRoute['menu_id'] == 'master-user'){
                    if(self.activeRoute['master_user_show_inactive']){
                        var partner_id = $(".de-btn-edit-user").data("partner-id");
                        var user_name = "";
                        for(var i = 0; i < self.activeRoute['data']['associated_company'].length; i++){
                            if(self.activeRoute['data']['associated_company'][i]['partner_id'] == partner_id){
                                user_name = self.activeRoute['data']['associated_company'][i]['user_name'];
                            }
                        }
                        var data = {
                            'message': "Are you sure you want to activate " + user_name + '?',
                            'ok_label': "Agree"
                        }
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_confirm",data)));
                    }else{
                        var partner_id = $(".de-btn-edit-user").data("partner-id");
                        var user_name = "";
                        for(var i = 0; i < self.activeRoute['data']['associated_company'].length; i++){
                            if(self.activeRoute['data']['associated_company'][i]['partner_id'] == partner_id){
                                user_name = self.activeRoute['data']['associated_company'][i]['user_name'];
                            }
                        }
                        var data = {
                            'message': "Are you sure you want to delete " + user_name + '?',
                            'ok_label': "Agree"
                        }
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_confirm",data)));
                    }
                }
            },
            loadEditUserView: function(e){
                e.preventDefault();
                e.stopPropagation();
                window.location.hash = '#menu_id=edit-user-profile&partner_id=' + $(e.currentTarget).data("partner-id");
                this.updateMainView();       
            },
            showEditUserView: function(e){
                var self = this;
    
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let partner_id = urlParams.get('partner_id') || '0';
    
                this._rpc({
                    route: '/user/prepare-edit',
                    params: {
                        partner_id: partner_id
                    }
                }).then(function(result){
                    if(result['status'] == 'allowed'){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_portal_user_edit",result['data'])));                     
                        $(document.body).on('click', function(e){
                            if (!$(e.target).is('.de-selector-container,.de-trigger-selector') && !$(e.target).closest('.de-selector-container,.de-trigger-selector').length)
                                $('.de-user-gray-no-border').click();
                        });
    
                        // if ( $(".de-trigger-o-site").children().length > 0 ) {
                        //     $(".de-user-id-form").show();
                        // }else{
                        //     $(".de-user-id-form").hide();
                        // }
                        
                        // $("body").on("DOMSubtreeModified", ".de-trigger-o-site", function() {
                        //     if ( $(this).children().length > 0 ) {
                        //         $(".de-user-id-form").show();
                        //     }else{
                        //         $(".de-user-id-form").hide();
                        //     }
                        // });
                        
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                    }
                });
            },
            getBase64: function(file) {
              return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
              });
            },
            updateUserPhoto:function(e){
                var self = this;
                var file = e.currentTarget.files[0];
                var filesize = ((file.size/1024)/1024).toFixed(4);
                file.asdas
                if (filesize > 2){
                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message':_t('maximum file size exceeded 2mb')})));
                }else{
                    this.getBase64(file).then(
                        function(data){
                          $('.de-user-photo-box img').attr("src",data);
                          $('.de-image-value').val(data.split(",")[1]);
                        }
                    );
                }  
                
            },
            loadMessageListView: function(e){
                var self = this;
                this._rpc({
                    route: '/dashboard/message-list'
                }).then(function(result){
                    console.log("result", result)                    

                    const groupMessage = (messageData) => {
                        var groupIndex = 0
                        var tempGroupRefArr = []                    
                        var tempArray = []

                        messageData.forEach((data, index) => {
                            var record_index = tempGroupRefArr.indexOf(data.record_name);
                            if (record_index >= 0){
                                tempArray[record_index]['message_data'].push({...data})
                                tempArray[record_index]['message_count'] ++;
                            }else{
                                tempArray[groupIndex] = {
                                    'mesage_name' : data.record_name,
                                    'message_data' : [{...data}],
                                    'message_count' : 1,
                                    'last_message_date_iso' : data['date'],
                                    'last_message_date' : moment(new Date(data['date'])).format('YYYY-MM-DD HH:mm'),
                                    'ref_id' : data['ref_id'],
                                }  
                                tempGroupRefArr.push(data.record_name)
                                groupIndex += 1
                            }
                        })

                        return tempArray
                    }

                    var template_data = {
                        'remote_hand' : groupMessage(result['remote_hand']),
                        'fault_report' : groupMessage(result['fault_report']),
                        'site_access' : groupMessage(result['site_access']),
                        'shipment' : groupMessage(result['shipment']),
                        'invoicing' : groupMessage(result['invoicing']),
                        'provisioning' : groupMessage(result['provisioning']),
                        'ordering' : groupMessage(result['ordering'])
                    }
                    
                    console.log(template_data)

                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_message_list", template_data)));

                    $('.de-message-list-row').click((e) => {
                        var ref_model = $(e.currentTarget).data('ref-model');
                        var ref_id = $(e.currentTarget).data('message-ref-id');
                        window.location.hash = `#menu_id=message-detail&ref_model=${ref_model}&ref_id=${ref_id}`;
                        self.updateMainView();
                    })
                });            
            },
            updateMessageListView: function(e){                
                this._rpc({
                    route: '/dashboard/message-list'
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_message_list", result)));
                });
            },            
            loadMessageDetailView: function(e){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let ref_model = urlParams.get('ref_model') || '';
                let ref_id = urlParams.get('ref_id') || '0';

                this._rpc({
                    route: '/dashboard/message-detail',
                    params: {
                        ref_model: ref_model,
                        ref_id: ref_id
                    }
                }).then(function(result){
                    if(result['message']){              
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_message_detail",{'data': result})));
                        $('.de-back-to-notif-list').click((e) => {
                            window.location.hash = '#menu_id=message-list';
                            self.updateMainView();
                        })
                        $('.de-ticket-log-chat-reply').click((e) => {
                            $(e.currentTarget).hide()
                            $(".de-ticket-log-chat-reply-sending").show()
                            var message = $(".de-ticket-log-chat-input").val();
                            var ref_id = $(e.currentTarget).data("ref-id");
                            var ref_model = $(e.currentTarget).data("ref-model");
                            var attachment = [];
                            $(".de-ticket-log-file-data").each(function(){
                                attachment.push({
                                    'data': $(this).val(),
                                    'filename': $(this).data("filename")
                                });
                            });
                            self._rpc({
                                route: '/message/reply',
                                params: {
                                    message: message,
                                    ref_id: ref_id,
                                    ref_model: ref_model,
                                    attachment: attachment
                                }
                            }).then(function(result){
                                if(result['status'] == 'allowed'){                        
                                    self.updateMainView();                                    
                                    $(e.currentTarget).show()
                                    $(".de-ticket-log-chat-reply-sending").hide()
                                }else{
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                                }
                            });
                        })
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot find Message!')})));
                    }
                });
            },
            loadNotificationListView: function(e){
                var self = this;

                this._rpc({
                    route: '/dashboard/notification-list'
                }).then(function(result){
                    var template_data = {'data': result['data']}
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_notification_list", template_data)));
                    $('#de-search-input-tags').tagsInput({
                        // 'onAddTag': function(input, value) {
                        //     var search_term = []
                        //     $(".de-search-tag-keyword").each(function() {
                        //         var column = $(this).children( ".de-search-tag-column" ).text()
                        //         var value = $(this).children( ".de-search-tag-value" ).text()
                        //         if (column == "Order Number"){
                        //             search_term.push('s_order.name' + '->' + value)
                        //         }else if(column == "Invoice Number"){
                        //             search_term.push('move.name' + '->' + value)
                        //         }else if(column == "Company"){
                        //             search_term.push('partner.name' + '->' + value)
                        //         }else if(column == "Reference Number"){
                        //             search_term.push('move.ref' + '->' + value)
                        //         }else if(column == "Invoice Date"){
                        //             search_term.push('move.invoice_date' + '->' + self.formatSearchDate(value))
                        //         }else if(column == "Due Date"){
                        //             search_term.push('move.invoice_date_due' + '->' + self.formatSearchDate(value))
                        //         }
                        //     });
                        //     self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        // },
                        // 'onRemoveTag': function(input, value) {
                        //     var search_term = []
                        //     $(".de-search-tag-keyword").each(function() {
                        //         var column = $(this).children( ".de-search-tag-column" ).text()
                        //         var value = $(this).children( ".de-search-tag-value" ).text()
                        //         if (column == "Order Number"){
                        //             search_term.push('s_order.name' + '->' + value)
                        //         }else if(column == "Invoice Number"){
                        //             search_term.push('move.name' + '->' + value)
                        //         }else if(column == "Company"){
                        //             search_term.push('partner.name' + '->' + value)
                        //         }else if(column == "Reference Number"){
                        //             search_term.push('move.ref' + '->' + value)
                        //         }else if(column == "Invoice Date"){
                        //             search_term.push('move.invoice_date' + '->' + self.formatSearchDate(value))
                        //         }else if(column == "Due Date"){
                        //             search_term.push('move.invoice_date_due' + '->' + self.formatSearchDate(value))
                        //         }
                        //     });
                        //     self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        // },
                        'searchCategory': {
                            source: [     
                                'Subject',                       
                                'Notification Date'
                            ]
                        },
                        'placeholder': _t('search')
                    });
                    $('.de-notification-list-table-tr').click((e) => {
                        var notif_id = $(e.currentTarget).data('notif-id');
                        window.location.hash = `#menu_id=notification-detail&notif_id=${notif_id}`;
                        self.updateMainView();
                    })  
                });                          
            },
            updateNotificationListView: function(e){                
                this._rpc({
                    route: '/dashboard/notification-list'
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_notification_list", result)));
                });
            },
            loadNotificationDetailView: function(e){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let notif_id = urlParams.get('notif_id') || '0';

                this._rpc({
                    route: '/dashboard/notification-detail',
                    params: {
                        notif_id: notif_id
                    }
                }).then(function(result){
                    if(result['data']){              
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_dashboard_notification_detail",{'data': result['data']})));
                        $('.de-back-to-notif-list').click((e) => {
                            window.location.hash = '#menu_id=notification-list';
                            self.updateMainView();
                        })
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot find Notification!')})));
                    }
                });
            },
            loadOrderWIPView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;

                var default_search_param = urlParams.get('search_param') || false; 
                if (default_search_param){
                    default_search_param = default_search_param.split('|')
                    var search_term = []
                    default_search_param.forEach(function (item, index) {
                        var temp_item = item.split('->')
                        var column = temp_item[0]
                        var value = temp_item[1]

                        if (column == "Service ID"){
                            search_term.push('p_task.ns_service_id' + '->' + value)
                        }else if(column == "Product Name"){
                            search_term.push('p_template.name' + '->' + value)
                        }

                    });

                    self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                }

                this._rpc({
                    route: '/order/under-provisioning',
                    params: {
                        order: this.activeRoute.order,
                        limit: 20,
                        offset: 0,
                        search_term: this.activeRoute.searchTerm
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    if (default_search_param){
                        template_data['search_value'] = default_search_param.join()
                    }
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_order_wip", template_data)));
                    $('#de-search-input-tags').tagsInput({
                        'onAddTag': function(input, value) {
                            console.log("add tag ")
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Service ID"){
                                    search_term.push('p_task.ns_service_id' + '->' + value)
                                }else if(column == "Operation Site"){
                                    search_term.push('o_sites.name' + '->' + value)
                                }else if(column == "Product Name"){
                                    search_term.push('p_template.name' + '->' + value)
                                }else if(column == "Order Date"){
                                    search_term.push('s_order.create_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Status"){
                                    search_term.push('p_task_type.name' + '->' + value)
                                }else if(column == "Requested Delivery Date"){
                                    search_term.push('p_task.x_studio_service_request_date' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'onRemoveTag': function(input, value) {
                            console.log("remove tag ")
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Service ID"){
                                    search_term.push('p_task.ns_service_id' + '->' + value)
                                }else if(column == "Operation Site"){
                                    search_term.push('o_sites.name' + '->' + value)
                                }else if(column == "Product Name"){
                                    search_term.push('p_template.name' + '->' + value)
                                }else if(column == "Order Date"){
                                    search_term.push('s_order.create_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Status"){
                                    search_term.push('p_task_type.name' + '->' + value)
                                }else if(column == "Requested Delivery Date"){   
                                    search_term.push('p_task.x_studio_service_request_date' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'searchCategory': {
                            source: [
                                'Service ID',
                                'Operation Site',
                                'Product Name',                            
                                'Order Date',
                                'Status',
                                'Requested Delivery Date',
                                'Product Category'
                            ]
                        },
                        'placeholder': _t('search')
                    });
                    self.scrollToHighlightedRow();
                });            
            },
            updateOrderWIPListView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;
                this._rpc({
                    route: '/order/under-provisioning',
                    params: {
                        order: this.activeRoute.order,
                        search_term: this.activeRoute.searchTerm,
                        limit: 20,
                        offset: 0
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    self.$el.find(".de-portal-wip-body").replaceWith($(qweb.render("nrs_de_portal.de_order_wip_table_body", template_data)));
                    self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                });
            },
            loadOrderInstalledView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;

                var default_search_param = urlParams.get('search_param') || false; 
                if (default_search_param){
                    default_search_param = default_search_param.split('|')
                    var search_term = []
                    default_search_param.forEach(function (item, index) {
                        var temp_item = item.split('->')
                        var column = temp_item[0]
                        var value = temp_item[1]

                        if (column == "Service ID"){
                            search_term.push('p_task.ns_service_id' + '->' + value)
                        }else if(column == "Product"){
                            search_term.push('p_template.name' + '->' + value)
                        }

                    });

                    self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                }

                this._rpc({
                    route: '/order/installed',
                    params: {
                        order: this.activeRoute.order,
                        keyword: this.activeRoute.keyword,
                        limit: 20,
                        offset: 0,
                        search_term: this.activeRoute.searchTerm
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}                    
                    if (default_search_param){
                        template_data['search_value'] = default_search_param.join()
                    }
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_order_installed",template_data)));
                    $('#de-search-input-tags').tagsInput({
                        'onAddTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Service ID"){
                                    search_term.push('p_task.ns_service_id' + '->' + value)
                                }else if(column == "Operation Site"){
                                    search_term.push('o_sites.name' + '->' + value)
                                }else if(column == "Product"){
                                    search_term.push('p_template.name' + '->' + value)
                                }else if(column == "Reference Number"){
                                    search_term.push('s_order.client_order_ref' + '->' + value)
                                }else if(column == "Service Order Number"){
                                    search_term.push('s_order.name' + '->' + value)
                                }else if(column == "Installed Date"){
                                    search_term.push('p_task.x_studio_installed_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Contract End Date"){
                                    search_term.push('s_order.x_studio_contract_end_date' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'onRemoveTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Service ID"){
                                    search_term.push('p_task.ns_service_id' + '->' + value)
                                }else if(column == "Operation Site"){
                                    search_term.push('o_sites.name' + '->' + value)
                                }else if(column == "Product"){
                                    search_term.push('p_template.name' + '->' + value)
                                }else if(column == "Reference Number"){
                                    search_term.push('s_order.client_order_ref' + '->' + value)
                                }else if(column == "Service Order Number"){
                                    search_term.push('s_order.name' + '->' + value)
                                }else if(column == "Installed Date"){
                                    search_term.push('p_task.x_studio_installed_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Contract End Date"){
                                    search_term.push('s_order.x_studio_contract_end_date' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'searchCategory': {
                            source: [
                                'Service ID',
                                'Operation Site',
                                'Product',
                                'Reference Number',
                                'Service Order Number',
                                'Installed Date',
                                'Contract End Date'
                            ]
                        },
                        'placeholder': _t('search')
                    });

                    self.scrollToHighlightedRow();
    
                    self._rpc({
                        route: '/order/installed/summary'
                    }).then(function(result){

                        self.$el.find(".de-installed-service-left-box").append($(qweb.render("nrs_de_portal.de_order_installed_summary",result)));
                        
                        $( ".de-p-category-label" ).each(function( index ) {
                            if($( this ).text() == "Interconnect"){
                                $( this ).text(TRANSLATE_TERM['label_interconnect'].toString())
                            }else if($( this ).text() == "Managed Services"){
                                $( this ).text(TRANSLATE_TERM['label_managed_services'].toString())
                            }else if($( this ).text() == "Power"){
                                $( this ).text(TRANSLATE_TERM['label_power'].toString())
                            }else if($( this ).text() == "Space"){
                                $( this ).text(TRANSLATE_TERM['label_space'].toString())
                            }
                        });

                        if (self.activeRoute['installedChartId'] && self.activeRoute['installedChartId'].length > 0){
                            self.activeRoute['installedChartId'].forEach(function (item, index) {
                                item.destroy();
                            });
                        }

                        var temp_chart_id = []
                        
                        for(var i = 0; i < result['chart'].length; i++){
                            console.log(result['chart'][i])
                            var location = result['chart'][i]['label'];
                            var total = result['chart'][i]['total'];
                            self.$el.find(".de-installed-service-right-box").append($(qweb.render("nrs_de_portal.de_order_installed_chart_summary",{'location': location, 'total': total})));
                            
                            var chart_config = {
                                type: 'doughnut',
                                data: {
                                    datasets: [
                                        {
                                            data: result['chart'][i]['data'],
                                            backgroundColor: result['chart'][i]['backgroundColor']
                                        }
                                    ]
                                },
                            };                         

                            temp_chart_id.push(new Chart(document.getElementById(location),chart_config))
                        }
                        
                        self.activeRoute['installedChartId'] = temp_chart_id

                        $(".de-p-category-color").each(function(){
                            $(this).css("background-color",$(this).data("color"));
                        });
                    });
                });            
            },
            updateOrderInstalledListView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;
                this._rpc({
                    route: '/order/installed',
                    params: {
                        order: this.activeRoute.order,
                        search_term: this.activeRoute.searchTerm,
                        limit: 20,
                        offset: 0
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    self.$el.find(".de-portal-installed-body").replaceWith($(qweb.render("nrs_de_portal.de_order_installed_table_body",template_data)));
                    self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));

                    self._rpc({
                        route: '/order/installed/summary',
                        params: {
                            search_term: self.activeRoute.searchTerm
                        }
                    }).then(function(result){
                        self.$el.find(".de-installed-service-left-box").empty();
                        self.$el.find(".de-installed-service-left-box").append($(qweb.render("nrs_de_portal.de_order_installed_summary",result)));

                        $( ".de-p-category-label" ).each(function( index ) {
                            if($( this ).text() == "Interconnect"){
                                $( this ).text(TRANSLATE_TERM['label_interconnect'].toString())
                            }else if($( this ).text() == "Managed Services"){
                                $( this ).text(TRANSLATE_TERM['label_managed_services'].toString())
                            }else if($( this ).text() == "Power"){
                                $( this ).text(TRANSLATE_TERM['label_power'].toString())
                            }else if($( this ).text() == "Space"){
                                $( this ).text(TRANSLATE_TERM['label_space'].toString())
                            }
                        });

                        if (self.activeRoute['installedChartId'] && self.activeRoute['installedChartId'].length > 0){
                            self.activeRoute['installedChartId'].forEach(function (item, index) {
                                item.destroy();
                            });
                        }

                        var temp_chart_id = []
                        
                        self.$el.find(".de-installed-service-right-box").empty();
                        
                        for(var i = 0; i < result['chart'].length; i++){
                            console.log(result['chart'][i])
                            var location = result['chart'][i]['label'];
                            var total = result['chart'][i]['total'];
                            self.$el.find(".de-installed-service-right-box").append($(qweb.render("nrs_de_portal.de_order_installed_chart_summary",{'location': location, 'total': total})));
                            
                            var chart_config = {
                                type: 'doughnut',
                                data: {
                                    datasets: [
                                        {
                                            data: result['chart'][i]['data'],
                                            backgroundColor: result['chart'][i]['backgroundColor']
                                        }
                                    ]
                                },
                            };
                                
                            // var summaryChart = new Chart(document.getElementById(location),chart_config);

                            temp_chart_id.push(new Chart(document.getElementById(location),chart_config))
                        }

                        self.activeRoute['installedChartId'] = temp_chart_id
    
                        $(".de-p-category-color").each(function(){
                            $(this).css("background-color",$(this).data("color"));
                        });
                    });

                }); 
            },
            downloadInstalledService: function(){
                window.open('/order/installed/download?keyword=' + this.activeRoute.keyword +'&order='+this.activeRoute.order)
            },
            loadRemoteHandsView: function(){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let action = urlParams.get('action') || '';
                let ticket_id = urlParams.get('ticket_id') || '0';
                let project_id = urlParams.get('project_id') || '0';
    
                if(action == 'read'){
                    this._rpc({
                        route: '/remote-hands/read',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                     
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_read_order_remote_hands",result)));
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else if(action == 'edit'){
                    this._rpc({
                        route: '/remote-hands/edit',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_edit_order_remote_hands",result)));                        
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)
                            var get_pricelist = function(){
                                        
                                var data = $(".de-portal-form").serializeArray();            
                                data = self.arrayToJSON(data);
                                self._rpc({
                                    route: '/ticket/pricelist',
                                    params: data
                                }).then(function(result){
                                    ;
                                    var temp_price = result['price'] + " " + TRANSLATE_TERM[result['currency']].toString() || result['default_currency']
                                    $(".de-service-price").text(temp_price);
                                });
                            };

                            if ($.trim($(".de-ticket-type-id").find(":selected").text()) == 'Scheduled Remote Hands'){
                                $(".de-requested-service-date").show();
                            }

                            $(".de-ticket-type-id").change(function(e){
                                if ($.trim($(e.currentTarget).find(":selected").text()) == 'Scheduled Remote Hands'){
                                    $(".de-requested-service-date").show();
                                }else{
                                    $(".de-requested-service-date").hide();
                                }
                            });
    
                            $(".de-partner-id, .de-osite, .de-service-id").change(function(){
                                get_pricelist();
                            });

                            var req_date = $("#requestdatepicker").val() != '' && $("#requestdatepicker").val() != null ?  new Date($("#requestdatepicker").val()) : new Date()
                            var today = new Date().setHours(0, 0, 0, 0);

                            $("#requestdatepicker").datetimepicker({
                                format: 'YYYY-MM-DD HH:mm',
                                date: $("#requestdatepicker").val(),
                                minDate: req_date < today ? req_date : today
                            });
                            
                            $("#requestdatepicker").click(function(){
                                $("#requestdatepicker").datetimepicker('toggle');
                            });
        
                            $('#requestdatepicker').on("change.datetimepicker", ({date, oldDate}) => {
                                var new_req_date = new Date($("#requestdatepicker").val()); 
                                var min_date = req_date < today ? req_date : today

                                if (new_req_date < min_date){
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                    if(oldDate && oldDate >= today)
                                        $("#requestdatepicker").val(moment(oldDate).format('YYYY-MM-DD HH:mm'))
                                    else
                                        $("#requestdatepicker").val(moment(new Date()).format('YYYY-MM-DD HH:mm'))
                                }
                            })
    
                            get_pricelist();
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else{
                    self._rpc({
                        route: '/remote-hands',
                        params: {
                            project_id: project_id
                        }
                    }).then(function(result){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_order_remote_hands",result)));
                        self.getTicketList();
                        if (project_id != '0'){
                            $(".de-service-id").trigger("change");
                        }
                        var get_pricelist = function(){
                            var data = $(".de-portal-form").serializeArray();            
                            data = self.arrayToJSON(data);
                            self._rpc({
                                route: '/ticket/pricelist',
                                params: data
                            }).then(function(result){
                                
                                var temp_price = result['price'] + " " + TRANSLATE_TERM[result['currency']].toString() || result['default_currency']                                    
                                $(".de-service-price").text(temp_price);
                            });
                        };
    
                        if(!result['value']['x_studio_operation_site']){
                            $(".de-partner-id").trigger("change");
                        }
    
                        $(".de-partner-id").change(function(){
                            get_pricelist();
                        });

                        $(".de-ticket-type-id").change(function(e){
                            if ($.trim($(e.currentTarget).find(":selected").text()) == 'Scheduled Remote Hands'){
                                $(".de-requested-service-date").show();
                            }else{
                                $(".de-requested-service-date").hide();
                            }
                        });
    
                        // $("#requestdatepicker").datetimepicker({
                        //     format: 'YYYY-MM-DD HH:mm'
                        // });
                        
                        // $("#requestdatepicker").click(function(){
                        //     $("#requestdatepicker").datetimepicker('toggle');
                        // });
                        $("#requestdatepicker").datetimepicker({
                            format: 'YYYY-MM-DD HH:mm',
                            minDate: new Date().setHours(0, 0, 0, 0)
                        });
                        
                        $("#requestdatepicker").click(function(){
                            $("#requestdatepicker").datetimepicker('toggle');
                        });
    
                        $('#requestdatepicker').on("change.datetimepicker", ({date, oldDate}) => {
                            var req_date = new Date($("#requestdatepicker").val()); 
                            var today = new Date();
                            if (req_date.setHours(0, 0, 0, 0) < today.setHours(0, 0, 0, 0)){
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                if(oldDate && oldDate >= today.setHours(0, 0, 0, 0))
                                    $("#requestdatepicker").val(moment(oldDate).format('YYYY-MM-DD'))
                                else
                                    $("#requestdatepicker").val(moment(new Date()).format('YYYY-MM-DD'))
                            }
                        })
    
                        get_pricelist();
                        $(".de-btn-save-order").click(function(e){
                            var data = $(".de-portal-form").serializeArray();
                            data = self.arrayToJSON(data); 
                            self._rpc({
                                route: '/remote-hands/save-check',
                                params: data
                            }).then(function(result){
                                if(result['status'] == 'pass'){                                
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_order_form_1_popup")));
                                    $(".de-understand-order-form-popup").click(function(e){
                                        self._rpc({
                                            route: '/get-external-link',
                                            params: {
                                                link_type: 'order_agreement'
                                            }
                                        }).then(function(result){
                                            $(".de-order-form-dialog").remove();
                                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_order_form_2_popup")));
                                            var temp_agreement_text = $(".de-order-popup-2").text().replace('_t_url', result['url'])
                                            $(".de-order-popup-2").text(temp_agreement_text)
                                        });
                                    })
                                }else{
                                    var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                                }
                            });
                        })
                    })                            
                }            
            },
            loadInterconnectionServicesView: function(){
                var self = this;

                self._rpc({
                    route: '/interconnection-service'
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_order_interconnection_services",result)));
                    $(".de-tooltips-popover").popover({
                        'container': $('.de-portal-form'),
                        'content' : 'If you are connecting to a 3rd party cabinet, we will require a letter of authorization from the 3rd party to be attached to the order form prior to order acceptance. <a href="/customer-portal-user-guide?page=10" target="_blank">Read More...</a>',
                        'html': true,
                        'animation': false
                    }).on("mouseenter", function() {
                        var _this = this;
                        $(this).popover("show");
                        $(".popover").on("mouseleave", function() {
                            $(_this).popover('hide');
                        });
                    }).on("mouseleave", function() {
                        var _this = this;
                        setTimeout(function() {
                            if (!$(".popover:hover").length) {
                            $(_this).popover("hide");
                            }
                        }, 300);
                    });

                    $(".de-partner-id").trigger("change");
                    var get_interconnection_pricelist = function(){
                        var data = $(".de-portal-form").serializeArray();            
                        data = self.arrayToJSON(data);
                        data['loa'] = '';
                        self._rpc({
                            route: '/interconnection/pricelist',
                            params: data
                        }).then(function(result){
                            $(".de-service-price").text(result['price']);
                            $(".de-mrc-product").val(result['mrc_product']);
                            $(".de-nrc-product").val(result['nrc_product']);
                        });
                    };                    

                    $('.de-quantity').focus(function(event) {
                        if ($(event.currentTarget).val() > 0 && $(event.currentTarget).val() != ''){                            
                            $(event.currentTarget).attr('old-value', $(event.currentTarget).val());
                        }
                    });

                    $(".de-quantity").on("input",function(event){
                        if ($(event.currentTarget).val() < 1 && $(event.currentTarget).val() != ''){                            
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Minimal Quantity is 1!')})));
                            $(event.currentTarget).val(1)
                        }else get_interconnection_pricelist();
                    });

                    $('.de-quantity').blur(function(event) {
                        var old_value = $(event.currentTarget).attr("old-value")
                        if ($(event.currentTarget).val() < 1 || $(event.currentTarget).val() == ''){        
                            if (old_value > 0 && old_value != ''){                            
                                $(event.currentTarget).val(old_value)
                            }else{
                                $(event.currentTarget).val(1)
                            }             
                        }
                    });

                    $(".de-partner-id, .de-choose-service, .de-media-type").change(function(e){
                        get_interconnection_pricelist();
                    });

                    $(".de-intra-customer, .de-osite, .de-service-id").change(function(e){
                        get_interconnection_pricelist();
                        if ($(".de-intra-customer").is(":checked")){
                            $(".de-service-id-z").hide()
                            $(".de-interconnection-loa").hide()
                            $(".de-service-id-z-select").empty();
                            var operation_site = $(".de-osite").val();
                            var product_categ = $(".de-service-id").data("product-categ");
                            if($(".de-service-id").val() != 'other'){
                                self._rpc({
                                    route: '/get/service-id',
                                    params: {
                                        operation_site: operation_site,
                                        product_categ: product_categ,
                                        service_id: $(".de-service-id").val(),                                 
                                        menu: self.activeRoute['menu_id']
                                    }
                                }).then(function(result){                            
                                    $(".de-service-id-z-select").show()
                                    $(".de-service-id-z-select").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                                });
                            }
                        }else{
                            $(".de-service-id-z").show()
                            $(".de-interconnection-loa").show()
                            $(".de-service-id-z-select").hide()
                        }
                    });
    
                    $("#requestdatepicker").datetimepicker({
                        format: 'YYYY-MM-DD',
                        minDate: new Date().setHours(0, 0, 0, 0)
                    });
                    
                    $("#requestdatepicker").click(function(){
                        $("#requestdatepicker").datetimepicker('toggle');
                    });

                    $('#requestdatepicker').on("change.datetimepicker", ({date, oldDate}) => {
                        var req_date = new Date($("#requestdatepicker").val()); 
                        var today = new Date();
                        if (req_date.setHours(0, 0, 0, 0) < today.setHours(0, 0, 0, 0)){
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                            if(oldDate && oldDate >= today.setHours(0, 0, 0, 0))
                                $("#requestdatepicker").val(moment(oldDate).format('YYYY-MM-DD'))
                            else
                                $("#requestdatepicker").val(moment(new Date()).format('YYYY-MM-DD'))
                        }
                    })
    
                    $(".de-file-input").change(function(e){
                        var file = e.currentTarget.files[0];
                        if(file){
                            self.getBase64(file).then(
                                function(data){
                                    $('.de-loa-file').val(data.split(",")[1]);
                                });
                            var filesize = ((file.size/1024)/1024).toFixed(4);
                            if (filesize > 2){
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message':_t('maximum file size exceeded 2mb')})));
                                $('.de-file-input').val(null);
                            }   
                        }else{
                            $('.de-loa-file').val('');
                        }
                        
                    });
    
                    $(".de-btn-save-order").click(function(e){
                        var data = $(".de-portal-form").serializeArray();
                        data = self.arrayToJSON(data); 
                        self._rpc({
                            route: '/interconnection-service/save-check',
                            params: data
                        }).then(function(result){
                            if(result['status'] == 'pass'){                                
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_order_form_1_popup")));
                                $(".de-understand-order-form-popup").click(function(e){
                                    self._rpc({
                                        route: '/get-external-link',
                                        params: {
                                            link_type: 'order_agreement'
                                        }
                                    }).then(function(result){
                                        $(".de-order-form-dialog").remove();
                                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_order_form_2_popup")));
                                        var temp_agreement_text = $(".de-order-popup-2").text().replace('_t_url', result['url'])
                                        $(".de-order-popup-2").text(temp_agreement_text)
                                    });
                                })
                            }else{
                                var err_message = TRANSLATE_TERM[result['message']]?.toString() || result['message']
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': err_message})));
                            }
                        });
                    })
                });                 
            },
            loadColocationAccessoriesView: function(){
                var self = this;
                this._rpc({
                    route: '/colocation-accessories'
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_order_colocation_accessories",result))); 
                    $(".de-partner-id").trigger("change");
    
                    var get_colocation_accessories_pricelist = function(){
                        var data = $(".de-portal-form").serializeArray();            
                        data = self.arrayToJSON(data);
                        self._rpc({
                            route: '/colocation-accessories/pricelist',
                            params: data
                        }).then(function(result){
                            $(".de-service-price").text(result['price']);
                        });
                    };
    
                    $(".de-partner-id, .de-product-id, .de-osite, .de-qty").change(function(){
                        get_colocation_accessories_pricelist();
                    });
    
                    $("#requestdatepicker").datetimepicker({
                        format: 'YYYY-MM-DD',
                        minDate: new Date().setHours(0, 0, 0, 0)
                    });
                    
                    $("#requestdatepicker").click(function(){
                        $("#requestdatepicker").datetimepicker('toggle');
                    });

                    $('#requestdatepicker').on("change.datetimepicker", ({date, oldDate}) => {
                        var req_date = new Date($("#requestdatepicker").val()); 
                        var today = new Date();
                        if (req_date.setHours(0, 0, 0, 0) < today.setHours(0, 0, 0, 0)){
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                            if(oldDate && oldDate >= today.setHours(0, 0, 0, 0))
                                $("#requestdatepicker").val(moment(oldDate).format('YYYY-MM-DD'))
                            else
                                $("#requestdatepicker").val(moment(new Date()).format('YYYY-MM-DD'))
                        }
                    })
    
                    $(".de-btn-save-order").click(function(e){
                        self.$el.find(".de-portal-content").append($(qweb.render("nrs_de_portal.de_submit_order")));
                    })
                });            
            },
            loadInvoiceView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;

                var default_search_param = urlParams.get('search_param') || false; 
                if (default_search_param){
                    default_search_param = default_search_param.split('|')
                    var search_term = []
                    default_search_param.forEach(function (item, index) {
                        var temp_item = item.split('->')
                        var column = temp_item[0]
                        var value = temp_item[1]

                        if (column == "Invoice Number"){
                            search_term.push('move.name' + '->' + value)
                        }else if(column == "Reference Number"){
                            search_term.push('move.ref' + '->' + value)
                        }

                    });

                    self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                }

                this._rpc({
                    route: '/invoice',
                    params: {
                        order: this.activeRoute.order,                        
                        limit: 20,
                        offset: 0,
                        search_term: this.activeRoute.searchTerm,
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'user_company': result['user_company'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    if (default_search_param){
                        template_data['search_value'] = default_search_param.join()
                    }
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_invoice", template_data)));
                    $('#de-search-input-tags').tagsInput({
                        'onAddTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Order Number"){
                                    search_term.push('s_order.name' + '->' + value)
                                }else if(column == "Invoice Number"){
                                    search_term.push('move.name' + '->' + value)
                                }else if(column == "Company"){
                                    search_term.push('partner.name' + '->' + value)
                                }else if(column == "Reference Number"){
                                    search_term.push('move.ref' + '->' + value)
                                }else if(column == "Invoice Date"){
                                    search_term.push('move.invoice_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Due Date"){
                                    search_term.push('move.invoice_date_due' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'onRemoveTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if (column == "Order Number"){
                                    search_term.push('s_order.name' + '->' + value)
                                }else if(column == "Invoice Number"){
                                    search_term.push('move.name' + '->' + value)
                                }else if(column == "Company"){
                                    search_term.push('partner.name' + '->' + value)
                                }else if(column == "Reference Number"){
                                    search_term.push('move.ref' + '->' + value)
                                }else if(column == "Invoice Date"){
                                    search_term.push('move.invoice_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Due Date"){
                                    search_term.push('move.invoice_date_due' + '->' + self.formatSearchDate(value))
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'searchCategory': {
                            source: [     
                                'Invoice Number',                       
                                'Order Number',
                                'Company',
                                'Reference Number',
                                'Invoice Date',
                                'Due Date',
                            ]
                        },
                        'placeholder': _t('search')
                    });
                });            
            },
            downloadInvoice: function(){
                window.open('/invoice/download?order='+this.activeRoute.order)
            },
            updateOrderInvoiceListView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;
                this._rpc({
                    route: '/invoice',
                    params: {
                        order: this.activeRoute.order,
                        search_term: this.activeRoute.searchTerm,
                        limit: 20,
                        offset: 0
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'user_company': result['user_company'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    self.$el.find(".de-portal-invoice-body").replaceWith($(qweb.render("nrs_de_portal.de_invoice_table_body",template_data)));
                    self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                });
            },
            actionNewFaultReport: function(e){
                e.preventDefault();
                e.stopPropagation();
    
                window.location.hash = '#menu_id=new-fault-report-ticket&project_id=' + $(e.currentTarget).data("project-id");
                this.updateMainView();
            },
            actionNewRemoteHands: function(e){
                e.preventDefault();
                e.stopPropagation();
    
                window.location.hash = '#menu_id=remote-hands&project_id=' + $(e.currentTarget).data("project-id");
                this.updateMainView();
            },
            actionNewShipment: function(e){
                e.preventDefault();
                e.stopPropagation();
    
                window.location.hash = '#menu_id=new-shipment-ticket&project_id=' + $(e.currentTarget).data("project-id");
                this.updateMainView();
            },
            loadFaultReportView: function(){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let action = urlParams.get('action') || '';
                let ticket_id = urlParams.get('ticket_id') || '0';
                let project_id = urlParams.get('project_id') || '0';
    
                if(action == 'read'){
                    this._rpc({
                        route: '/fault-report/read',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_read_new_fault_report",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'Each service is assigned a unique Service ID as an identifier for any changes (e.g. disconnect orders) or actions (e.g. fault report ticket) on this service. <a href="/customer-portal-user-guide?page=9" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else if(action == 'edit'){
                    this._rpc({
                        route: '/fault-report/edit',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_edit_new_fault_report",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'Each service is assigned a unique Service ID as an identifier for any changes (e.g. disconnect orders) or actions (e.g. fault report ticket) on this service. <a href="/customer-portal-user-guide?page=9" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else{
                    this._rpc({
                        route: '/fault-report',
                        params: {
                            project_id: project_id
                        }
                    }).then(function(result){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_new_fault_report",result)));
                        $(".de-tooltips-popover").popover({
                            'container': $('.de-portal-form'),
                            'content' : 'Each service is assigned a unique Service ID as an identifier for any changes (e.g. disconnect orders) or actions (e.g. fault report ticket) on this service. <a href="/customer-portal-user-guide?page=9" target="_blank">Read More...</a>',
                            'html': true,
                            'animation': false
                        }).on("mouseenter", function() {
                            var _this = this;
                            $(this).popover("show");
                            $(".popover").on("mouseleave", function() {
                                $(_this).popover('hide');
                            });
                        }).on("mouseleave", function() {
                            var _this = this;
                            setTimeout(function() {
                                if (!$(".popover:hover").length) {
                                $(_this).popover("hide");
                                }
                            }, 300);
                        });
                        
                        if (project_id != '0'){
                            $(".de-service-id").trigger("change");
                        }
                        if(!result['value']['x_studio_operation_site']){
                            $(".de-partner-id").trigger("change");
                        }
                        self.getTicketList();                  
                    });
                }
            },
            loadSiteAccessView: function(){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let action = urlParams.get('action') || '';
                let ticket_id = urlParams.get('ticket_id') || '0';
    
                if(action == 'read'){
                    this._rpc({
                        route: '/site-access/read',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_read_new_site_access",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'If a user with Permanent site access requires special access they should also create a temporary site access ticket. <a href="/customer-portal-user-guide?page=12" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)
                            self.getTicketList();
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else if(action == 'edit'){
                    this._rpc({
                        route: '/site-access/edit',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_edit_new_site_access",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'If a user with Permanent site access requires special access they should also create a temporary site access ticket. <a href="/customer-portal-user-guide?page=12" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)
                            self.getTicketList();
                            
                            var today = new Date().setHours(0, 0, 0, 0);
                            var start_date = $("#visitdate").val() != '' && $("#visitdate").val() != null ?  new Date($("#visitdate").val()).setHours(0, 0, 0, 0) : today

                            $("#visitdate, #visitdateend").each((i,el)=>{
                                $(el).datetimepicker({
                                    format: 'YYYY-MM-DD HH:mm',
                                    'date': $(el).val(),
                                    minDate: start_date < today ? start_date : today
                                });
                                $(el).click(function(){
                                    $(el).datetimepicker('toggle');
                                });
                            });                            

                            $('#visitdate').on("change.datetimepicker", ({date, oldDate}) => {
                                var new_start_date = new Date($("#visitdate").val()).setHours(0, 0, 0, 0);
                                var min_date = start_date < today ? start_date : today

                                if(new_start_date < min_date){
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                    if(oldDate && oldDate >= min_date)
                                        $("#visitdate").val(moment(oldDate).format('YYYY-MM-DD HH:mm'))
                                    else
                                        $("#visitdate").val(moment(new Date()).format('YYYY-MM-DD HH:mm'))

                                }else{                                
                                    $("#visitdateend").val(moment(date).format('YYYY-MM-DD HH:mm'))
                                    $("#visitdateend").datetimepicker('minDate', moment(date).format('YYYY-MM-DD HH:mm'));
                                }
                            })

                            if(result['value']['ns_special_visit_area'] == 'yes'){
                                $('.de-visit-area-name-box').show()
                            }else{                                
                                $('.de-visit-area-name-box').hide()
                            }
                            
                            $(".de-special-visit-area").change(function(e){
                                var special_visit =  $(e.currentTarget).val()
                                if(special_visit == 'yes'){
                                    $('.de-visit-area-name-box').show()
                                }else{                                
                                    $('.de-visit-area-name-box').hide()
                                    $('.de-visit-area-name').val('')
                                }
                            });
                            
                            $(".de-osite").change(function(e){
                                var operation_site = $(e.currentTarget).val();
                                $(".de-chip-delete").click();
                                $(".de-selector-box").empty();
                                self._rpc({
                                    route: '/get/area',
                                    params: {
                                        operation_site: operation_site
                                    }
                                }).then(function(result){
                                    $(".de-selector-box").append($(qweb.render("nrs_de_portal.de_area_selection",result)));
                                });
                            });
    
                            $(".de-partner-id").change(function(e){
                                $(".de-chip-delete").click();
                                $(".de-selector-box").empty();
                            });

                            $(".de-form-input-visitor").popover({
                                'container': $('.de-form-box-visitor'),
                                'content' : TRANSLATE_TERM['tooltip_fault_report_visitor_name'].toString(),
                                'placement' : 'right' 
                            });

                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else{
                    this._rpc({
                        route: '/site-access'
                    }).then(function(result){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_new_site_access",result)));
                        $(".de-tooltips-popover").popover({
                            'container': $('.de-portal-form'),
                            'content' : 'If a user with Permanent site access requires special access they should also create a temporary site access ticket. <a href="/customer-portal-user-guide?page=12" target="_blank">Read More...</a>',
                            'html': true,
                            'animation': false
                        }).on("mouseenter", function() {
                            var _this = this;
                            $(this).popover("show");
                            $(".popover").on("mouseleave", function() {
                                $(_this).popover('hide');
                            });
                        }).on("mouseleave", function() {
                            var _this = this;
                            setTimeout(function() {
                                if (!$(".popover:hover").length) {
                                $(_this).popover("hide");
                                }
                            }, 300);
                        });
                        
                        self.getTicketList();
    
                        $(".de-partner-id").trigger("change");

                        
                        var today = new Date().setHours(0, 0, 0, 0);
                        
                        $("#visitdate, #visitdateend").each((i,el)=>{
                            $(el).datetimepicker({
                                format: 'YYYY-MM-DD HH:mm',
                                'date': $(this).val(),                                
                                minDate: today
                            });
                            $(el).click(function(){
                                $(this).datetimepicker('toggle');
                            });
                        });

                        $('#visitdate').on("change.datetimepicker", ({date, oldDate}) => {
                            var start_date = new Date($("#visitdate").val()).setHours(0, 0, 0, 0);
                            if(start_date < today){
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                if(oldDate && oldDate >= today)
                                    $("#visitdate").val(moment(oldDate).format('YYYY-MM-DD HH:mm'))
                                else
                                    $("#visitdate").val(moment(new Date()).format('YYYY-MM-DD HH:mm'))

                            }else{                                
                                $("#visitdateend").val(moment(date).format('YYYY-MM-DD HH:mm'))
                                $("#visitdateend").datetimepicker('minDate', moment(date).format('YYYY-MM-DD HH:mm'));
                            }
                        })

                        $(".de-special-visit-area").change(function(e){
                            var special_visit =  $(e.currentTarget).val()
                            if(special_visit == 'yes'){
                                $('.de-visit-area-name-box').show()
                            }else{                                
                                $('.de-visit-area-name-box').hide()
                                $('.de-visit-area-name').val('')
                            }
                        });

                        $(".de-osite").change(function(e){
                            var operation_site = $(e.currentTarget).val();
                            $(".de-chip-delete").click();
                            $(".de-selector-box").empty();
                            self._rpc({
                                route: '/get/area',
                                params: {
                                    operation_site: operation_site
                                }
                            }).then(function(result){
                                $(".de-selector-box").append($(qweb.render("nrs_de_portal.de_area_selection",result)));
                            });
                        });
    
                        $(".de-partner-id").change(function(e){
                            $(".de-chip-delete").click();
                            $(".de-selector-box").empty();
                        });

                        $(".de-form-input-visitor").popover({
                            'placement' : 'right',
                            'container': $('.de-form-box-visitor'),
                            'content' : TRANSLATE_TERM['tooltip_fault_report_visitor_name'].toString(),
                            'trigger': 'focus'
                            
                        });

                    });  
                }            
            },
            loadShipmentView: function(){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let project_id = urlParams.get('project_id') || '0';
                let action = urlParams.get('action') || '';
                let ticket_id = urlParams.get('ticket_id') || '0';
    
                if(action == 'read'){
                    this._rpc({
                        route: '/shipment/read',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_read_new_shipment",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'For larger shipments please select the “Require Loading Dock” check box and our operations team will contact you with the arrangements. <a href="/customer-portal-user-guide?page=14" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();  
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)                      
                            if (result['value']['ticket_type_id'] == 'Inbound'){
                                $(".de-form-box-handling-instruction").show();
                            }
                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else if(action == 'edit'){
                    this.activeRoute['deleted_shipment_detail'] = []
                    this._rpc({
                        route: '/shipment/edit',
                        params: {
                            ticket_id: ticket_id
                        }
                    }).then(function(result){
                        if(result['status'] == 'allowed'){                        
                            self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_edit_new_shipment",result)));
                            $(".de-tooltips-popover").popover({
                                'container': $('.de-portal-form'),
                                'content' : 'For larger shipments please select the “Require Loading Dock” check box and our operations team will contact you with the arrangements. <a href="/customer-portal-user-guide?page=14" target="_blank">Read More...</a>',
                                'html': true,
                                'animation': false
                            }).on("mouseenter", function() {
                                var _this = this;
                                $(this).popover("show");
                                $(".popover").on("mouseleave", function() {
                                    $(_this).popover('hide');
                                });
                            }).on("mouseleave", function() {
                                var _this = this;
                                setTimeout(function() {
                                    if (!$(".popover:hover").length) {
                                    $(_this).popover("hide");
                                    }
                                }, 300);
                            });
                            
                            $(".de-form-input-ticket-description").val(result['value']['description'])
                            self.getTicketList();
                            $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${result['value']['operation_site_timezone']})</span>`)
                            $(".de-require-loading-dock").change(function(e){
                                var require_loading_dock =  $(e.currentTarget).val()
                                if(require_loading_dock == 'yes'){
                                    $('#expecteddate').val('')
                                    $('.de-expected-date').hide()
                                    $('.de-shipment-date-range').show();
                                    $( ".de-loading-dock" ).prop( "checked", true );
                                }else{
                                    $('#shipmentdate').val('')
                                    $('#shipmentdateend').val('')
                                    $('.de-shipment-date-range').hide()
                                    $('.de-expected-date').show()
                                    $( ".de-loading-dock" ).prop( "checked", false );
                                }
                            });

                            if ($.trim($(".de-ticket-type-id").find(":selected").text()) == 'Inbound'){
                                $(".de-form-box-handling-instruction").show();
                            }

                            $(".de-ticket-type-id").change(function(e){
                                if ($.trim($(e.currentTarget).find(":selected").text()) == 'Inbound'){
                                    $(".de-form-box-handling-instruction").show();
                                }else{
                                    $(".de-form-box-handling-instruction").hide();
                                }
                            });

                            var today = new Date().setHours(0, 0, 0, 0);
                            var start_date = $("#shipmentdate").val() != '' && $("#shipmentdate").val() != null ?  new Date($("#shipmentdate").val()).setHours(0, 0, 0, 0) : today
                            var expected_date = $("#expecteddate").val() != '' && $("#expecteddate").val() != null ?  new Date($("#expecteddate").val()).setHours(0, 0, 0, 0) : today

                            $("#expecteddate").datetimepicker({
                                format: 'YYYY-MM-DD',
                                'date': $("#expecteddate").val(),                                
                                minDate: expected_date < today ? expected_date : today
                            });

                            $("#expecteddate").click(function(){
                                $('#expecteddate').datetimepicker('toggle');
                            });

                            $("#shipmentdate, #shipmentdateend").each((i,el)=>{
                                $(el).datetimepicker({
                                    format: 'YYYY-MM-DD HH:mm',
                                    'date': $(el).val(),
                                    minDate: start_date < today ? start_date : today
                                });
                                $(el).click(function(){
                                    $(el).datetimepicker('toggle');
                                });
                            });
    
                            $('#expecteddate').on("change.datetimepicker", ({date, oldDate}) => {
                                var exp_date = new Date($("#expecteddate").val()).setHours(0, 0, 0, 0); 
                                if (exp_date < today){
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                    if(oldDate && oldDate >= today)
                                        $("#expecteddate").val(moment(oldDate).format('YYYY-MM-DD'))
                                    else
                                        $("#expecteddate").val(moment(new Date()).format('YYYY-MM-DD'))
                                }
                            })
    
                            $('#shipmentdate').on("change.datetimepicker", ({date, oldDate}) => {
                                var shipment_date = new Date($("#shipmentdate").val()).setHours(0, 0, 0, 0);
                                if(shipment_date < today){
                                    $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                    if(oldDate && oldDate >= today)
                                        $("#shipmentdate").val(moment(oldDate).format('YYYY-MM-DD HH:mm'))
                                    else
                                        $("#shipmentdate").val(moment(new Date()).format('YYYY-MM-DD HH:mm'))
                                }else{                                
                                    $("#shipmentdateend").val(moment(date).format('YYYY-MM-DD  HH:mm'))
                                    $("#shipmentdateend").datetimepicker('minDate', moment(date).format('YYYY-MM-DD HH:mm'));
                                }
                            })
                            
                            $(".de-handling-instruction").change(function(e){
                                var handling_instruction =  $(e.currentTarget).val()
                                if(handling_instruction == 'service_area'){
                                    $('.handling-instruction-text').empty()
                                    $('.handling-instruction-text').append("<span>(Please make sure these items can fit into your service area; otherwise, special handling charges may apply or your items can be returned to sender at your expenses.)</span>")
                                }else{
                                    $('.handling-instruction-text').empty()
                                    $('.handling-instruction-text').append("<span>(Please confirm with operations for availability and maximum free storage days.  Your items can be returned to sender at your expenses or storage fees can apply.)</span>")
                                }
                            });

                        }else{
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }                                        
                    });
                }else{
                    this._rpc({
                        route: '/shipment',
                        params: {
                            project_id: project_id
                        }
                    }).then(function(result){
                        self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_new_shipment",result)));
                        $(".de-tooltips-popover").popover({
                            'container': $('.de-portal-form'),
                            'content' : 'For larger shipments please select the “Require Loading Dock” check box and our operations team will contact you with the arrangements. <a href="/customer-portal-user-guide?page=14" target="_blank">Read More...</a>',
                            'html': true,
                            'animation': false
                        }).on("mouseenter", function() {
                            var _this = this;
                            $(this).popover("show");
                            $(".popover").on("mouseleave", function() {
                                $(_this).popover('hide');
                            });
                        }).on("mouseleave", function() {
                            var _this = this;
                            setTimeout(function() {
                                if (!$(".popover:hover").length) {
                                $(_this).popover("hide");
                                }
                            }, 300);
                        });
                        
                        self.getTicketList();

                        $(".de-require-loading-dock").change(function(e){
                            var require_loading_dock =  $(e.currentTarget).val()
                            if(require_loading_dock == 'yes'){
                                $('#expecteddate').val('')
                                $('.de-expected-date').hide()
                                $('.de-shipment-date-range').show();
                                $( ".de-loading-dock" ).prop( "checked", true );
                            }else{
                                $('#shipmentdate').val('')
                                $('#shipmentdateend').val('')
                                $('.de-shipment-date-range').hide()
                                $('.de-expected-date').show()
                                $( ".de-loading-dock" ).prop( "checked", false );
                            }
                        });

                        $(".de-ticket-type-id").change(function(e){
                            if ($.trim($(e.currentTarget).find(":selected").text()) == 'Inbound'){
                                $(".de-form-box-handling-instruction").show();
                            }else{
                                $(".de-form-box-handling-instruction").hide();
                            }
                        });

                        $('#expecteddate').datetimepicker({
                            format: 'YYYY-MM-DD',
                            'date': $('#expecteddate').val(),
                            minDate: new Date().setHours(0, 0, 0, 0)
                        });
                        $('#expecteddate').click(function(){
                            $('#expecteddate').datetimepicker('toggle');
                        });

                        $("#shipmentdate, #shipmentdateend").each((i,el)=>{
                            $(el).datetimepicker({
                                format: 'YYYY-MM-DD HH:mm',
                                'date': $(el).val(),
                                minDate: new Date().setHours(0, 0, 0, 0)
                            });
                            $(el).click(function(){
                                $(el).datetimepicker('toggle');
                            });
                        });

                        $('#expecteddate').on("change.datetimepicker", ({date, oldDate}) => {
                            var exp_date = new Date($("#expecteddate").val()); 
                            var today = new Date();
                            if (exp_date.setHours(0, 0, 0, 0) < today.setHours(0, 0, 0, 0)){
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                if(oldDate && oldDate >= today.setHours(0, 0, 0, 0))
                                    $("#expecteddate").val(moment(oldDate).format('YYYY-MM-DD'))
                                else
                                    $("#expecteddate").val(moment(new Date()).format('YYYY-MM-DD'))
                            }
                        })

                        $('#shipmentdate').on("change.datetimepicker", ({date, oldDate}) => {
                            var shipment_date = new Date($("#shipmentdate").val());
                            var today = new Date();
                            if(shipment_date.setHours(0, 0, 0, 0) < today.setHours(0, 0, 0, 0)){
                                $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t('Cannot pick past dates!')})));
                                if(oldDate && oldDate >= today.setHours(0, 0, 0, 0))
                                    $("#shipmentdate").val(moment(oldDate).format('YYYY-MM-DD HH:mm'))
                                else
                                    $("#shipmentdate").val(moment(new Date()).format('YYYY-MM-DD HH:mm'))
                            }else{                                
                                $("#shipmentdateend").val(moment(date).format('YYYY-MM-DD HH:mm'))
                                $("#shipmentdateend").datetimepicker('minDate', moment(date).format('YYYY-MM-DD HH:mm'));
                            }
                        })
                        
                        $(".de-handling-instruction").change(function(e){
                            var handling_instruction =  $(e.currentTarget).val()
                            if(handling_instruction == 'service_area'){
                                $('.handling-instruction-text').empty()
                                $('.handling-instruction-text').append("<span>(Please make sure these items can fit into your service area; otherwise, special handling charges may apply or your items can be returned to sender at your expenses.)</span>")
                            }else{
                                $('.handling-instruction-text').empty()
                                $('.handling-instruction-text').append("<span>(Please confirm with operations for availability and maximum free storage days.  Your items can be returned to sender at your expenses or storage fees can apply.)</span>")
                            }
                        });
                        
                    });
                }
                
            },
            loadTicketListTableView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;
                this._rpc({
                    route: '/ticket-list-table',
                    params: {
                        order: this.activeRoute.order,
                        search_term: false,
                        limit: 20,
                        offset: 0
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_ticket_list_table",template_data)));
                    $('#de-search-input-tags').tagsInput({
                        'onAddTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if(column == "Ticket Name"){
                                    search_term.push('name' + '->' + value)
                                }else if(column == "Create By"){
                                    search_term.push('create_uid.name' + '->' + value)
                                }else if (column == "Create Date"){
                                    search_term.push('create_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Ticket Type"){
                                    search_term.push('ticket_type_id.name' + '->' + value)
                                }else if(column == "Status"){
                                    search_term.push('stage_id.name' + '->' + value)
                                }else if(column == "Last Update"){
                                    search_term.push('write_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Operation Site"){
                                    search_term.push('x_studio_operation_site.name' + '->' + value)
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'onRemoveTag': function(input, value) {
                            var search_term = []
                            $(".de-search-tag-keyword").each(function() {
                                var column = $(this).children( ".de-search-tag-column" ).text()
                                var value = $(this).children( ".de-search-tag-value" ).text()
                                if(column == "Ticket Name"){
                                    search_term.push('name' + '->' + value)
                                }else if(column == "Create By"){
                                    search_term.push('create_uid.name' + '->' + value)
                                }else if (column == "Create Date"){
                                    search_term.push('create_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Ticket Type"){
                                    search_term.push('ticket_type_id.name' + '->' + value)
                                }else if(column == "Status"){
                                    search_term.push('stage_id.name' + '->' + value)
                                }else if(column == "Last Update"){
                                    search_term.push('write_date' + '->' + self.formatSearchDate(value))
                                }else if(column == "Operation Site"){
                                    search_term.push('x_studio_operation_site.name' + '->' + value)
                                }
                            });
                            self.actionSetSearchTerm(search_term.length > 0 ? search_term.join('|') : false)
                        },
                        'searchCategory': {
                            source: [
                                'Ticket Name',                            
                                'Ticket Type',
                                'Operation Site',
                                'Create Date',
                                'Create By',
                                'Status',
                                'Last Update'
                            ]
                        },                        
                        'placeholder': _t('search')
                    });
                });            
            },
            updateOrderTicketListView: function(){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let highlight = urlParams.get('highlight') || '';
                var self = this;
                this._rpc({
                    route: '/ticket-list-table',
                    params: {
                        order: this.activeRoute.order,
                        search_term: this.activeRoute.searchTerm,
                        limit: 20,
                        offset: 0
                    }
                }).then(function(result){
                    var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                    self.$el.find(".de-portal-ticket-list-body").replaceWith($(qweb.render("nrs_de_portal.de_ticket_list_table_body",template_data)));
                    self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                });
            },
            getTicketList: function(){
                var self = this;
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let ticket_id = urlParams.get('ticket_id');
                let menu_id = urlParams.get('menu_id') || ''; 
                this._rpc({
                    route: '/ticket-list',
                    params: {
                        ticket_id: ticket_id,
                        menu_id: menu_id
                    }
                }).then(function(result){
                    $(".de-ticket-list-container").empty();
                    result.forEach(rec => {
                        if(rec['stage'] == 'Unassigned'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_unassigned'].toString() || rec['stage']
                        }else if(rec['stage'] == 'In Progress'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_in_progress'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Pending Customer'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_pending_customer'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Scheduled'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_scheduled'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Completed'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_completed'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Closed'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_closed'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Escalate'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_escalate'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Fix'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_fix'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Resolved'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_resolved'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Cancelled'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_cancelled'].toString() || rec['stage']
                        }else if(rec['stage'] == 'New'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_new'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Approved'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_approved'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Declined'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_declined'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Approved (Inbound)'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_approved_inbound'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Approved (Outbound)'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_approved_outbound'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Arrived'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_arrived'].toString() || rec['stage']
                        }else if(rec['stage'] == 'Dispatched'){
                            rec['stage'] = TRANSLATE_TERM['status_ticket_dispatched'].toString() || rec['stage']
                        }
                    })
                    $(".de-ticket-list-container").append($(qweb.render("nrs_de_portal.de_ticket_list",{'count': result.length, 'data': result, 'selected': ticket_id})));
                });
            },
            loadContactUs: function(){
                var self = this;
                this._rpc({
                    route: '/address/operation-site',
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_contact_container",result))); 
    
                    $(".de-map-marker-box").click(function(e){
                        var id = $(e.currentTarget).data("c-id");
                        var name = $(e.currentTarget).children("text").attr('id');
                        $(".de-search-input").val(name)
                        self._rpc({
                            route: '/search/operation-site',
                            params: {
                                country: id
                            }
                        }).then(function(result){
                            $(".de-contact-list").empty();
                            $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
                        });
                        e.stopImmediatePropagation()
                    });
    
                    $("#deportalmap").click(function(e){
                        var id = $(e.currentTarget).data("c-id");
                        var name = $(e.currentTarget).children("text").attr('id');
                        $(".de-search-input").val(name)
                        self._rpc({
                            route: '/search/operation-site',
                            params: {
                                country: ''
                            }
                        }).then(function(result){
                            $(".de-contact-list").empty();
                            $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
                        });
                    });
                });            
            },
            updateContact: function(){
                var self = this;
                self._rpc({
                    route: '/search/operation-site',
                    params: {
                        keyword: $(".de-search-input").val()
                    }
                }).then(function(result){
                    $(".de-contact-list").empty();
                    $(".de-contact-list").append($(qweb.render("nrs_de_portal.de_contact_list",result))); 
                });
            },
            openEmail: function(){
                var self = this;
                window.location.replace("mailto:portal-feedback@digitaledgedc.com");
            },
            loadFAQ: function(){
                var self = this;
                this._rpc({
                    route: '/documents/faq',
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_faq_document",result))); 
                });
            },
            updateFAQ: function(){
                var self = this;
                self._rpc({
                    route: '/search/documents/faq',
                    params: {
                        keyword: $(".de-search-input").val()
                    }
                }).then(function(result){
                    $(".de-faq-box").empty();
                    $(".de-faq-box").append($(qweb.render("nrs_de_portal.de_faq_document_detail",result))); 
                });
            },
            loadPolicies: function(){
                var self = this;
                this._rpc({
                    route: '/documents/policies',
                }).then(function(result){
                    self.$el.find(".de-portal-content").html($(qweb.render("nrs_de_portal.de_policies_document",result))); 
                });
            },
            updatePolicies: function(){
                var self = this;
                self._rpc({
                    route: '/search/documents/policies',
                    params: {
                        keyword: $(".de-search-input").val()
                    }
                }).then(function(result){
                    $(".de-policies-container").empty();
                    $(".de-policies-container").append($(qweb.render("nrs_de_portal.de_policies_document_detail",result))); 
                });
            },
            partnerIDChanged: function(e){
                var self = this;
                var partner_id = $(e.currentTarget).val();
                // $(".de-osite").empty();
                $(".de-service-id").empty();
                $(".de-ticket-type-id").empty();
                self._rpc({
                    route: '/get/operation-site',
                    params: {
                        partner_id: partner_id
                    }
                }).then(function(result){
                    $(".de-osite").append($(qweb.render("nrs_de_portal.de_operation_site_selection",result)));
                    if(result['data'].length == 1){
                       $(".de-osite").trigger("change"); 
                    }
                });
            },
            operationSiteChanged: function(e){
                var self = this;
                var partner_id = $(".de-partner-id").val();
                var operation_site = $(e.currentTarget).val();
                var timezone = $(e.currentTarget).find(":selected").attr('data-timezone');
                $(".de-date-timezone").replaceWith(`<span class="de-date-timezone">(UTC ${timezone})</span>`)
                $(".de-service-id").empty();
                $(".de-partner-id").empty();
                var product_categ = $(".de-service-id").data("product-categ");
                self._rpc({
                    route: '/get/service-id',
                    params: {
                        // partner_id: true,
                        operation_site: operation_site,
                        product_categ: product_categ,
                        menu: self.activeRoute['menu_id']
                    }
                }).then(function(result){
                    $(".de-service-id").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                    $(".de-service-id").trigger("change");
                });
    
                if($(e.currentTarget).hasClass("de-update-ticket-type")){
                    var team = $(e.currentTarget).data("team-name");
                    $(".de-ticket-type-id").empty();
                    self._rpc({
                        route: '/get/ticket-type',
                        params: {
                            operation_site: operation_site,
                            team: team
                        }
                    }).then(function(result){
                        $(".de-ticket-type-id").append($(qweb.render("nrs_de_portal.de_ticket_type_selection",result)));
                    });
                }
            },
            serviceIDChanged: function(e){
                var self = this;
                var service_id = $(e.currentTarget).val(); 
                var z_service_id = $(".de-service-id-z").val(); 
    
                var queryString = window.location.hash.substring(1);
                var urlParams = new URLSearchParams(queryString);
                var menu_id = urlParams.get('menu_id') || '';  
    
                $(".de-partner-id").empty();

                if (service_id == "other"){                    
                    // $(".de-service-id").empty();
                    // $(".de-partner-id").empty();
                    var operation_site = $(".de-osite").val();
                    var product_categ = $(".de-service-id").data("product-categ");
                    self._rpc({
                        route: '/get/service-id-popup',
                        params: {
                            operation_site: operation_site,
                            product_categ: product_categ,
                            menu: self.activeRoute['menu_id'],                                                    
                            limit: 20,
                            offset: 0
                        }
                    }).then(function(result){  
                        var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-id'}
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_service_selection_popup", template_data)));
                        $(".de-close-service-id-selection-dialog").click((e)=>{
                            $(".de-service-id").empty();
                            self._rpc({
                                route: '/get/service-id',
                                params: {
                                    operation_site: operation_site,
                                    product_categ: product_categ,
                                    menu: self.activeRoute['menu_id']
                                }
                            }).then(function(result){
                                $(".de-service-id").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                                $(".de-service-id").trigger("change");
                            });
                        })
                    });
                }else{
                    self._rpc({
                        route: '/get/company-id',
                        params: {
                            service_id: service_id
                        }
                    }).then(function(result){
                        $(".de-partner-id").append($(qweb.render("nrs_de_portal.de_company_id_selection",result)));
                        if(result['data'].length == 1){
                            $(".de-partner-id").trigger("change"); 
                        }
                    });
                }
            },
            serviceIDZChanged: function(e){
                var self = this;
                var service_id = null; 
                var z_service_id = null;
                var is_intra_customer = false;
                if ($(".de-intra-customer").is(":checked")){
                    is_intra_customer = true;
                    service_id = $(".de-service-id").val(); 
                    z_service_id = $(".de-service-id-z-select").val(); 

                    if (z_service_id == "other"){ 
                        var operation_site = $(".de-osite").val();
                        var product_categ = $(".de-service-id").data("product-categ");
                        self._rpc({
                            route: '/get/service-id-popup',
                            params: {
                                operation_site: operation_site,
                                product_categ: product_categ,
                                menu: self.activeRoute['menu_id'],                                                    
                                limit: 20,
                                offset: 0
                            }
                        }).then(function(result){  
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-z-id'}
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_service_z_selection_popup", template_data)));
                            $(".de-close-service-id-selection-dialog").click((e)=>{
                                $(".de-service-id-z-select").empty();
                                self._rpc({
                                    route: '/get/service-id',
                                    params: {
                                        operation_site: operation_site,
                                        product_categ: product_categ,
                                        service_id: service_id, 
                                        menu: self.activeRoute['menu_id']
                                    }
                                }).then(function(result){
                                    $(".de-service-id-z-select").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                                });
                            })
                        });
                    }
                    
                }else{                    
                    service_id = $(".de-service-id").val(); 
                    z_service_id = $(".de-service-id-z").val(); 
                }

                
            },
            openTicket: function(e){
                var ticket_id = $(e.currentTarget).data("ticket-id");
                var team = $(e.currentTarget).data("team");
    
                if(team.indexOf("Remote Hands") >= 0){
                    window.location.hash = '#menu_id=remote-hands&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(team.indexOf("Fault Report") >= 0){
                    window.location.hash = '#menu_id=new-fault-report-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(team.indexOf("Site Access") >= 0){
                    window.location.hash = '#menu_id=new-site-access-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(team.indexOf("Shipment") >= 0){
                    window.location.hash = '#menu_id=new-shipment-ticket&action=read&ticket_id=' + ticket_id;
                    this.updateMainView();
                }
            },
            openFormEdit: function(e){
                var ticket_id = $(e.currentTarget).data("ticket-id");
    
                if(this.activeRoute['menu_id'] == 'remote-hands'){
                    window.location.hash = '#menu_id=remote-hands&action=edit&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(this.activeRoute['menu_id'] == 'new-fault-report-ticket'){
                    window.location.hash = '#menu_id=new-fault-report-ticket&action=edit&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(this.activeRoute['menu_id'] == 'new-site-access-ticket'){
                    window.location.hash = '#menu_id=new-site-access-ticket&action=edit&ticket_id=' + ticket_id;
                    this.updateMainView();
                }else if(this.activeRoute['menu_id'] == 'new-shipment-ticket'){
                    window.location.hash = '#menu_id=new-shipment-ticket&action=edit&ticket_id=' + ticket_id;
                    this.updateMainView();
                }
            },
            minimizeNotificationBox: function(e){
                if($(e.currentTarget).hasClass("de-minimize")){
                    $(e.currentTarget).removeClass("de-minimize");
                    $(e.currentTarget).parent().removeClass("de-notification-box-minimize");
                    $(e.currentTarget).prev(".de-notification-body").removeClass("de-hide");
                    $(e.currentTarget).next(".de-notification-hide").removeClass("de-hide");
                }else{
                    $(e.currentTarget).addClass("de-minimize");
                    $(e.currentTarget).parent().addClass("de-notification-box-minimize");
                    $(e.currentTarget).prev(".de-notification-body").addClass("de-hide");
                    $(e.currentTarget).next(".de-notification-hide").addClass("de-hide");
                }
            },
            openDocument: function(e){
                e.preventDefault();
                e.stopPropagation();
                window.location.hash = $(e.currentTarget).attr("href");
                this.updateMainView();
            },
            hideNotificationBox: function(e){
                var self = this;            
                self._rpc({
                    route: '/hide/notification',
                    params: {
                        notif_id: $(e.currentTarget).data("notification-id")
                    }
                }).then(function(result){
                    $(e.currentTarget).parent().parent().remove();
                });
            },
            hideMessageBox: function(e){
                var self = this;            
                self._rpc({
                    route: '/hide/message',
                    params: {
                        message_id: $(e.currentTarget).data("message-id")
                    }
                }).then(function(result){
                    $(e.currentTarget).parent().remove();
                    var message_count = $(".de-ticket-list-count span").text();
                    message_count = parseInt(message_count) -1;
                    $(".de-ticket-list-count span").text(message_count);
                });
            },
            replyTicketMessage: function(e){
                var self = this;
                var message = $(".de-ticket-log-chat-input").val();
                var ticket_id = $(e.currentTarget).data("ticket-id");
                var attachment = [];
                $(".de-ticket-log-file-data").each(function(){
                    attachment.push({
                        'data': $(this).val(),
                        'filename': $(this).data("filename")
                    });
                });
                
                self._rpc({
                    route: '/ticket/reply',
                    params: {
                        message: message,
                        ticket_id: ticket_id,
                        attachment: attachment
                    }
                }).then(function(result){
                    if(result['status'] == 'allowed'){                        
                        $(".de-ticket-log").empty();
                        $(".de-ticket-log").append($(qweb.render("nrs_de_portal.de_ticket_log",result)));
                        if(result['message'] != "" ){
                            $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                        }
                    }else{
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message': _t(result['message'])})));
                    }
                });
            },
            selectTicketAttachment: function(e){
                var self = this;
                var files = e.currentTarget.files;
                var getTicketFileBase64 = function(file) {
                  return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = () => resolve({data: reader.result, filename: file.name});
                    reader.onerror = error => reject(error);
                  });
                };
                var fileName = '';
                for(var i = 0; i < files.length; i++){
                    var filesize = ((files[i].size/1024)/1024).toFixed(4);
                    if (filesize > 2){
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_alert",{'message':_t('maximum file size exceeded 2mb ,' + files[i].name)})));
                        $('.de-file-input').val(null);
                    }else{
                        getTicketFileBase64(files[i]).then(
                            function(result){                
                                $(".de-ticket-log-file-container").append($(qweb.render("nrs_de_portal.de_ticket_log_file",{data: result['data'].split(",")[1], filename: result['filename']})));
                            }
                        );
                    }
                   
                }
            },
            deleteTicketFile: function(e){
                $(e.currentTarget).parent().remove();
            },
            showEmoji: function(e){
                if($(".de-emoji-container").hasClass("de-hide")){
                    $(".de-emoji-container").removeClass("de-hide");
                    $(".de-emoji-container").empty();
                    $(".de-emoji-container").append($(qweb.render("nrs_de_portal.de_emoji_popover",{emojis: emojis})));
                }else{
                    $(".de-emoji-container").addClass("de-hide");
                }            
            },
            selectEmoji: function(e){
                var emoji = $(e.currentTarget).data("unicode");
                $(".de-emoji-container").addClass("de-hide");
                var currentPos = document.getElementById("deticketlogchatinput").selectionStart;
                var currentValue = $(".de-ticket-log-chat-input").val();
                $(".de-ticket-log-chat-input").val(currentValue.slice(0, currentPos) + emoji + currentValue.slice(currentPos));
                document.getElementById("deticketlogchatinput").setSelectionRange(currentPos+emoji.length, currentPos+emoji.length)
                $(".de-ticket-log-chat-input").focus();
            },
            scrollToHighlightedRow: function(){
            },
            updateAccordionView: function(e){
                if($(e.currentTarget).hasClass("collapsed")){
                    $(e.currentTarget).children(".de-faq-chevron").removeClass("fa-chevron-right");
                    $(e.currentTarget).children(".de-faq-chevron").addClass("fa-chevron-down");
                }else{
                    $(e.currentTarget).children(".de-faq-chevron").removeClass("fa-chevron-down");
                    $(e.currentTarget).children(".de-faq-chevron").addClass("fa-chevron-right");                
                }
            },
            updateInputColor: function(e){
                if($(e.currentTarget).val().length > 0){
                    $(e.currentTarget).addClass("de-valid-input");
                }else{
                    $(e.currentTarget).removeClass("de-valid-input");
                }
            },
            action2FA: function(e){
                var action = $(e.currentTarget).data("action");
                $(".de-portal").append($(qweb.render("nrs_de_portal.de_need_password",{action: action})));
            },
            actionLogout: function(e){
                e.preventDefault()
                e.stopPropagation();
                utils.set_cookie('acids','');
                this._rpc({
                    route: '/portal/update-acids'
                }).then(function(result){
                    window.location = $(e.currentTarget).attr("href");
                });
            },
            addVisitorInput: function(e){
                let queryString = window.location.hash.substring(1);
                let urlParams = new URLSearchParams(queryString);
                let action = urlParams.get('action') || '';
                
                var first_length = $(".de-form-input-box-visitor").length;
                if (first_length <= 5){
                    $(e.currentTarget).parent().parent().after(`
                        <div class="de-form-box de-form-box-visitor" style="position: relative">
                            <span class="de-form-label de-form-label-extra"></span>
                            <span class="de-form-input-box ${action == 'edit' ? 'de-form-input-box-edit' : ''} de-form-input-box-visitor d-flex">

                                <input type="text" name="x_studio_requested_visitor" required="required" placeholder="Visitor Name ..." class="de-form-input de-form-input-visitor" data-toggle="popover" data-trigger="focus"/>                    
                                <button class="btn btn-default d-flex align-items-center add-visitor-btn"><span class="fa fa-plus"/></button>
                            </span>
                        </div>
                    `)
                }                            
                var after_append_length = $(".de-form-input-box-visitor").length;
                if (after_append_length < 5){
                    $(".de-form-input-box-visitor").each(function(i, e){
                        if(i < after_append_length - 1){
                            $(e).find(".add-visitor-btn").remove()
                            $(e).find(".remove-visitor-btn").remove()
                            $(e).append(`<button class="btn btn-default d-flex align-items-center remove-visitor-btn"><span class="fa fa-close"/></button>`)
                        }
                    })
                }else{
                    $(".de-form-input-box-visitor").each(function(i, e){
                        $(e).find(".add-visitor-btn").remove()
                        $(e).find(".remove-visitor-btn").remove()
                        $(e).append(`<button class="btn btn-default d-flex align-items-center remove-visitor-btn"><span class="fa fa-close"/></button>`)
                    })
                }

               
            },
            removeVisitorInput: function(e){                
                $(e.currentTarget).parent().parent().remove()
                var input_length = $(".de-form-input-box-visitor").length;
                $(".de-form-input-box-visitor").each(function(i, e){                    
                    $(e).find(".add-visitor-btn").remove()
                    $(e).find(".remove-visitor-btn").remove()
                    
                    if(i < input_length - 1){
                        $(e).append(`<button class="btn btn-default d-flex align-items-center remove-visitor-btn"><span class="fa fa-close"/></button>`)
                    }else{                      
                        $(e).append(`<button class="btn btn-default d-flex align-items-center add-visitor-btn"><span class="fa fa-plus"/></button>`)
                    }
                })
                $(".de-form-box-visitor:first").removeClass( "required" );
                $(".de-form-box-visitor:first").addClass("required")
                $(".de-form-box-visitor:first").children('.de-form-label').html("Requested Visitor's Name")

            },
            actionPaginationNext: function(e){
                var self = this;                
                var pagination_info = $('.de-pagination-info')
                var limit = pagination_info.attr("data-limit")
                var offset = pagination_info.attr("data-offset")
                var total = pagination_info.attr("data-total")
                var type = pagination_info.attr("data-type")
                if((parseInt(offset) + parseInt(limit)) < total){                    
                    if(self.activeRoute['menu_id'] == 'under-provisioning'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        this._rpc({
                            route: '/order/under-provisioning',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-wip-body").replaceWith($(qweb.render("nrs_de_portal.de_order_wip_table_body", template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'installed-services'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/order/installed',
                            params: {
                                order: this.activeRoute.order,
                                keyword: this.activeRoute.keyword,
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-installed-body").replaceWith($(qweb.render("nrs_de_portal.de_order_installed_table_body",template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'invoice'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/invoice',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'user_company': result['user_company'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-invoice-body").replaceWith($(qweb.render("nrs_de_portal.de_invoice_table_body",template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'ticket-list-table'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/ticket-list-table',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-ticket-list-body").replaceWith($(qweb.render("nrs_de_portal.de_ticket_list_table_body",template_data)));                            
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(type == "popup-service-id"){
                        var operation_site = $(".de-osite").val();
                        var product_categ = $(".de-service-id").data("product-categ");
                        self._rpc({
                            route: '/get/service-id-popup',
                            params: {
                                operation_site: operation_site,
                                product_categ: product_categ,
                                menu: self.activeRoute['menu_id'],                                                    
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){  
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-id'}                            
                            self.$el.find(".de-service-id-selection-dialog").replaceWith($(qweb.render("nrs_de_portal.de_service_selection_popup", template_data)));
                        });
                    }else if(type == "popup-service-z-id"){
                        var operation_site = $(".de-osite").val();
                        var product_categ = $(".de-service-id").data("product-categ");
                        self._rpc({
                            route: '/get/service-id-popup',
                            params: {
                                operation_site: operation_site,
                                product_categ: product_categ,
                                menu: self.activeRoute['menu_id'],
                                service_id: $(".de-service-id").val(),                                                    
                                limit: 20,
                                offset: parseInt(offset) + parseInt(limit)
                            }
                        }).then(function(result){  
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-z-id'}                            
                            self.$el.find(".de-service-id-selection-dialog").replaceWith($(qweb.render("nrs_de_portal.de_service_z_selection_popup", template_data)));
                        });
                    }
                }
            },
            actionPaginationPrev: function(e){
                var self = this;                
                var pagination_info = $('.de-pagination-info')
                var limit = pagination_info.attr("data-limit")
                var offset = pagination_info.attr("data-offset")
                var type = pagination_info.attr("data-type")
                if((parseInt(offset) - parseInt(limit)) >= 0){
                    if(self.activeRoute['menu_id'] == 'under-provisioning'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        this._rpc({
                            route: '/order/under-provisioning',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-wip-body").replaceWith($(qweb.render("nrs_de_portal.de_order_wip_table_body", template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'installed-services'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/order/installed',
                            params: {
                                order: this.activeRoute.order,
                                keyword: this.activeRoute.keyword,
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-installed-body").replaceWith($(qweb.render("nrs_de_portal.de_order_installed_table_body",template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'invoice'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/invoice',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'user_company': result['user_company'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-invoice-body").replaceWith($(qweb.render("nrs_de_portal.de_invoice_table_body",template_data)));
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(self.activeRoute['menu_id'] == 'ticket-list-table'){
                        let queryString = window.location.hash.substring(1);
                        let urlParams = new URLSearchParams(queryString);
                        let highlight = urlParams.get('highlight') || '';
                        var self = this;
                        this._rpc({
                            route: '/ticket-list-table',
                            params: {
                                order: this.activeRoute.order,
                                search_term: this.activeRoute.searchTerm,
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'highlight': highlight}
                            self.$el.find(".de-portal-ticket-list-body").replaceWith($(qweb.render("nrs_de_portal.de_ticket_list_table_body",template_data)));                            
                            self.$el.find(".de-pagination").replaceWith($(qweb.render("nrs_de_portal.de_pagination", template_data)));
                        });
                    }else if(type == "popup-service-id"){
                        var operation_site = $(".de-osite").val();
                        var product_categ = $(".de-service-id").data("product-categ");
                        self._rpc({
                            route: '/get/service-id-popup',
                            params: {
                                operation_site: operation_site,
                                product_categ: product_categ,
                                menu: self.activeRoute['menu_id'],                                                    
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){  
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-id'}                            
                            self.$el.find(".de-service-id-selection-dialog").replaceWith($(qweb.render("nrs_de_portal.de_service_selection_popup", template_data)));
                        });
                    }else if(type == "popup-service-z-id"){
                        var operation_site = $(".de-osite").val();
                        var product_categ = $(".de-service-id").data("product-categ");
                        self._rpc({
                            route: '/get/service-id-popup',
                            params: {
                                operation_site: operation_site,
                                product_categ: product_categ,
                                menu: self.activeRoute['menu_id'],
                                service_id: $(".de-service-id").val(),                                                    
                                limit: 20,
                                offset: parseInt(offset) - parseInt(limit)
                            }
                        }).then(function(result){  
                            var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-service-z-id'}                            
                            self.$el.find(".de-service-id-selection-dialog").replaceWith($(qweb.render("nrs_de_portal.de_service_z_selection_popup", template_data)));
                        });
                    }

                }
            },
            formatSearchDate: function(input){

                var arrayValue = input.split(' or ')
                var returnArray = []

                arrayValue.forEach((value, index) => {
                    var date_string = value;

                    if (/[0-9]{2}\/[0-9]{2}\/[0-9]{4}/g.test(value)){
                        var temp_value = value.split("/")
                        date_string = temp_value[2] + '-' + temp_value[1] + '-' + temp_value[0]
                    }else if(/[0-9]{2}\/[0-9]{4}/g.test(value)){
                        var temp_value = value.split("/")
                        date_string = temp_value[1] + '-' + temp_value[0]
                    }else if(/[0-9]{2}\/[0-9]{2}/g.test(value)){
                        var temp_value = value.split("/")
                        date_string = temp_value[1] + '-' + temp_value[0]
                    }

                    returnArray.push(date_string)

                })

                return returnArray.join(' or ')
            },
            servicePopupSelect: function(e){
                var self = this;
                var service_id = $(e.currentTarget).data("service-id");
                var service_name = $(e.currentTarget).data("name");
                var partner = $(e.currentTarget).data("partner");

                var operation_site = $(".de-osite").val();
                var product_categ = $(".de-service-id").data("product-categ");                

                self._rpc({
                    route: '/get/service-id',
                    params: {
                        // partner_id: true,
                        operation_site: operation_site,
                        product_categ: product_categ,
                        menu: self.activeRoute['menu_id'],
                        additionalData: {
                            'fromPopup' : true,
                            'service_id' : service_id,
                            'service_name' : service_name,
                            'partner' : partner                             
                        }
                    }
                }).then(function(result){
                    $(".de-dialog-container").remove(); 
                    $(".de-service-id").empty();
                    $(".de-partner-id").empty();
                    $(".de-service-id").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                    $(".de-service-id").trigger("change");
                });
            },
            serviceZPopupSelect: function(e){
                var self = this;
                var service_id = $(e.currentTarget).data("service-id");
                var service_name = $(e.currentTarget).data("name");
                var partner = $(e.currentTarget).data("partner");

                var operation_site = $(".de-osite").val();
                var product_categ = $(".de-service-id").data("product-categ");                

                self._rpc({
                    route: '/get/service-id',
                    params: {
                        // partner_id: true,
                        operation_site: operation_site,
                        product_categ: product_categ,
                        menu: self.activeRoute['menu_id'],
                        service_id: $(".de-service-id").val(),  
                        additionalData: {
                            'fromPopup' : true,
                            'service_id' : service_id,
                            'service_name' : service_name,
                            'partner' : partner                             
                        }
                    }
                }).then(function(result){
                    $(".de-dialog-container").remove(); 
                    $(".de-service-id-z-select").empty();
                    $(".de-service-id-z-select").append($(qweb.render("nrs_de_portal.de_service_id_selection",result)));
                });
            },
            changePrivacyPolicyAgreement: function(e){
                var self = this
                $(".de-portal").append($(qweb.render("nrs_de_portal.de_change_agreement")));
                $(".de-uncheck-policy-agreement").click(function(e){
                    self._rpc({
                        route: '/user/uncheck-policy-agreement'
                    }).then(function(result){
                        window.location.href = "/portal"
                    });
                })
            },
            masterUserFilterInactive: function(e){
                var self = this;
                var status = $(e.currentTarget).attr('data-filter')

                if(status == 'true'){
                    $(e.currentTarget).attr('data-filter', 'false');
                    $(e.currentTarget).css("background-color","white");
                    $(e.currentTarget).css("color","#3D3D3D");
                    $(".de-master-user-delete").text("Delete User");
                    self.activeRoute['master_user_show_inactive'] = false
                }else{
                    $(e.currentTarget).attr('data-filter', 'true');
                    $(e.currentTarget).css("background-color","#3D3D3D");
                    $(e.currentTarget).css("color","white");
                    $(".de-master-user-delete").text("Activate User");
                    self.activeRoute['master_user_show_inactive'] = true
                }
                                     
                self._rpc({
                    route: '/user/associated',
                    params: {
                        show_inactive: self.activeRoute['master_user_show_inactive']
                    }
                }).then(function(result){

                    self.$el.find(".de-master-user-left").empty()

                    var first_partner = result['data']['associated_company'][Object.keys(result['data']['associated_company'])[0]];
                    self.$el.find(".de-master-user-left").append($(qweb.render("nrs_de_portal.de_portal_user_profile",first_partner)));

                    self.$el.find(".de_portal_master_user_body").replaceWith($(qweb.render("nrs_de_portal.de_portal_table_master_user_body",result['data'])));
                    
                    self.activeRoute['data'] = result['data'];
                    self.activeRoute['old_data'] = JSON.parse(JSON.stringify(result['data']));
                })
            },
            addTableLine: function(e){
                var table_name = $(e.currentTarget).attr('data-table-name')

                if (table_name == "shipment-detail"){
                    this._rpc({
                        route: '/get/uom'
                    }).then(function(res){
                       var random_number = Math.floor((Math.random() * 100) + 1);
                        var text = ''
                        $.each(res.data,function(index,value){
                            text +=  '<option value="'+value['id']+'">'+value['name']+'</option>';              
                        })
                        $(".shipment-detail-table-add-line").remove();
                        $(".shipment-detail-table-body").append(`
                            <tr class="shipment-detail-table-row" data-shipment-detail-id="new">
                                <td><input type="number" name="ns_shipment_detail_item_number" class="de-form-table-input detail-item-number" placeholder="Number Input..."/></td>
                                <td><input type="text" name="ns_shipment_detail_dimension" class="de-form-table-input detail-dimension" placeholder="Text Input..."/></td>
                                <td><input type="number" name="ns_shipment_detail_weight" class="de-form-table-input detail-weight" placeholder="Number Input..."/></td>
                                <td>
                                        <select name="ns_uom" id="new`+random_number+`" class="de-form-select custom-select detail-weight-id" required="required" style="width: 150px">
                                                <option value="">Select ...</option>`
                                                +text+
                                        `</select>
                                </td>
                                <td><input type="text" name="ns_shipment_detail_tracking_number" class="de-form-table-input detail-tracking-number" placeholder="Text Input..."/></td>
                                <td class="table-tool"><button class="btn btn-sm btn-danger de-remove-table-line" data-table-name="shipment-detail"><span class="fas fa-times"/></button></td>
                            </tr>  
                        `); 
                        $(".shipment-detail-table-body").append( `
                            <tr class="shipment-detail-table-add-line">
                                <td colspan="5">
                                    <span class="de-table-add-line"  data-table-name="shipment-detail">
                                        <span class="fas fa-plus"/> add line ...
                                    </span>
                                </td>                                        
                            </tr>
                        `);
                    });
                }
                if (table_name == "site-acces-detail"){
                    $(".site-acces-detail-table-add-line").remove();
                    $(".site-acces-detail-table-body").append( `
                        <tr class="site-acces-detail-table-row de-form-box-visitor" data-site-acces-detail-id="new">
                        <td><input type="text" name="ns_site_access_detail_visitor_name" class="de-form-table-input de-form-input-visitor detail-visitor-name" placeholder="Text Input..." data-toggle="popover" data-trigger="focus"/></td>
                        <td><input type="text" name="ns_site_access_detail_visitor_id_nUmber" class="de-form-table-input detail-visitor-id-number" placeholder="Text Input..."/></td>
                            <td class="table-tool"><button class="btn btn-sm btn-danger de-remove-table-line" data-table-name="site-acces-detail"><span class="fas fa-times"/></button></td>
                        </tr>  
                    `);
                    $(".site-acces-detail-table-body").append( `
                        <tr class="site-acces-detail-table-add-line">
                            <td colspan="5">
                                <span class="de-table-add-line"  data-table-name="site-acces-detail">
                                    <span class="fas fa-plus"/> add line ...
                                </span>
                            </td>                                        
                        </tr>
                    `);
                }
                $(".de-form-input-visitor").popover({
                    'container': $('.de-form-box-visitor'),
                    'content' : TRANSLATE_TERM['tooltip_fault_report_visitor_name'].toString(),
                    'trigger': 'focus',
                    'placement' : 'right' 
                });
            },
            removeTableLine: function(e){
                var temp_deleted_route = this.activeRoute['deleted_shipment_detail']
                var table_name = $(e.currentTarget).attr('shipment-detail-table-row')                
                var record_id = $(e.currentTarget).parent().parent().attr('data-shipment-detail-id')
                if(record_id != 'new'){                    
                    temp_deleted_route.push($(e.currentTarget).parent().parent().attr('data-shipment-detail-id'))
                }
                if (table_name == "site-acces-detail") {
                  
                    var temp_deleted_route = this.activeRoute['deleted_access_detail']
                    var table_name = $(e.currentTarget).attr('site-acces-detail-table-row')                
                    var record_id = $(e.currentTarget).parent().parent().attr('data-site-acces-detail-id')
                    if(record_id != 'new'){                    
                        temp_deleted_route.push($(e.currentTarget).parent().parent().attr('data-site-acces-detail-id'))
                    }
                    this.activeRoute['deleted_access_detail'] = temp_deleted_route
                    console.log($(e.currentTarget).parent().parent().attr('data-site-acces-detail-id'))
                    $(e.currentTarget).parent().parent().remove()
                }
               
            },
            uomChanged: function(e){
                var self = this;
                var uom = $(e.currentTarget).val(); 
                var detail_id = $(e.currentTarget).attr('id');

                if (uom == "other"){                    
                    self._rpc({
                        route: '/get/uom-popup',
                        params: {                                                 
                            limit: 20,
                            offset: 0
                        }
                    }).then(function(result){  
                        var template_data = {'data': result['data'], 'offset': result['offset'], 'limit': result['limit'], 'total': result['total'], 'pagination_type': 'popup-uom','selectid':detail_id}
                        $(".de-portal").append($(qweb.render("nrs_de_portal.de_uom_selection_popup", template_data)));
                        $(".de-close-uom-id-selection-dialog").click((e)=>{
                            $(e.currentTarget).empty();
                            self._rpc({
                                route: '/get/uom',
                            }).then(function(result){
                                $(e.currentTarget).append($(qweb.render("nrs_de_portal.de_shipment_detail_uom",result)));
                                $(e.currentTarget).trigger("change");
                            });
                        })
                    });
                }
            },
            uomPopupSelect: function(e){
                var self = this;
                var uom_id = $(e.currentTarget).data("uom-id");
                var uom_name = $(e.currentTarget).data("name");
                var id = $(e.currentTarget).data('id'); 
                self._rpc({
                    route: '/get/uom',
                    params: {
                        additionalData: {
                            'fromPopup' : true,
                            'uom_id' : uom_id,
                            'uom_name' : uom_name,                    
                        }
                    }
                }).then(function(result){
                    $("#"+id).empty()
                    $("#"+id).empty()
                    $("#"+id).append($(qweb.render("nrs_de_portal.de_shipment_detail_uom",result)));
                    $("#"+id).trigger("change");
                    $(".de-dialog-container").remove();
                    
                   
                });
            },
        });
    
    
    });