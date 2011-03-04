#
# Copyright (c) 2008-2011 Brad Taylor <brad@getcoded.net>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import simplejson

from datetime import datetime

from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.template.defaultfilters import linebreaksbr
from django.shortcuts import render_to_response, get_object_or_404

from berserk2.timeline.models import Event
from berserk2.timeline.templatetags.utcunixtimestamp import utcunixtimestamp

def timeline_index(request,
                   template_name='timeline/timeline_index.html'):
    events = Event.objects.order_by('-date')[:50]

    new_start_after = 0
    if events.count() > 0:
        new_start_after = events[0].pk

    new_earlier_than = 0
    if events.count() > 0:
        new_earlier_than = events[events.count()-1].pk

    return render_to_response(template_name,
                              {'events': events,
                               'new_start_after': new_start_after,
                               'new_earlier_than': new_earlier_than},
                              context_instance=RequestContext(request))

def timeline_latest_events_json(request, start_after):
    """
    Returns a list of events newer than start_after (a event pk) in json format.
    """
    events = Event.objects.filter(pk__gt=start_after) \
                          .order_by('date')
    data = map(lambda e: {
        'pk': e.pk, 'date': utcunixtimestamp(e.date),
        'message': e.get_message_for_display(),
        'comment': linebreaksbr(e.comment),
    }, events)

    new_start_after = start_after
    if events.count() > 0:
        new_start_after = events[events.count()-1].pk

    return HttpResponse(simplejson.dumps({
        'events': data,
        'new_start_after': new_start_after,
    }))

def timeline_previous_events_json(request, earlier_than):
    """
    Returns a list of 25 events older than earlier_than (a event pk) in json
    format.
    """
    events = Event.objects.filter(pk__lt=earlier_than) \
                          .order_by('-date')[:25]
    data = map(lambda e: {
        'pk': e.pk, 'date': utcunixtimestamp(e.date),
        'message': e.get_message_for_display(),
        'comment': linebreaksbr(e.comment),
    }, events)

    new_earlier_than = -1 # signal end of data
    if events.count() > 0:
        new_earlier_than = events[events.count()-1].pk

    return HttpResponse(simplejson.dumps({
        'events': data,
        'new_earlier_than': new_earlier_than,
    }))
