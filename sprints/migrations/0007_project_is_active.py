# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding field 'Project.is_active'
        db.add_column('sprints_project', 'is_active', self.gf('django.db.models.fields.BooleanField')(default=True), keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Project.is_active'
        db.delete_column('sprints_project', 'is_active')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sprints.bugtracker': {
            'Meta': {'unique_together': "(('base_url', 'product', 'backend'),)", 'object_name': 'BugTracker'},
            'backend': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'sprints.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.BugTracker']"}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remote_tracker_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'sprints.milestonestatisticscache': {
            'Meta': {'unique_together': "(('date', 'milestone'),)", 'object_name': 'MilestoneStatisticsCache'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.Milestone']"}),
            'total_estimated_hours': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_open_tasks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_remaining_hours': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'sprints.project': {
            'Meta': {'object_name': 'Project'},
            'bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['sprints.BugTracker']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'sprints.sprint': {
            'Meta': {'ordering': "['-end_date']", 'object_name': 'Sprint'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.Milestone']", 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sprints'", 'to': "orm['sprints.Project']"}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'velocity': ('django.db.models.fields.IntegerField', [], {'default': '6'})
        },
        'sprints.task': {
            'Meta': {'unique_together': "(('remote_tracker_id', 'bug_tracker'),)", 'object_name': 'Task'},
            'bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.BugTracker']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remote_tracker_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'sprints': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sprints.Sprint']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'sprints.tasksnapshot': {
            'Meta': {'object_name': 'TaskSnapshot'},
            'actual_hours': ('django.db.models.fields.IntegerField', [], {}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assigned_to'", 'null': 'True', 'to': "orm['auth.User']"}),
            'component': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'estimated_hours': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remaining_hours': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.Task']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'sprints.tasksnapshotcache': {
            'Meta': {'unique_together': "(('date', 'task_snapshot'),)", 'object_name': 'TaskSnapshotCache'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task_snapshot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.TaskSnapshot']"})
        }
    }

    complete_apps = ['sprints']
