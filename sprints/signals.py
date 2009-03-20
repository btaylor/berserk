from datetime import datetime, date
from berserk2.sprints.models import Task, TaskSnapshot, TaskSnapshotCache

def update_task_snapshot_cache(sender, instance, created):
    """
    Called by TaskSnapshot's post_save signal.
    
    Updates the TaskSnapshotCache with the most recent TaskSnapshot for the
    day.  This is to be used later by Sprint's get_users_load.
    """
    if not created: return

    day = instance.date.date()
    snaps_for_day = TaskSnapshotCache.objects.filter(date=date_only)
    for c in snaps_for_day:
        if c.task_snapshot.date > instance.date:
            # There's already a newer snapshot in the db
            return

    snaps_for_day.delete()
    TaskSnapshotCache.objects.create(date=date_only,
                                     task_snapshot=instance)

import logging
from berserk2.bugzilla import *

def create_task_snapshot(sender, instance, created):
    """
    Called from Task's post_save signal.
    
    Polls the BugTracker for the latest data for the Task, and creates a new
    TaskSnapshot for it.
    """
    def lookup_user(email):
        users = User.objects.filter(email=email)
        return users[0] if users.count() > 0 else None

    tracker = instance.bug_tracker
    try:
        client = BugzillaClient(tracker.base_url, tracker.backend)
    except AttributeError:
        logging.error('Bugzilla backend %s not found' % tracker.backend)
        return
    
    if not client.login(tracker.username, tracker.password):
        logging.error('Could not authenticate with Bugzilla')
        return

    bug = client.get_bug(instance.remote_tracker_id)
    TaskSnapshot.objects.create(task=instance, title=bug.summary,
                                status=bug.status,
                                submitted_by=lookup_user(bug.submitted_by),
                                assigned_to=lookup_user(bug.assigned_to),
                                estimated_hours=int(bug.estimated_time),
                                actual_hours=int(bug.actual_time),
                                remaining_hours=int(bug.remaining_time))
