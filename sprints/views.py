#
# Copyright (c) 2008-2009 Brad Taylor <brad@getcoded.net>
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

from django.db.models import Sum
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_object_or_404

from berserk2.sprints.models import *
from berserk2.sprints.utils import date_range

def sprint_detail(request, sprint_id=None,
                  template_name='sprints/sprint_detail.html'):
    if sprint_id == None:
        sprint = Sprint.objects.current()
    else:
        sprint = get_object_or_404(Sprint, pk=int(sprint_id))

    if sprint == None:
        raise Http404(_('No sprints have been defined yet.  Visit the Admin page to get started.'))

    iteration_days = xrange(1, sprint.iteration_days()+2)

    return render_to_response(template_name,
                              {'sprint': sprint,
                               'iteration_days': iteration_days},
                              context_instance=RequestContext(request))

import simplejson

from django.http import HttpResponse
from django.core import serializers

def sprint_load_effort_json(request, sprint_id):
    """
    Returns a list of users and their load and effort values for each of the
    days in the Sprint.
    """
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    data = sprint.load_and_effort_by_user()

    effort_rows = []
    for user, load in data['effort'].iteritems():
        effort_rows.append([user.username] + load)

    load_rows = []
    for user, load in data['load'].iteritems():
        load_rows.append([user.username] + ['%.0f' % l for l in load])

    return HttpResponse(simplejson.dumps({
        'load': load_rows, 'effort': effort_rows,
    }))

def sprint_tasks_json(request, sprint_id):
    """
    Returns a list of tasks and the effort values for each of the days in the
    Sprint.
    """
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    tasks = Task.objects.filter(sprints=sprint)

    tasks_data = []
    for task in tasks:
        task_rem = []
        latest_snap = None
        for day, date in date_range(sprint.start_date, sprint.end_date):
            snaps = TaskSnapshotCache.objects.filter(task_snapshot__task=task,
                                                     date=date)
            if snaps.count() > 0:
                latest_snap = snaps[0].task_snapshot
            task_rem.append(latest_snap.remaining_hours if latest_snap else 0)

        if latest_snap == None:
            continue

        tasks_data.append([
                '<a href="%s">#%s</a>' % (task.get_absolute_url(), task.remote_tracker_id),
                latest_snap.title, latest_snap.component,
                unicode(latest_snap.assigned_to), unicode(latest_snap.submitted_by),
                latest_snap.status, latest_snap.estimated_hours
        ])
    
    return HttpResponse(simplejson.dumps(tasks_data))

def sprint_burndown_json(request, sprint_id):
    """
    Returns a list of points with the iteration day as the X axis and the
    number of remaining hours as the Y axis.
    """
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    
    remaining_hours = []
    for day, date in date_range(sprint.start_date, sprint.end_date):
        data = TaskSnapshotCache.objects.filter(task_snapshot__task__sprints=sprint,
                                             date=date) \
                                        .aggregate(rem=Sum('task_snapshot__remaining_hours'))
        remaining_hours.append([day, data['rem'] if data['rem'] else 0])

    return HttpResponse(simplejson.dumps(remaining_hours))
