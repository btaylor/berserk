#!/usr/bin/env python

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

from datetime import date, datetime, timedelta

from berserk2.sprints.models import *

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Count, Sum, Q
from django.template import loader, Context
from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Emails users who have not updated their remaining hours in UPDATE_HOURS_REMINDER_DAYS"

    def handle_noargs(self, **options):
        def log(msg):
            print '[%s]: %s' % (datetime.now(), msg)

        log('Starting up')

        for project in Project.objects.all():
            log('   Examining %s...' % project)

            sprint = Sprint.objects.current(project)
            if sprint == None:
                log('       No active sprints found.  Exiting.')
                continue

            for user in User.objects.all():
                log('       Examining user %s...' % user)

                if user.email == "":
                    log('       - User has no email address.  Aborting.')
                    continue

                if TaskSnapshot.objects.filter(task__sprints=sprint,
                                               assigned_to=user) \
                                       .exclude(Q(status__istartswith='RESOLVED') | Q(status__istartswith='CLOSED') \
                                                | Q(status__istartswith='VERIFIED')) \
                                       .count() == 0:
                    log('       - User has no tasks assigned this sprint.')
                    continue

                sprint_tasks = TaskSnapshotCache.objects.filter(task_snapshot__task__sprints=sprint,
                                                                task_snapshot__assigned_to=user)

                past_tasks = sprint_tasks.filter(date=date.today() - timedelta(settings.UPDATE_HOURS_REMINDER_DAYS))
                todays_tasks = sprint_tasks.filter(date=date.today())

                if past_tasks.aggregate(Count('id')) != todays_tasks.aggregate(Count('id')):
                    log('       - User has a different number of tasks than in the past.')
                    continue

                if past_tasks.aggregate(Sum('task_snapshot__remaining_hours')) != todays_tasks.aggregate(Sum('task_snapshot__remaining_hours')):
                    log('       - User has updated their hours in the last %s days.' % settings.UPDATE_HOURS_REMINDER_DAYS)
                    continue

                log('       - User has not updated their hours!')

                t = loader.get_template('email/update-hours-reminder-subject.txt')
                c = Context({
                    'date': date.today(), 'remind_days': settings.UPDATE_HOURS_REMINDER_DAYS,
                    'user': user, 'sprint': sprint, 'project': project,
                    'task_snapshot_cache': todays_tasks
                })

                # Make sure to strip out any trailing newlines as they will cause sendmail
                # to reject the email
                subject = t.render(c).rstrip()

                t = loader.get_template('email/update-hours-reminder.txt')
                body = t.render(c)

                email = EmailMessage (subject, body, settings.EMAIL_FROM,
                                      to=[user.email], bcc=["%s <%s>" % i for i in settings.MANAGERS])
                email.send(fail_silently=False)
