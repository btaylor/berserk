/*
 * Copyright (c) 2011 Brad Taylor <brad@getcoded.net>
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

function Notifier (args) {
	this._init(args);
}

Notifier.prototype = {
	_options : {
		cookie_name : 'notification_enabled',
		cookie_expiry_days : 1000,
		enabledChanged : null
	},

	_init : function (options) {
		this._options = $.extend({}, this._options, options);
		if (this._options.enabledChanged)
			this._options.enabledChanged(this.enabled());
	},

	_cookie : function () {
		return $.cookie(this._options.cookie_name) == 'true';
	},

	_allowed : function () {
		return (window.webkitNotifications
			&& window.webkitNotifications.checkPermission() == 0);
	},

	_setCookie : function (val) {
		$.cookie(this._options.cookie_name, val,
                         { expires: this._options.cookie_expiry_days } );
		if (this._options.enabledChanged)
			this._options.enabledChanged(val);
	},

	supported : function () {
		return window.webkitNotifications;
	},

	enabled : function () {
		return (this._cookie() && this._allowed());
	},

	enable : function () {
		if (this._allowed()) {
			this._setCookie(true);
			return;
		}

		var klass = this;
		window.webkitNotifications.requestPermission(function () {
			klass._setCookie(klass._allowed());

			// If we've been denied once, we're denied forever,
			// even if we re-request permission.  Alert the user to
			// that fact, so they don't get stabby.
			if (!klass._allowed()) {
				alert("Sorry, we can't show notifications because you've denied us in the past. You can re-enable notifications in your browser settings.");
			}
		});
	},

	disable : function () {
		this._setCookie(false);
	},

	toggleEnabled : function () {
		if (this.enabled())
			this.disable();
		else
			this.enable();
	},

	htmlNotify : function (options) {
		if (!this.enabled())
			return;

		if (!('url' in options))
			return;

		var p = window.webkitNotifications.createHTMLNotification(options.url);

		// We're only allowed to have 4 notifications up at one time.
		// Any further notifications will be queued until one or more
		// of the other notifications are hidden, so wait until we've
		// been shown to start the timer.
		p.ondisplay = function () {
			setTimeout(function () { p.cancel (); },
			           'timeout' in options ? options.timeout : 5000);
		};

		p.show();
	},
};
