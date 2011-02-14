
from south.db import db
from django.db import models
from berserk2.sprints.models import *

class Migration:

    def forwards(self, orm):

        # Adding model 'TaskSnapshot'
        db.create_table('sprints_tasksnapshot', (
            ('status', models.CharField(max_length=32)),
            ('submitted_by', models.ForeignKey(orm['auth.User'], related_name='submitted_by', null=True)),
            ('task', models.ForeignKey(orm.Task, db_index=True)),
            ('title', models.CharField(max_length=128)),
            ('actual_hours', models.IntegerField()),
            ('component', models.CharField(max_length=128)),
            ('assigned_to', models.ForeignKey(orm['auth.User'], related_name='assigned_to', null=True, db_index=True)),
            ('date', models.DateTimeField(auto_now_add=True, db_index=True)),
            ('estimated_hours', models.IntegerField()),
            ('id', models.AutoField(primary_key=True)),
            ('remaining_hours', models.IntegerField()),
        ))
        db.send_create_signal('sprints', ['TaskSnapshot'])

        # Adding model 'Task'
        db.create_table('sprints_task', (
            ('remote_tracker_id', models.CharField(max_length=32)),
            ('bug_tracker', models.ForeignKey(orm.BugTracker)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('sprints', ['Task'])

        # Adding model 'TaskSnapshotCache'
        db.create_table('sprints_tasksnapshotcache', (
            ('date', models.DateField(db_index=True)),
            ('task_snapshot', models.ForeignKey(orm.TaskSnapshot, db_index=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('sprints', ['TaskSnapshotCache'])

        # Adding model 'Sprint'
        db.create_table('sprints_sprint', (
            ('end_date', models.DateField()),
            ('default_bug_tracker', models.ForeignKey(orm.BugTracker, null=True)),
            ('start_date', models.DateField()),
            ('velocity', models.IntegerField(default=6)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('sprints', ['Sprint'])

        # Adding model 'BugTracker'
        db.create_table('sprints_bugtracker', (
            ('username', models.CharField(max_length=32)),
            ('product', models.CharField(max_length=128, verbose_name='Product Name')),
            ('base_url', models.CharField(max_length=256, verbose_name='Bugzilla Base URL')),
            ('password', models.CharField(max_length=32)),
            ('id', models.AutoField(primary_key=True)),
            ('backend', models.CharField(max_length=32)),
        ))
        db.send_create_signal('sprints', ['BugTracker'])

        # Adding ManyToManyField 'Task.sprints'
        db.create_table('sprints_task_sprints', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('task', models.ForeignKey(Task, null=False)),
            ('sprint', models.ForeignKey(Sprint, null=False))
        ))

        # Creating unique_together for [base_url, product, backend] on BugTracker.
        db.create_unique('sprints_bugtracker', ['base_url', 'product', 'backend'])

        # Creating unique_together for [remote_tracker_id, bug_tracker] on Task.
        db.create_unique('sprints_task', ['remote_tracker_id', 'bug_tracker_id'])



    def backwards(self, orm):

        # Deleting model 'TaskSnapshot'
        db.delete_table('sprints_tasksnapshot')

        # Deleting model 'Task'
        db.delete_table('sprints_task')

        # Deleting model 'TaskSnapshotCache'
        db.delete_table('sprints_tasksnapshotcache')

        # Deleting model 'Sprint'
        db.delete_table('sprints_sprint')

        # Deleting model 'BugTracker'
        db.delete_table('sprints_bugtracker')

        # Dropping ManyToManyField 'Task.sprints'
        db.delete_table('sprints_task_sprints')

        # Deleting unique_together for [base_url, product, backend] on BugTracker.
        db.delete_unique('sprints_bugtracker', ['base_url', 'product', 'backend'])

        # Deleting unique_together for [remote_tracker_id, bug_tracker] on Task.
        db.delete_unique('sprints_task', ['remote_tracker_id', 'bug_tracker_id'])



    models = {
        'sprints.tasksnapshot': {
            'Meta': {'get_latest_by': "'date'"},
            'actual_hours': ('models.IntegerField', [], {}),
            'assigned_to': ('models.ForeignKey', ['User'], {'related_name': "'assigned_to'", 'null': 'True', 'db_index': 'True'}),
            'component': ('models.CharField', [], {'max_length': '128'}),
            'date': ('models.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True'}),
            'estimated_hours': ('models.IntegerField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'remaining_hours': ('models.IntegerField', [], {}),
            'status': ('models.CharField', [], {'max_length': '32'}),
            'submitted_by': ('models.ForeignKey', ['User'], {'related_name': "'submitted_by'", 'null': 'True'}),
            'task': ('models.ForeignKey', ['Task'], {'db_index': 'True'}),
            'title': ('models.CharField', [], {'max_length': '128'})
        },
        'sprints.task': {
            'Meta': {'unique_together': "('remote_tracker_id','bug_tracker')"},
            'bug_tracker': ('models.ForeignKey', ['BugTracker'], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'remote_tracker_id': ('models.CharField', [], {'max_length': '32'}),
            'sprints': ('models.ManyToManyField', ['Sprint'], {'blank': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'sprints.tasksnapshotcache': {
            'date': ('models.DateField', [], {'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'task_snapshot': ('models.ForeignKey', ['TaskSnapshot'], {'db_index': 'True'})
        },
        'sprints.sprint': {
            'Meta': {'ordering': "['-end_date']", 'get_latest_by': "'end_date'"},
            'default_bug_tracker': ('models.ForeignKey', ['BugTracker'], {'null': 'True'}),
            'end_date': ('models.DateField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('models.DateField', [], {}),
            'velocity': ('models.IntegerField', [], {'default': '6'})
        },
        'sprints.bugtracker': {
            'Meta': {'unique_together': "('base_url','product','backend')"},
            'backend': ('models.CharField', [], {'max_length': '32'}),
            'base_url': ('models.CharField', [], {'max_length': '256', 'verbose_name': "'Bugzilla Base URL'"}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'password': ('models.CharField', [], {'max_length': '32'}),
            'product': ('models.CharField', [], {'max_length': '128', 'verbose_name': "'Product Name'"}),
            'username': ('models.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['sprints']
