// Mixpanel JSONP

(function(d,c){var a,b,g,e;a=d.createElement("script");a.type="text/javascript";
a.async=!0;a.src=("https:"===d.location.protocol?"https:":"http:")+
'//mixpanel.com/site_media/js/api/mixpanel.2.js';b=d.getElementsByTagName("script")[0];
b.parentNode.insertBefore(a,b);c._i=[];c.init=function(a,d,f){var b=c;
"undefined"!==typeof f?b=c[f]=[]:f="mixpanel";g=['disable','track','track_links',
'track_forms','register','register_once','unregister','identify','name_tag','set_config'];
for(e=0;e<g.length;e++)(function(a){b[a]=function(){b.push([a].concat(
Array.prototype.slice.call(arguments,0)))}})(g[e]);c._i.push([a,d,f])};window.mixpanel=c}
)(document,[]);

var MPTracker = (function () {

    var _JUNK_VALUE = "Null",
        _SIGNED_IN;
    if (!Constants.uid) {
        _SIGNED_IN = "False";
    } else {
        _SIGNED_IN = "True";
    }

    return {

        /* Constants */

        DEV_TOKEN: "8c7e3110b57437cd914a66d81ef91014",
        PROD_TOKEN: "b1e0c8f26c4b7739abbbacba6cd3627a",
        DEFAULT_PROPERTIES: {
            "$initial_referrer": _JUNK_VALUE,
            "$initial_referring_domain": _JUNK_VALUE,
            "$search_engine": _JUNK_VALUE,
            "$mp_keyword": _JUNK_VALUE,
            "$os": _JUNK_VALUE,
            "$browser": _JUNK_VALUE,
            "$referrer": _JUNK_VALUE,
            "$referring_domain": _JUNK_VALUE,
            "mp_country_code": _JUNK_VALUE,
            "signed_in": _SIGNED_IN
        },
        CONFIG_PROPERTIES: {
            cross_subdomain_cookie: false,
            store_google: false,
            save_referrer: false,
            track_pageview: false
        },

        typed_search: false,

        _redirect_to: function (url) {
            window.location.href = url;
        },
        _submit_form: function (form_id) {
            $(form_id).submit();
        },

        /* Methods for /support */
        click_option: function (node_title, node_id) {
            mixpanel.track("Visited '" + node_title + "' (" + node_id + ")");
        },
        click_link_option: function (node_title, node_id, url) {
            mixpanel.track("Visited '" + node_title + "' (" + node_id + ")", {}, function () {
                MPTracker._redirect_to(url);
            });
            // Redirect user anyway if callback never fires
            var t = setTimeout(function () { MPTracker._redirect_to(url); }, 1500);
        },

        /* Methods for tracking support funnel */
        click_link: function (selector, event_name) {
            document.body.on("click", selector, function (event, elm) {
                if (event.button == 1 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
                    // Opening link in a new tab or window.  Track the event, but don't prevent
                    // default behavior or redirect.
                    mixpanel.track(event_name, {}, function () {});
                    return;
                }
                event.preventDefault();
                var url = elm.getAttribute("href");
                mixpanel.track(event_name, {}, function () {
                    MPTracker._redirect_to(url);
                });
                var t = setTimeout(function () { MPTracker._redirect_to(url); }, 1500);
            });
        },
        click_submit: function (submit_button_id, form_id, event_name) {
            $(submit_button_id).observe("click", function (event) {
                event.preventDefault();
                mixpanel.track(event_name, {}, function () {
                    MPTracker._submit_form(form_id);
                });
                // Submit form anyway if callback never fires
                var t = setTimeout(function () { MPTracker._submit_form(form_id) }, 1500);
            });
        },
        type_in_input: function (input_id, event_name) {
            $(input_id).observe("keyup", function () {
                if (!MPTracker.typed_search) {
                    mixpanel.track(event_name);
                    MPTracker.typed_search = true;
                }
            });
        }
    }
})();

mixpanel.init(MPTracker.PROD_TOKEN, MPTracker.CONFIG_PROPERTIES);
mixpanel.register(MPTracker.DEFAULT_PROPERTIES);
mixpanel.identify(Constants.sess_id);
mixpanel.name_tag(Constants.sess_id);
