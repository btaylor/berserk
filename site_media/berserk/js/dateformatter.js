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

function DateFormatter (args) {
	this._init(args);
}

DateFormatter.prototype = {
	_options : {
	},

	_MONTHS : [
		'January', 'Feburary', 'March', 'April',
		'May', 'June', 'July', 'August',
		'September', 'October', 'November', 'December'
	],

	_DAYS : [
		'Sunday', 'Monday', 'Tuesday', 'Wednesday',
		'Thursday', 'Friday', 'Saturday'
	],

	_init : function (options) {
		this._options = $.extend({}, this._options, options);
	},

	getRelativeDateString : function (date) {
		var curr = new Date().getTime() / 1000;
		var diff = curr - date;

		if (diff < 60) {
			return 'moments ago';
		} else if (diff < 3600) {
			var mins = Math.round(diff / 60);
			return mins + ' minute' + (mins == 1 ? '' : 's') + ' ago';
		} else if (diff < 43200) {
			var hours = Math.round(diff / 3600);
			return hours + ' hour' + (hours == 1 ? '' : 's') + ' ago';
		}
		return this.getDateString(new Date(date * 1000));
	},

	_getDateDaysFromNow : function (date, days) {
		return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days,
		                date.getHours(), date.getMinutes(), date.getSeconds(), date.getMilliseconds());
	},

	getDateString : function (date) {
		var now = new Date();
		var day = new Date(date.getFullYear(), date.getMonth(), date.getDate());
		var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

		if (day.valueOf() == this._getDateDaysFromNow(today, -1).valueOf())
			return 'Yesterday';
		else if (day.valueOf() == today.valueOf())
			return 'Today';
		else if (day.valueOf() == this._getDateDaysFromNow(today, 1).valueOf())
			return 'Tomorrow';
		else if (day.valueOf() > this._getDateDaysFromNow(today, -6).valueOf()
			 && day.valueOf() < this._getDateDaysFromNow(today, 6).valueOf())
			return this._DAYS[date.getDay()];

		if (date.getFullYear() == now.getFullYear())
			return this._MONTHS[date.getMonth()] + ' ' + date.getDate();

		return this._MONTHS[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();
	},

	getTimeString : function (date) {
		var hours = date.getHours(),
		    minutes = date.getMinutes(),
		    ampm = 'AM', ret = '';

		if (hours == 0) {
			hours = 12;
		} else if (hours == 12) {
			ampm = 'PM';
		} else if (hours > 12) {
			ampm = 'PM';
			hours -= 12;
		}

		if (minutes < 10)
			minutes = '0' + minutes;

		return hours + ':' + minutes + ' ' + ampm;
	},

	getDateTimeString : function (date) {
		return this.getDateString(date) + ', ' + this.getTimeString(date);
	}
};
