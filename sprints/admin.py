from django import forms
from django.contrib import admin
from django.forms.util import ErrorList
from berserk2.bugzilla import BugzillaClient
from berserk2.sprints.models import BugTracker, Sprint, Task

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

class SprintAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'velocity')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('remote_tracker_id', 'bug_tracker')
    search_fields = (
        'tasksnapshot__title', 'tasksnapshot__status',
        'tasksnapshot__assigned_to__first_name', 'tasksnapshot__assigned_to__last_name',
        'tasksnapshot__submitted_by__first_name', 'tasksnapshot__submitted_by__last_name',
    )

admin.site.register(BugTracker, BugTrackerAdmin)
admin.site.register(Sprint, SprintAdmin)
admin.site.register(Task, TaskAdmin)
