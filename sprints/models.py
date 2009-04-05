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

from time import *
from datetime import datetime, date, timedelta

from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.utils.translation import ugettext as _

from berserk2.sprints.utils import date_range
from berserk2.sprints.managers import SprintManager

class BugTracker(models.Model):
    """
    A Bugzilla bug tracker.
    """
    product = models.CharField(max_length=128,
        verbose_name='Product Name',
        help_text=_('The Bugzilla product name to monitor.'))
    base_url = models.CharField(max_length=256,
        verbose_name='Bugzilla Base URL',
        help_text=_("Example: 'https://bugzilla.mozilla.org'.  Make sure to omit trailing slashes."))
    backend = models.CharField(max_length=32,
        help_text=_('The name of the class under berserk2.bugzilla.backends to use for accessing your Bugzilla instance.'))
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    class Meta:
        unique_together = ('base_url', 'product', 'backend')

    def __unicode__(self):
        return str(self.product)

    def get_remote_task_url(self, task):
        return '%s/show_bug.cgi?id=%s' % (self.base_url, task.remote_tracker_id)

class Sprint(models.Model):
    """
    A work-iteration represented by a date range and a velocity, or the number
    of expected work-hours per day.
    """
    start_date = models.DateField()
    end_date = models.DateField()
    velocity = models.IntegerField(default=6,
        help_text=_('The number of expected work-hours in a day'))
    default_bug_tracker = models.ForeignKey(BugTracker, null=True)
    objects = SprintManager()

    class Meta:
        get_latest_by = 'end_date'
        ordering = ['-end_date']

    def __unicode__(self):
        return _("%s - %s") % (self.start_date.strftime("%b. %e"),
                               self.end_date.strftime("%b. %e %Y"))

    @models.permalink
    def get_absolute_url(self):
        return ('sprint_detail', (), {'sprint_id': self.id})

    def is_active(self):
        """
        Returns true if the current date is between the start and end dates of
        the Sprint. 
        """
        return date.today() >= self.start_date \
               and date.today() <= self.end_date

    def iteration_days(self):
        """
        Returns the number of absolute days between the start and end dates of
        the Sprint.
        """
        return (self.end_date - self.start_date).days

    def iteration_workdays(self):
        """
        Returns the number of work days (M-F) between the start and end dates of the
        Sprint.
        """
        return _workday_diff(self.start_date, self.end_date)

    def load_and_effort_by_user(self):
        """
        Returns a tuple containing two child dicts.

         - The first dict mas a User to an array of their effort for every day
           in the Sprint.  Effort is the total remaining hours left in an
           Sprint-day.

         - The second dict maps a User to an array of their load for every day
           in the Sprint.  Load is calculated by:
                (total_hours / (weekdays * velocity) * 100.
        """
        users_load = {}
        users_effort = {}
        for day, date in date_range(self.start_date, self.end_date):
            rows = TaskSnapshotCache.objects.filter(date__lte=date, date__gte=date,
                                                    task_snapshot__task__sprints=self) \
                                            .values('task_snapshot__assigned_to') \
                                            .annotate(Sum('task_snapshot__remaining_hours'))
            for row in rows:
                assigned_to = row['task_snapshot__assigned_to']
                if assigned_to == None:
                    continue
                
                try:
                    user = User.objects.get(pk=int(assigned_to))
                except ObjectDoesNotExist:
                    continue

                if not users_load.has_key(user):
                    users_load[user] = [0]*(self.iteration_days() + 1)
                    users_effort[user] = [0]*(self.iteration_days() + 1)

                users_effort[user][day] = int(row['task_snapshot__remaining_hours__sum'])
                users_load[user][day] = _calc_load(users_effort[user][day],
                                                   _workday_diff(self.start_date, date),
                                                   self.iteration_workdays(),
                                                   self.velocity)
        return (users_load, users_effort)
    
    def get_previous_or_none(self):
        """
        Returns the previous Sprint by end_date, or None if none were found.
        """
        try:
            return self.get_previous_by_end_date()
        except models.DoesNotExist:
            pass
        return None
    
    def get_next_or_none(self):
        """
        Returns the next Sprint by end_date, or None if none were found.
        """
        try:
            return self.get_next_by_end_date()
        except models.DoesNotExist:
            pass
        return None

class Task(models.Model):
    """
    A work task associated with zero or more sprints.
    """
    remote_tracker_id = models.CharField(max_length=32)
    sprints = models.ManyToManyField(Sprint, blank=True)
    bug_tracker = models.ForeignKey(BugTracker)

    class Meta:
        unique_together = ('remote_tracker_id', 'bug_tracker')

    def __unicode__(self):
        return _("Issue #%s") % (self.remote_tracker_id)

    def get_absolute_url(self):
        return self.bug_tracker.get_remote_task_url(self)

    def get_latest_snapshot(self):
        """
        Returns the most recent snapshot of the Task.  If no snapshots found,
        returns None.
        """
        try:
            return TaskSnapshot.objects.filter(task=self).latest('date')
        except DoesNotExist:
            return None

    def snapshot(self):
        """
        Creates a new TaskSnapshot from the most recent Bugzilla data. Returns
        the new snapshot if successful, None otherwise.
        """
        def lookup_user(email):
            users = User.objects.filter(email=email)
            return users[0] if users.count() > 0 else None

        try:
            client = BugzillaClient(self.bug_tracker.base_url,
                                    self.bug_tracker.backend)
        except AttributeError:
            logging.error('Bugzilla backend %s not found' % self.bug_tracker.backend)
            return None
        
        if not client.login(self.bug_tracker.username,
                            self.bug_tracker.password):
            logging.error('Could not authenticate with Bugzilla')
            return None

        bug = client.get_bug(self.remote_tracker_id)
        return TaskSnapshot.objects.create(task=self, title=bug.summary,
                                           component=bug.component, status=bug.status,
                                           submitted_by=lookup_user(bug.submitted_by),
                                           assigned_to=lookup_user(bug.assigned_to),
                                           estimated_hours=int(bug.estimated_time),
                                           actual_hours=int(bug.actual_time),
                                           remaining_hours=int(bug.remaining_time))

import logging
from berserk2.bugzilla import *

def _create_task_snapshot(sender, instance, created, **kwargs):
    """
    Called from Task's post_save signal.
    
    Polls the BugTracker for the latest data for the Task, and creates a new
    TaskSnapshot for it.
    """
    instance.snapshot()

post_save.connect(_create_task_snapshot, sender=Task,
                  dispatch_uid='berserk2.sprints.models.Task')

class TaskSnapshot(models.Model):
    """
    A snapshot of the working data for a task.
    """
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    task = models.ForeignKey(Task, db_index=True)
    title = models.CharField(max_length=128)
    component = models.CharField(max_length=128)
    assigned_to = models.ForeignKey(User, related_name='assigned_to',
                                    null=True, db_index=True)
    submitted_by = models.ForeignKey(User, related_name='submitted_by', null=True)
    status = models.CharField(max_length=32)
    estimated_hours = models.IntegerField()
    actual_hours = models.IntegerField()
    remaining_hours = models.IntegerField()

    class Meta:
        get_latest_by = 'date'
    
    def __unicode__(self):
        return _("Snapshot of task %d at %s") % (self.task.id, self.date)
    
    def get_submitted_by_display(self):
        if self.submitted_by == None:
            return unicode(None)
        else:
            return self.submitted_by.first_name
    
    def get_assigned_to_display(self):
        if self.assigned_to == None:
            return unicode(None)
        else:
            return self.assigned_to.first_name

    def is_closed(self):
        """
        Returns True if the snapshot shows the Task is in a resolved state.
        """
        return (self.status == "RESOLVED" \
                or self.status == "CLOSED" \
                or self.status == "VERIFIED")

def _update_task_snapshot_cache(sender, instance, created, **kwargs):
    """
    Called by TaskSnapshot's post_save signal.
    
    Updates the TaskSnapshotCache with the most recent TaskSnapshot for the
    day.  This is to be used later by Sprint's get_users_load.
    """
    if not created: return

    day = instance.date.date()
    snaps_for_day = TaskSnapshotCache.objects.filter(date=day,
                                                     task_snapshot__task=instance.task)
    for c in snaps_for_day:
        if c.task_snapshot.date > instance.date:
            return # There's already a newer snapshot in the db

    snaps_for_day.delete()
    TaskSnapshotCache.objects.create(date=day,
                                     task_snapshot=instance)

post_save.connect(_update_task_snapshot_cache, sender=TaskSnapshot,
                  dispatch_uid='berserk2.sprints.models.TaskSnapshot')

class TaskSnapshotCache(models.Model):
    """
    A cache of the last TaskSnapshot of the day for a given Task.
    """
    date = models.DateField(db_index=True)
    task_snapshot = models.ForeignKey(TaskSnapshot, db_index=True)

    def __unicode__(self):
        return _("%s - #%d") % (self.date, self.task_snapshot.id)




def _workday_diff(start, end):
    return len([d for dy, d in date_range(start, end) if d.isoweekday() <= 5])

def _calc_load(rem, day, total_days, velocity):
    days_left = total_days - day
    hours_left = days_left * velocity
    return (float(rem) / float(hours_left)) * 100 \
        if hours_left > 0 else 0
