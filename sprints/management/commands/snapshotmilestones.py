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

from datetime import datetime
from berserk2.sprints.models import Sprint, Task, Project

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Snapshots statistics about the current sprint's milestone"

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

            if sprint.milestone:
                log('       Fetching statistics for milestone %s' % sprint.milestone.name)
                sprint.milestone.snapshot_statistics()
            else:
                log('       Current sprint has no milestone set.  Exiting.')
