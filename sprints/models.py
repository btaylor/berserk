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
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.utils.translation import ugettext as _

class BugTracker(models.Model):
    """
    A Bugzilla bug tracker.
    """
    product = models.CharField(max_length=128)
    base_url = models.CharField(max_length=256)
    backend = models.CharField(max_length=32)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    def __unicode__(self):
        return str(product_id)

class Sprint(models.Model):
    """
    A work-iteration represented by a date range and a velocity, or the number
    of expected work-hours per day.
    """
    start_date = models.DateField()
    end_date = models.DateField()
    velocity = models.IntegerField(default=6)

    def __unicode__(self):
        return _("%s - %s") % (self.start_date.strftime("%b. %e"),
                               self.end_date.strftime("%b. %e %Y"))

    def is_active(self):
        """
        Returns true if the current date is between the start and end dates of
        the Sprint. 
        """
        return date.today() >= self.start_date \
               and date.today() <= self.end_date

    def get_iteration_days(self):
        """
        Returns the number of absolute days between the start and end dates of
        the Sprint.
        """
        return (self.end_date - self.start_date).days

    def get_users_load(self):
        pass

class Task(models.Model):
    """
    A work task associated with zero or more sprints.
    """
    remote_tracker_id = models.CharField(max_length=32, unique=True)
    sprints = models.ManyToManyField(Sprint, blank=True)
    bug_tracker = models.ForeignKey(BugTracker)

    def __unicode__(self):
        return _("Issue #%s") % (self.remote_tracker_id)

    def get_latest_snapshot(self):
        """
        Returns the most recent snapshot of the Task.  If no snapshots found,
        returns None.
        """
        try:
            return TaskSnapshot.objects.filter(task=self).order_by("-date")[0]
        except IndexError:
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
                                           status=bug.status,
                                           submitted_by=lookup_user(bug.submitted_by),
                                           assigned_to=lookup_user(bug.assigned_to),
                                           estimated_hours=int(bug.estimated_time),
                                           actual_hours=int(bug.actual_time),
                                           remaining_hours=int(bug.remaining_time))

    def get_remote_tracker_url(self):
        """
        Returns a remote URL to the Task.
        """
        return bug_tracker.user_url_format % self.remote_tracker_id

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
    date = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task)
    title = models.CharField(max_length=128)
    assigned_to = models.ForeignKey(User, related_name='assigned_to', null=True)
    submitted_by = models.ForeignKey(User, related_name='submitted_by', null=True)
    status = models.CharField(max_length=32)
    estimated_hours = models.IntegerField()
    actual_hours = models.IntegerField()
    remaining_hours = models.IntegerField()
    
    def __unicode__(self):
        return _("Snapshot of task %d at %s") % (self.task.id, self.date)

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
    snaps_for_day = TaskSnapshotCache.objects.filter(date=day)
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
    date = models.DateField()
    task_snapshot = models.ForeignKey(TaskSnapshot)

    def __unicode__(self):
        return _("%s - #%d") % (self.date, self.task_snapshot.id)

def _date_range(start, end):
    date = start
    while date <= end:
        yield ((date - start).days, date)
        date = date + timedelta(1)

def _weekday_diff(start, end):
    return len([d for dy, d in date_range(start, end) if d.isoweekday() <= 5])
