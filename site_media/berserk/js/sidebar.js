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

function Sidebar (args) {
	this._init(args);
}

Sidebar.prototype = {
	_options : {
		eventDetailUrl : null
	},

	_init : function (options) {
		this._options = $.extend({}, this._options, options);
	},

	_updateEventDisplay : function (id, time, message, task, comment) {
		var timestr = new Date(time * 1000).toString();
		timestr = "Yesterday, 10:34pm";
		$('#timeline-sidebar-event').empty()
		                            .append($('<p>').html(timestr))
		                            .append($('<h1>').html(message))
                                            .append($('<blockquote>').html(comment));
	},

	_updateDetailDisplay : function (id) {
		if (!this._options.eventDetailUrl)
			return;

		// TODO: show loading spinner
		$('#timeline-sidebar-detail').empty();

		var url = this._options.eventDetailUrl.replace('99', id);
		$.get(url, function (data) {
			$('#timeline-sidebar-detail').html(data);
		});
	},

	select : function (evt) {
		var id = $(evt).attr('data-id'),
		    time = $(evt).attr('data-timestamp'),
		    message = $(evt).children('.timeline-message').html(),
		    task = $(evt).children('.timeline-event-task').html(),
		    comment = $(evt).children('.timeline-event-comment').html();

		this._updateEventDisplay(id, time, message, task, comment);
		this._updateDetailDisplay(id);
	},
};
