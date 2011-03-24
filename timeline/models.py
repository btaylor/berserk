#
# Copyright (c) 2008-2011 Brad Taylor <brad@getcoded.net>
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

import re

from django.db import models
from django.contrib.auth.models import User
from django.template import Context, Template

from berserk2.bugtracker import BugTrackerFactory
from berserk2.timeline.managers import ActorManager
from berserk2.sprints.models import BugTracker, Task
from berserk2.core.templatetags.truncate import truncate_chars

class Actor(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    GENDER_CHOICES = (
        ('U', u'Unknown'),
        ('M', u'Male'),
        ('F', u'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    user = models.ForeignKey(User, null=True, blank=True)
    objects = ActorManager()

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)

    def get_reflexive_gender_pronoun(self):
        """
        Returns the lowercase reflexive gender pronoun (e.g.: himself, herself)
        for the actor's gender.
        """
        if self.gender == 'M':
            return 'himself'
        elif self.gender == 'F':
            return 'herself'
        else:
            return 'itself'

    def get_third_person_pronoun(self):
        """
        Returns the lowercase third-person gender pronoun (e.g.: He, She) for
        the actor's gender.
        """
        if self.gender == 'M':
            return 'he'
        elif self.gender == 'F':
            return 'her'
        else:
            return 'it'

class Event(models.Model):
    date = models.DateTimeField(editable=False, db_index=True)
    source = models.CharField(max_length=32)
    protagonist = models.ForeignKey(Actor, related_name='protagonist',
                                    null=True, db_index=True)
    deuteragonist = models.ForeignKey(Actor, related_name='deuteragonist',
                                      null=True, db_index=True)
    message = models.CharField(max_length=512)
    comment = models.TextField()
    task = models.ForeignKey(Task, related_name='task',
                             blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True)

    def __unicode__(self):
        return self.message

    def save(self, *args, **kwargs):
        if not self.id and not self.date:
            self.date = datetime.now()
        super(Event, self).save(*args, **kwargs)

    def get_message_for_display(self):
        proto_self = ''
        proto_caps_third = ''
        if self.protagonist:
            proto_self = self.protagonist.get_reflexive_gender_pronoun()
            proto_caps_third = self.protagonist.get_third_person_pronoun().title()

        deuter_self = ''
        if self.deuteragonist:
            deuter_self = self.deuteragonist.get_reflexive_gender_pronoun()

        task_link = ''
        if self.task:
            snap = self.task.get_latest_snapshot()
            task_link = '<a href="%s" target="_blank">#%s</a>' \
                        % (self.task.get_absolute_url(), self.task.remote_tracker_id)

        t = Template(self.message)
        return t.render(Context({
            'protagonist': self.protagonist, 'proto_self': proto_self,
            'proto_caps_third': proto_caps_third,
            'deuteragonist': self.deuteragonist, 'deuter_self': deuter_self,
            'task_link': task_link,
        }, autoescape=False))

    def get_task_for_display(self):
        if self.task:
            snap = self.task.get_latest_snapshot()
            return '#%s: %s' % (self.task.remote_tracker_id, snap.title)
        return ''
