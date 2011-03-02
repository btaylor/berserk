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

from datetime import datetime

from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404

from berserk2.timeline.models import Event

def timeline_index(request,
                   template_name='timeline/timeline_index.html'):
    events = Event.objects.order_by('-date')[:50]
    return render_to_response(template_name,
                              {'events': events},
                              context_instance=RequestContext(request))

def timeline_latest_events_json(request, last_update_date):
    """
    Returns a list of events since last_update_date in json format.
    """
    events = Event.objects.filter(date_gt=last_update_date) \
                          .order_by('-date')
    data = map(lambda e: (e.message, e.comment))
    return HttpResponse(simplejson.dumps({
        'last_updated': datetime.now(),
        'events': data,
    }))
