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
		updateDelay : 200,
		eventDetailUrl : null
	},

	_selectedId : -1,
	_activeTimeout : null,

	_init : function (options) {
		this._options = $.extend({}, this._options, options);
		this._dateFormatter = new DateFormatter();

		// Make the sidebar follow the user as they scroll
		var klass = this;
		var activeScrollTimeout = null;
		$(window).scroll(function () {
			if (activeScrollTimeout)
				clearTimeout(activeScrollTimeout);

			var activeScrollTimeout = setTimeout(function () {
				activeScrollTimeout = null;

				var min = $('#timeline-content-container').offset().top;
				if ($(window).scrollTop() > min)
					$('#timeline-sidebar').css('top', $(window).scrollTop() - min);
				else
					$('#timeline-sidebar').css('top', 0);
			}, 300);
		});
	},

	_updateEventDisplay : function (id, time, message, task, comment) {
		var timestr = this._dateFormatter.getDateTimeString(new Date(time * 1000));
		$('#timeline-sidebar-event').empty()
		                            .append($('<p>').html(timestr))
		                            .append($('<h1>').html(message))
                                            .append($('<blockquote>').html(comment));
	},

	_updateDetailDisplay : function (id) {
		if (!this._options.eventDetailUrl)
			return;

		// Rate limit requests so we don't spam the server if someone
		// mashes the j key.
		if (this._activeTimeout)
			clearTimeout(this._activeTimeout);

		// TODO: show loading spinner
		$('#timeline-sidebar-detail').empty();

		var url = this._options.eventDetailUrl.replace('99', id);

		var klass = this;
		this._activeTimeout = setTimeout(function () {
			klass._activeTimeout = null;
			$.get(url, function (data) {
				// If our selection has changed while the request was
				// active, dump it
				if (klass._selectedId != id)
					return;

				$('#timeline-sidebar-detail').html(data);
			});
		}, this._options.updateDelay);
	},

	select : function (evt) {
		var id = $(evt).attr('data-id'),
		    time = $(evt).attr('data-timestamp'),
		    message = $(evt).children('.timeline-message').html(),
		    task = $(evt).children('.timeline-event-task').html(),
		    comment = $(evt).children('.timeline-event-comment').html();

		this._selectedId = id;
		this._updateEventDisplay(id, time, message, task, comment);
		this._updateDetailDisplay(id);
	},
};
