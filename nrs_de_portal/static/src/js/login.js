odoo.define('nrs_de_portal.login', function (require) {
    'use strict';
    
        var publicWidget = require('web.public.widget');
    
        publicWidget.registry.deLogin = publicWidget.Widget.extend({
            selector: ".de-login-container",
            events: {
                'click .de-lang-box': 'showLanguageSelector',
                'click .de-lang-item': 'selectLanguage',
                'click .de-show-password': 'showPassword',
                'click .de-login-portal-preview': 'showCarousel',
                'click .de-hide-caraousel': 'hideCarousel'
            },
            start: function () {
                this._super.apply(this, arguments);
                
                var frontend_lang = "en_US";
                var cookies = document.cookie.split(";");
                for(var i = 0; i < cookies.length; i++){
                    var item = cookies[i].split("=");
                    if(item[0].trim() == "frontend_lang"){
                        frontend_lang = item[1].trim();
                    }
                }
                $(".de-lang-item").each(function(item){
                    if($(this).data("lang-url-code") == frontend_lang){
                        $(".de-lang-text").text($(this).text());
                    }
                    $(this).attr("href", "/" + $(this).data("lang-url-code") + $(this).attr("href"));
                });

                var rememberMe = localStorage.getItem(btoa('remember-me'))

                if (rememberMe || rememberMe == 'true'){
                    var email = localStorage.getItem(btoa('user-login-email'))
                    // var password = localStorage.getItem(btoa('user-login-password'))

                    $(".de-remember-me-checkbox").prop( "checked", true );
                    
                    $(".de-login-email").val(atob(email))
                    // $(".de-login-password").val(atob(password))
                }

                $(".de-remember-me-checkbox").change(function() {
                    if(!this.checked) {
                        localStorage.removeItem(btoa('remember-me'))
                        localStorage.removeItem(btoa('user-login-email'))
                        // localStorage.removeItem(btoa('user-login-password'))
                    }
                });

                $(".de-btn-login").click(function(e){
                    if ($(".de-remember-me-checkbox").is(":checked")){
                        var email = $(".de-login-email").val()
                        // var password = $(".de-login-password").val()                        

                        localStorage.setItem(btoa('remember-me'), true)
                        localStorage.setItem(btoa('user-login-email'), btoa(email))
                        // localStorage.setItem(btoa('user-login-password'), btoa(password))
                    }
                })

                $(".de-policy-agreement-checkbox").change(function(e){
                    if ($(".de-policy-agreement-checkbox").is(":checked")){
                        $(".de-btn-sign-up").removeAttr("disabled");
                        $(".de-btn-sign-up").css('background-color','#3D3D3D');
                    }else{                        
                        $(".de-btn-sign-up").attr("disabled", true);
                        $(".de-btn-sign-up").css('background-color','#aaaaaa');
                    }
                })
                var label = 'Customer Portal'
                var url = window.location.href

                if(url.includes("portal")){
                    $(".o_login_auth").addClass("de-hide");
                }
                
                if(url.includes("odoo-ps-pshk-digital-edge-dc-ns-staging-3126446.dev.odoo.com"))
                    label = 'Business Operations Support System';
                else if(url.includes("staging-nurosoft.odoo.com"))
                    label = 'Customer Portal';
                else if(url.includes("boss.digitaledgedc.com"))
                    label = 'Business Operations Support System';
                else if(url.includes("portal.digitaledgedc.com"))
                    label = 'Customer Portal';
                else if(url.includes("boss-staging.digitaledgedc.com"))
                    label = 'Business Operations Support System';
                else if(url.includes("portal-staging.digitaledgedc.com"))
                    label = 'Customer Portal';

                var image_path = "/nrs_de_portal/static/src/img/de-logo-vertical.png"

                if(url.includes("portal.chuanjunnet.cn"))
                    image_path = "/nrs_de_portal/static/src/img/chuanjun-logo-vertical.png"
                else if(url.includes("portal-staging.chuanjunnet.cn"))
                    image_path = "/nrs_de_portal/static/src/img/chuanjun-logo-vertical.png"

                $('.de-login-logo').attr('src',image_path);
                $(".de-login-label").text(label)
            },
            showCarousel: function(e){
                e.preventDefault();
                $(".de-carousel-box").removeClass("de-hide");
            },
            hideCarousel: function(e){
                e.preventDefault();
                $(".de-carousel-box").addClass("de-hide");
            },
            showPassword: function(e){
                if($(e.currentTarget).hasClass('de-ic-eyes-slash')){
                    $(e.currentTarget).prev(".de-password-input").css({"font-family":"inherit","top":""});
                    $(e.currentTarget).removeClass('de-ic-eyes-slash');
                    $(e.currentTarget).addClass('de-ic-eyes');
                }else{
                    $(e.currentTarget).prev(".de-password-input").css({"font-family":"text-security-disc","top":"8px"});
                    $(e.currentTarget).removeClass('de-ic-eyes');
                    $(e.currentTarget).addClass('de-ic-eyes-slash');
                }
            },
            showLanguageSelector: function(e){
                e.preventDefault();
                if($(e.currentTarget).hasClass("de-unselect-language")){
                    $(e.currentTarget).removeClass("de-unselect-language");
                    $(e.currentTarget).addClass("de-select-language");
                    $(".de-lang-selector").removeClass("de-hide");
                }else{
                    $(e.currentTarget).removeClass("de-select-language");
                    $(e.currentTarget).addClass("de-unselect-language");
                    $(".de-lang-selector").addClass("de-hide");
                }
            },
            selectLanguage: function(e){            
                window.location = $(e.currentTarget).attr("href");
            }
        });
    
    
    });