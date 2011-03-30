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
from django.views.decorators.cache import cache_page
from django.contrib.csrf.middleware import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.template.defaultfilters import linebreaksbr
from django.shortcuts import render_to_response, get_object_or_404, redirect


from berserk2.timeline.models import Event
from berserk2.timeline.plugins import PluginFactory
from berserk2.timeline.templatetags.utcunixtimestamp import utcunixtimestamp

def timeline_index(request,
                   template_name='timeline/index.html'):
    events = Event.objects.order_by('-date')[:50]

    new_start_after = datetime.now()
    if events.count() > 0:
        new_start_after = utcunixtimestamp(events[0].date)

    new_earlier_than = 0
    if events.count() > 0:
        new_earlier_than = utcunixtimestamp(events[events.count()-1].date)

    return render_to_response(template_name,
                              {'events': events,
                               'new_start_after': new_start_after,
                               'new_earlier_than': new_earlier_than},
                              context_instance=RequestContext(request))

def timeline_latest_events_json(request, start_after):
    """
    Returns a list of events newer than start_after (a event pk) in json format.
    """
    after = datetime.fromtimestamp(float(start_after))
    events = Event.objects.filter(date__gt=after) \
                          .order_by('date')
    data = map(lambda e: {
        'pk': e.pk, 'date': utcunixtimestamp(e.date),
        'message': e.get_message_for_display(),
        'task': e.get_task_for_display(),
        'comment': linebreaksbr(e.comment),
    }, events)

    new_start_after = start_after
    if events.count() > 0:
        new_start_after = utcunixtimestamp(events[events.count()-1].date)

    return HttpResponse(simplejson.dumps({
        'events': data,
        'new_start_after': new_start_after,
    }))

def timeline_previous_events_json(request, earlier_than):
    """
    Returns a list of 25 events older than earlier_than (a event pk) in json
    format.
    """
    before = datetime.fromtimestamp(float(earlier_than))
    events = Event.objects.filter(date__lt=before) \
                          .order_by('-date')[:25]
    data = map(lambda e: {
        'pk': e.pk, 'date': utcunixtimestamp(e.date),
        'message': e.get_message_for_display(),
        'task': e.get_task_for_display(),
        'comment': linebreaksbr(e.comment),
    }, events)

    new_earlier_than = -1 # signal end of data
    if events.count() > 0:
        new_earlier_than = utcunixtimestamp(events[events.count()-1].date)

    return HttpResponse(simplejson.dumps({
        'events': data,
        'new_earlier_than': new_earlier_than,
    }))

def timeline_event_popup(request, event_id,
                         template_name='timeline/event_popup.html'):
    """
    Returns a popup-sized HTML page which describes the given event, otherwise
    raises Http404.
    """
    event = get_object_or_404(Event, pk=event_id)
    return render_to_response(template_name,
                              {'e': event},
                              context_instance=RequestContext(request))

@csrf_exempt
@cache_page(60 * 15)
def timeline_event_detail(request, event_id):
    """
    Returns a partial HTML page which describes the event in detail if
    available, otherwise returns a blank page.

    This page is cached for 15 minutes, as it is likely to be expensive to
    generate.
    """
    event = get_object_or_404(Event, pk=event_id)
    viewer = PluginFactory.get_detailed_viewer_for(event)
    if not viewer:
        return HttpResponse()

    view = viewer()
    return view.render(request, event)

def timeline_jump(request, event_id):
    """
    Redirects the browser to the URL associated with a given event.  If there
    are more than one related URLs, jumps to the first one.
    """
    event = get_object_or_404(Event, pk=event_id)
    url = None
    if event.task:
        url = event.task.get_absolute_url()
    return redirect(url)

@csrf_exempt
def timeline_push(request, source_id):
    """
    Accepts any request to this URL and routes it to the correct PushSource
    based upon name.
    """
    sources = PluginFactory.get_push_source_by_id(source_id)
    if not sources:
        raise Http404()

    for source in sources:
        s = source()
        s.push(request)

    return HttpResponse()
