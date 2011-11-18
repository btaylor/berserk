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

import simplejson

from time import mktime
from datetime import timedelta

from django.db import transaction
from django.core import serializers
from django.db import IntegrityError
from django.db.models import Count, Sum, Q
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404

from berserk2 import settings
from berserk2.sprints.models import *
from berserk2.sprints.utils import date_range
from berserk2.bugtracker import BugTrackerFactory
from berserk2.sprints.urls import reverse_full_url
from berserk2.sprints.models import _workday_diff, _calc_load

@login_required
def sprint_index(request):
    """
    If the user has it, redirect to the last sprint they were viewing.  If
    not, redirect the user to the first project they're a member of.  If they
    have no projects, 404.
    """
    profile = request.user.profile
    if profile.last_accessed_sprint:
        return HttpResponseRedirect(profile.last_accessed_sprint.get_absolute_url())

    projects = Project.objects.filter(users=request.user)
    if projects.count() == 0:
        raise Http404(_('You are not a member of any project.  Ask your administrator to add you.'))
    return HttpResponseRedirect(projects[0].get_absolute_url())

@login_required
def sprint_project_index(request, project_slug):
    """
    Redirect the user to the latest sprint for this project.  If there are no
    sprints, 404.
    """
    project = get_object_or_404(Project, slug=project_slug, users=request.user)
    sprint = Sprint.objects.current(project)
    if sprint == None:
        try:
            sprint = Sprint.objects.latest(project=project)
        except:
            pass

    if sprint == None:
        raise Http404(_('No sprints have been defined yet.  Visit the Admin page to get started.'))

    return HttpResponseRedirect(sprint.get_absolute_url())

@login_required
def sprint_detail(request, sprint_id, project_slug,
                  template_name='sprints/sprint_detail.html'):
    project = get_object_or_404(Project, slug=project_slug, users=request.user)
    sprint = get_object_or_404(Sprint, pk=int(sprint_id), project=project)
    iteration_days = xrange(1, sprint.iteration_days()+2)

    # Remember that we accessed this sprint for later
    profile = request.user.profile
    if profile.last_accessed_sprint != sprint:
        profile.last_accessed_sprint = sprint
        profile.save()

    return render_to_response(template_name,
                              {'sprint': sprint,
                               'iteration_days': iteration_days,
                               'projects': Project.objects.filter(is_active=True) },
                              context_instance=RequestContext(request))

@login_required
def sprint_edit(request, sprint_id, project_slug,
                template_name='sprints/sprint_edit.html'):
    project = get_object_or_404(Project, slug=project_slug, users=request.user)
    sprint = get_object_or_404(Sprint, pk=int(sprint_id), project=project)
    bookmarklet_url = settings.NEW_TASK_BOOKMARKLET_URL \
                          % reverse_full_url('sprint_current_bookmarklet', kwargs={'project_slug': project.slug})

    # Remember that we accessed this sprint for later
    profile = request.user.profile
    if profile.last_accessed_sprint != sprint:
        profile.last_accessed_sprint = sprint
        profile.save()

    return render_to_response(template_name,
                              {'sprint': sprint,
                               'bookmarklet_url': bookmarklet_url,
                               'projects': Project.objects.filter(is_active=True) },
                              context_instance=RequestContext(request))

import urllib

@login_required
def sprint_current_bookmarklet(request, project_slug):
    def redirect(error=None, notice=None):
        if error is not None:
            request.flash['error'] = error
        if notice is not None:
            request.flash['notice'] = notice
        return HttpResponseRedirect(reverse('sprint_edit',
                                            kwargs={'sprint_id': sprint.id,
                                                    'project_slug': project_slug}))

    projects = Project.objects.filter(slug=project_slug, users=request.user)
    if projects.count() == 0:
        return HttpResponseRedirect(reverse('sprint_index'))

    sprint = Sprint.objects.current(project=projects[0])
    if sprint == None or request.method != 'GET':
        return HttpResponseRedirect(reverse('sprint_index'))

    tracker = BugTrackerFactory.get_bug_tracker()
    if not tracker:
        return redirect(error=_('Your bug tracker has not been set up yet.'))

    base_url = sprint.project.bug_tracker.base_url
    remote_tracker_id = tracker.get_id_from_url(urllib.unquote(request.GET['url']),
                                                base_url)

    if not remote_tracker_id:
        return redirect(error=_('I don\'t recognize this type of URL.'))

    result = _add_task(request, sprint, sprint.project.bug_tracker,
                       remote_tracker_id)
    if 'error' in result:
        return redirect(error=result['error'])
    elif 'notice' in result:
        return redirect(notice=result['notice'])
    return redirect()

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
        effort_rows.append(['%s <span class="sparkline invisible">%s</span>' % \
            (get_username_for_display(u), ','.join([str(v) for v in e if v != '']))] + e)

    load_rows = []
    for u, l in load.iteritems():
        load_rows.append([get_username_for_display(u)] + ['%.0f' % i for i in l if type(i) == type(float())])

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
                '<a href="%s" target="_blank">#%s</a>' % (s.task.get_absolute_url(), s.task.remote_tracker_id),
                s.title, s.component, s.get_assigned_to_display(), s.get_submitted_by_display(),
                s.status, s.estimated_hours
            ]
            task_data.extend(iteration_days)
            tasks_data.append(task_data)

        task_data[(csnap.date - sprint.start_date).days + 7] = s.remaining_hours
        latest_snap = s

    for task in tasks_data:
        task[1] = task[1] + '&nbsp;<span class="sparkline invisible">%s</span>' % \
            ','.join([str(i) for i in task[6:] if i != ''])

    return HttpResponse(simplejson.dumps(tasks_data))

def sprint_my_tasks_json(request, sprint_id):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps([]))

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    cached_snaps = TaskSnapshotCache.objects.filter(task_snapshot__assigned_to=request.user,
                                                    task_snapshot__task__sprints=sprint)
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
            '<a href="javascript:deleteTask(%s);"><img id="%s" src="/site_media/berserk/images/edit-delete.png" width="16" height="16"/></a>' \
                % (snap.task.id, snap.task.id)
        ])
    return HttpResponse(simplejson.dumps(tasks_data))

def sprint_burndown_json(request, sprint_id):
    """
    Returns a list of points with the iteration day as the X axis and the
    number of remaining hours as the Y axis.
    """
    sprint = get_object_or_404(Sprint, pk=int(sprint_id))

    remaining_hours = []
    user_remaining_hours = []
    open_tasks = []
    for day, date in date_range(sprint.start_date, sprint.end_date):
        cache = TaskSnapshotCache.objects.filter(task_snapshot__task__sprints=sprint,
                                                 date=date)
        data = cache.aggregate(rem=Sum('task_snapshot__remaining_hours'))
        remaining_hours.append([day, data['rem'] if data['rem'] else 'null'])

        data = cache.exclude(Q(task_snapshot__status='RESOLVED') \
                             | Q(task_snapshot__status='CLOSED') \
                             | Q(task_snapshot__status='VERIFIED')) \
                    .aggregate(count=Count('task_snapshot'))
        if data['count']:
            open_tasks.append([day, data['count']])

        if not request.user.is_authenticated():
            continue

        data = cache.filter(task_snapshot__assigned_to=request.user) \
                            .aggregate(rem=Sum('task_snapshot__remaining_hours'))
        user_remaining_hours.append([day, data['rem'] if data['rem'] else 'null'])

    weekends = []
    for day, date in date_range(sprint.start_date, sprint.end_date):
        if date.isoweekday() == 7:
            weekends.append({'start': day - 2, 'end': day})

    return HttpResponse(simplejson.dumps({
        'data': [remaining_hours, user_remaining_hours, open_tasks],
        'weekends': weekends,
    }))

def sprint_milestone_graph_json(request, sprint_id):
    """
    Returns a list of points with the date as the X axis and the number of
    remaining hours as the Y axis.
    """
    def jstime(date):
        """
        Similar to Unix time, Javascript time is the number of *milli*seconds
        since the epoch.
        """
        return mktime(date.timetuple()) * 1000

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    milestone = sprint.milestone

    if sprint.milestone is None:
        return HttpResponse(simplejson.dumps({}))

    stats = MilestoneStatisticsCache.objects.filter(milestone=milestone) \
                                            .order_by('date')
    return HttpResponse(simplejson.dumps({
        'remaining_hours': [(jstime(s.date), s.total_remaining_hours) for s in stats],
        'open_tasks': [(jstime(s.date), s.total_open_tasks) for s in stats],
        'start_date': jstime(milestone.start_date),
        'end_date': jstime(milestone.end_date),
        'sprint_start_date': jstime(sprint.start_date),
        'sprint_end_date': jstime(sprint.end_date),
    }))

def sprint_statistics_partial(request, sprint_id,
                              template_name='sprints/sprint_statistics_partial.html'):
    if not request.user.is_authenticated():
        return HttpResponse('')

    sprint = get_object_or_404(Sprint, pk=int(sprint_id))
    cached_snaps = TaskSnapshotCache.objects.filter(task_snapshot__assigned_to=request.user)
    if sprint.is_active():
        cached_snaps = cached_snaps.filter(date=date.today())
    else:
        cached_snaps = cached_snaps.filter(date=sprint.end_date)

    sum = cached_snaps.aggregate(value=Sum('task_snapshot__remaining_hours'))
    hours = sum['value'] if sum['value'] != None else 0

    load = None
    if sprint.is_active():
        load = _calc_load(hours, _workday_diff(sprint.start_date, date.today()),
                          sprint.iteration_workdays(), sprint.velocity)

    return render_to_response(template_name,
                              {'hours': hours, 'load': load },
                              context_instance=RequestContext(request))

@csrf_exempt
def sprint_delete_task_json(request, sprint_id):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps([]))

    sprint = get_object_or_404(Sprint, pk=int(sprint_id),
                               project__users=request.user)

    if 'task_id' not in request.POST:
        return HttpResponseRedirect(sprint.get_absolute_url())

    task = get_object_or_404(Task, pk=int(request.POST['task_id']))
    try:
        task.sprints.remove(sprint)
    except Exception, e:
        return HttpResponse(simplejson.dumps({'error': e.message}))
    finally:
        return HttpResponse(simplejson.dumps({
            'notice': _('Task #%s has been removed from this sprint.') % task.remote_tracker_id
        }))

@csrf_exempt
@transaction.commit_manually
def sprint_new_json(request, sprint_id):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps([]))

    sprint = get_object_or_404(Sprint, pk=int(sprint_id),
                               project__users=request.user)
    if request.method != 'POST':
        return HttpResponseRedirect(sprint.get_absolute_url())

    result = _add_task(request, sprint,
                       sprint.project.bug_tracker,
                       request.POST['remote_tracker_id'])

    return HttpResponse(simplejson.dumps(result))

def _add_task(request, sprint, bug_tracker, remote_tracker_id):
    err, task = None, None
    try:
        if not sprint.is_active():
            raise Exception(_('You cannot edit an inactive sprint.'))

        task, created = Task.objects.get_or_create(bug_tracker=bug_tracker,
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
