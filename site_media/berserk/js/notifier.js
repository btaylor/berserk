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
		$.cookie(this._options.cookie_name, val);
		if (this._options.enabledChanged)
			this._options.enabledChanged(val);
	},

	enabled : function () {
		return (this._cookie() && this._allowed());
	},

	enable : function () {
		if (this._allowed()) {
			this._setCookie(true);
			return;
		}

		window.webkitNotifications.requestPermission(function () {
			this._setCookie(this._allowed());
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
		p.show();

		setTimeout(function () { p.cancel (); },
		           'timeout' in options ? options.timeout : 5000);
	},
};
