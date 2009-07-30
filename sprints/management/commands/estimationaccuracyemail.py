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
    help = "Emails users at the end of the sprint with statistics about the accuracy of their estimates"

    def handle_noargs(self, **options):
        def log(msg):
            print '[%s]: %s' % (datetime.now(), msg)

        log('Starting up')

        past_sprints = Sprint.objects.filter(end_date__lt=date.today()) \
                                     .order_by('-end_date')
        if past_sprints.count() == 0:   
            log('   No past sprints found.  Exiting.')
            return

        sprint = past_sprints[0]
        for user in User.objects.filter(email__isnull=False):
            log('   Examining user %s...' % user)

            if user.email == "":
                log('   - User has no email address.  Aborting.')
                continue

            cached_snaps = TaskSnapshotCache.objects.filter(task_snapshot__task__sprints=sprint,
                                                            task_snapshot__assigned_to=user,
                                                            date=sprint.end_date) \
                                                    .filter(Q(task_snapshot__status='RESOLVED') \
                                                            | Q(task_snapshot__status='CLOSED') \
                                                            | Q(task_snapshot__status='VERIFIED')) \
                                                    .order_by('-date') \
                                                    .select_related()
            if cached_snaps.count() == 0:
                log('   - User closed no bugs this iteration or was assigned no tasks.  Aborting.')
                continue
            
            t = loader.get_template('email/estimation-accuracy-subject.txt')
            c = Context({
                'user': user, 'sprint': sprint,
                'completed': [c.task_snapshot for c in cached_snaps]
            })

            # Make sure to strip out any trailing newlines as they will cause sendmail
            # to reject the email
            subject = t.render(c).rstrip()

            t = loader.get_template('email/estimation-accuracy.txt')
            body = t.render(c)
        
            print "About to send to %s" % user
            print subject
            print body
            print

            #email = EmailMessage (subject, body, settings.EMAIL_FROM,
            #                      to=[user.email], bcc=["%s <%s>" % i for i in settings.MANAGERS])
            #email.send(fail_silently=False)
