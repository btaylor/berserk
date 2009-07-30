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

from django import forms
from django.db.models import Q
from django.contrib import admin
from django.forms.util import ErrorList
from berserk2.bugzilla import BugzillaClient
from berserk2.sprints.models import BugTracker, Sprint, Task, Milestone

from django.utils.translation import ugettext as _

class BugTrackerAdminForm(forms.ModelForm):
    class Meta:
        model = BugTracker

    def clean_base_url(self):
        return self.cleaned_data['base_url'].rstrip('/')

    def clean(self):
        backend = self.cleaned_data['backend']
        base_url = self.cleaned_data['base_url']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        
        if BugzillaClient.validate_backend(backend):
            client = BugzillaClient(base_url, backend)
            if not client.login(username, password):
                raise forms.ValidationError(_('Authentication credentials could not be validated.  Either your username or password is incorrect, or the server could not be reached.'))
        else:
            self._errors['backend'] = ErrorList([
                _("Backend '%s' could not be found.  Make sure it can be found in berserk2.bugzilla.backends.") % backend
            ])
            del self.cleaned_data['backend']
        
        return self.cleaned_data

class BugTrackerAdmin(admin.ModelAdmin):
    list_display = ('product', 'base_url')
    search_fields = ['product', 'base_url']
    
    form = BugTrackerAdminForm
    fieldsets = (
        ('General', {
            'fields': ('base_url', 'product', 'backend')
        }),
        ('Authentication', {
            'fields': ('username', 'password')
        }),
    )

class SprintAdminForm(forms.ModelForm):
    class Meta:
        model = Sprint

    def clean(self):
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']

        if start_date >= end_date:
            self.errors['start_date'] = ErrorList([
                _('The start date must be less than the end date.')
            ])
            del self.cleaned_data['start_date']
        
        sprints = Sprint.objects.filter(
            (Q(start_date__lte=start_date) & Q(end_date__gte=start_date))
            | (Q(start_date__gte=start_date) & Q(start_date__lte=end_date))
        )
        
        if self.initial.has_key('id'):
            sprints = sprints.exclude(pk=self.initial['id'])

        if sprints.count() > 0:
            del self.cleaned_data['start_date']
            del self.cleaned_data['end_date']
            raise forms.ValidationError(_('The start or end dates overlap Sprint #%d from %s.') % (sprints[0].id, sprints[0]))

        return self.cleaned_data

class SprintAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'velocity')
    form = SprintAdminForm

class TaskAdmin(admin.ModelAdmin):
    list_display = ('remote_tracker_id', 'bug_tracker')
    search_fields = (
        'remote_tracker_id', 'tasksnapshot__title', 'tasksnapshot__status',
        'tasksnapshot__assigned_to__first_name', 'tasksnapshot__assigned_to__last_name',
        'tasksnapshot__submitted_by__first_name', 'tasksnapshot__submitted_by__last_name',
    )

class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)

admin.site.register(BugTracker, BugTrackerAdmin)
admin.site.register(Sprint, SprintAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Milestone, MilestoneAdmin)
