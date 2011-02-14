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

import sys
from datetime import datetime
from berserk2.sprints.models import Sprint, Task

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Creates snapshots of all the tasks in the current sprint"

    def handle_noargs(self, **options):
        def log(msg):
            print '[%s]: %s' % (datetime.now(), msg)

        log('Starting up')

        sprint = Sprint.objects.current()
        if sprint == None:
            log('   No active sprints found.  Exiting.')
            sys.exit()

        tasks = Task.objects.filter(sprints=sprint)
        for task in tasks:
            log('   Creating new snapshot of %d (#%s)' % (task.id, task.remote_tracker_id))
            task.snapshot()
