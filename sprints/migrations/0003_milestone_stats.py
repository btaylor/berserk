
from south.db import db
from django.db import models
from berserk2.sprints.models import *

class Migration:

    def forwards(self, orm):

        # Adding model 'MilestoneStatisticsCache'
        db.create_table('sprints_milestonestatisticscache', (
            ('total_open_tasks', models.IntegerField()),
            ('total_estimated_hours', models.IntegerField()),
            ('total_remaining_hours', models.IntegerField()),
            ('milestone', models.ForeignKey(orm.Milestone)),
            ('date', models.DateField(auto_now_add=True, db_index=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('sprints', ['MilestoneStatisticsCache'])

        # Adding field 'Milestone.bug_tracker'
        db.add_column('sprints_milestone', 'bug_tracker', models.ForeignKey(orm.BugTracker))

        # Adding field 'Milestone.remote_tracker_name'
        db.add_column('sprints_milestone', 'remote_tracker_name', models.CharField(max_length=128))



    def backwards(self, orm):

        # Deleting model 'MilestoneStatisticsCache'
        db.delete_table('sprints_milestonestatisticscache')

        # Deleting field 'Milestone.bug_tracker'
        db.delete_column('sprints_milestone', 'bug_tracker_id')

        # Deleting field 'Milestone.remote_tracker_name'
        db.delete_column('sprints_milestone', 'remote_tracker_name')



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
        'sprints.milestone': {
            'Meta': {'get_latest_by': "'-end_date'"},
            'bug_tracker': ('models.ForeignKey', ['BugTracker'], {}),
            'end_date': ('models.DateField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '128'}),
            'remote_tracker_name': ('models.CharField', [], {'max_length': '128'}),
            'start_date': ('models.DateField', [], {})
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
            'milestone': ('models.ForeignKey', ['Milestone'], {'null': 'True', 'blank': 'True'}),
            'start_date': ('models.DateField', [], {}),
            'velocity': ('models.IntegerField', [], {'default': '6'})
        },
        'sprints.milestonestatisticscache': {
            'date': ('models.DateField', [], {'auto_now_add': 'True', 'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('models.ForeignKey', ['Milestone'], {}),
            'total_estimated_hours': ('models.IntegerField', [], {}),
            'total_open_tasks': ('models.IntegerField', [], {}),
            'total_remaining_hours': ('models.IntegerField', [], {})
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
