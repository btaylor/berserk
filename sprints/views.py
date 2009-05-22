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

from datetime import timedelta

from django.db.models import Sum
from django.db import transaction
from django.db import IntegrityError
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404

from berserk2 import settings
from berserk2.sprints.models import *
from berserk2.sprints.utils import date_range
from berserk2.sprints.urls import reverse_full_url

def sprint_index(request):
    sprint = Sprint.objects.current()
    if sprint == None:
        try:
            sprint = Sprint.objects.latest()
        except:
            pass

    if sprint == None:
        raise Http404(_('No sprints have been defined yet.  Visit the Admin page to get started.'))
    
    return HttpResponseRedirect(sprint.get_absolute_url())

def sprint_detail(request, sprint_id,
                  template_name='sprints/sprint_detail.html'):
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    iteration_days = xrange(1, sprint.iteration_days()+2)

    return render_to_response(template_name,
                              {'sprint': sprint,
                               'iteration_days': iteration_days},
                              context_instance=RequestContext(request))

@login_required
def sprint_edit(request, sprint_id,
                template_name='sprints/sprint_edit.html'):
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    bookmarklet_url = settings.NEW_TASK_BOOKMARKLET_URL \
                          % reverse_full_url('sprint_current_bookmarklet')
    return render_to_response(template_name,
                              {'sprint': sprint,
                               'bookmarklet_url': bookmarklet_url},
                              context_instance=RequestContext(request))

import urllib, cgi

@login_required
def sprint_current_bookmarklet(request):
    sprint = Sprint.objects.current()
    if sprint == None or request.method != 'GET':
        return HttpResponseRedirect(reverse('sprint_index'))

    remote_tracker_id = None

    # e.g.: https://bugzilla.mozilla.org/show_bug.cgi?id=490130
    url = urllib.unquote(request.GET['url'])

    path, query = urllib.splitquery(url)
    if not path.startswith(sprint.default_bug_tracker.base_url):
        request.flash['error'] = _('Hmm, this doesn\'t look like my default bug tracker URL.');
        return HttpResponseRedirect(reverse('sprint_edit',
                                            kwargs={'sprint_id': sprint.id}))

    data = cgi.parse_qsl(query)
    for item in data:
        key, value = item
        if key == 'id':
            remote_tracker_id = value

    if not remote_tracker_id:
        request.flash['error'] = _('Hmm, I\'ve never seen this type of URL before.  Fancy!')
        return HttpResponseRedirect(reverse('sprint_edit',
                                            kwargs={'sprint_id': sprint.id}))

    result = _add_task(request, sprint, sprint.default_bug_tracker,
                       remote_tracker_id)
    if 'error' in result:
        request.flash['error'] = result['error']
    elif 'notice' in result:
        request.flash['notice'] = result['notice']

    return HttpResponseRedirect(reverse('sprint_edit',
                                        kwargs={'sprint_id': sprint.id}))


import simplejson

from django.http import HttpResponse
from django.core import serializers

def sprint_load_effort_json(request, sprint_id):
    """
    Returns a list of users and their load and effort values for each of the
    days in the Sprint.
    """
    def get_username_for_display(u):
        return u.first_name if u != None else 'None'

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    load, effort = sprint.load_and_effort_by_user()

    effort_rows = []
    for u, e in effort.iteritems():
        effort_rows.append([get_username_for_display(u)] + e)

    load_rows = []
    for u, l in load.iteritems():
        load_rows.append([get_username_for_display(u)] + ['%.0f' % i for i in l])

    return HttpResponse(simplejson.dumps({
        'load': load_rows, 'effort': effort_rows,
    }))

def sprint_tasks_json(request, sprint_id):
    """
    Returns a list of tasks and the effort values for each of the days in the
    Sprint.
    """
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    iteration_days = [''] * (sprint.iteration_days() + 1)

    # This code is finely tuned to reduce the number of queries.  Please test
    # performance numbers before modifying
    tasks = Task.objects.filter(sprints=sprint).values('id')
    csnaps = TaskSnapshotCache.objects.filter(task_snapshot__task__in=tasks) \
                                      .filter(date__gte=sprint.start_date,
                                              date__lt=sprint.end_date + timedelta(1)) \
                                      .order_by('task_snapshot__task', '-date')
    tasks_data = []
    task_data = latest_snap = None
    for csnap in csnaps:
        s = csnap.task_snapshot
        if latest_snap == None or s.task != latest_snap.task:
            task_data = [
                '<a href="%s">#%s</a>' % (s.task.get_absolute_url(), s.task.remote_tracker_id),
                s.title, s.component, s.get_assigned_to_display(), s.get_submitted_by_display(),
                s.status, s.estimated_hours,
            ]
            task_data.extend(iteration_days)
            tasks_data.append(task_data)

        task_data[(csnap.date - sprint.start_date).days + 7] = s.remaining_hours
        latest_snap = s

    return HttpResponse(simplejson.dumps(tasks_data))

def sprint_my_tasks_json(request, sprint_id):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps([]))

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    cached_snaps = TaskSnapshotCache.objects.filter(task_snapshot__assigned_to=request.user)
    if sprint.is_active():
        cached_snaps = cached_snaps.filter(date=date.today())
    else:
        cached_snaps = cached_snaps.filter(date=sprint.end_date)
    
    tasks_data = []
    for cached_snap in cached_snaps:
        snap = cached_snap.task_snapshot
        tasks_data.append([
            '<a href="%s">#%s</a>' % (snap.task.get_absolute_url(), snap.task.remote_tracker_id),
            snap.title, snap.component, snap.status,
            snap.estimated_hours, snap.remaining_hours,
            snap.task.id,
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
        remaining_hours.append([day, data['rem'] if data['rem'] else 'null'])

    user_remaining_hours = []
    if request.user.is_authenticated():
        for day, date in date_range(sprint.start_date, sprint.end_date):
            data = TaskSnapshotCache.objects.filter(task_snapshot__task__sprints=sprint,
                                                    date=date, task_snapshot__assigned_to=request.user) \
                                            .aggregate(rem=Sum('task_snapshot__remaining_hours'))
            user_remaining_hours.append([day, data['rem'] if data['rem'] else 'null'])

    weekends = []
    for day, date in date_range(sprint.start_date, sprint.end_date):
        if date.isoweekday() == 7:
            weekends.append({'start': day - 2, 'end': day})

    return HttpResponse(simplejson.dumps({
        'data': [remaining_hours, user_remaining_hours],
        'weekends': weekends,
    }))

@transaction.commit_manually
def sprint_new_json(request, sprint_id):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps([]))

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))

    if request.method != 'POST':
        return HttpResponseRedirect(sprint.get_absolute_url())

    result = _add_task(request, sprint,
                       sprint.default_bug_tracker,
                       request.POST['remote_tracker_id'])

    return HttpResponse(simplejson.dumps(result))

def _add_task(request, sprint, default_bug_tracker, remote_tracker_id):
    err, task = None, None
    try:
        if not sprint.is_active():
            raise Exception(_('You cannot edit an inactive sprint.'))
        
        task, created = Task.objects.get_or_create(bug_tracker=default_bug_tracker,
                                                   remote_tracker_id=remote_tracker_id)
        if created:
            snapshot = task.get_latest_snapshot()
        else:
            snapshot = task.snapshot()

        if snapshot == None:
            raise Exception(_('Invalid task id, or unable to contact the Bug Tracker to fetch Task information.'))
        elif snapshot.assigned_to != request.user:
            raise Exception(_('Please assign this bug to yourself before adding it to your sprint.'))
        elif snapshot.remaining_hours == 0:
            raise Exception(_('No time remains on this bug. Please add additional hours before adding it to your sprint.'))
        
        if task.sprints.filter(pk=sprint.pk):
            raise Exception(_('This task has already been added to the sprint.'))

        task.sprints.add(sprint)
        task.save()
    except ValueError:
        transaction.rollback()
        return {'error': _('You must enter a valid bug number.')}
    except Exception, e:
        transaction.rollback()
        return {'error': e.message}
    else:
        transaction.commit()

    return {'notice': _('Task #%s has been added to your sprint.') % task.remote_tracker_id}
