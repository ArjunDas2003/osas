# Generated by Django 5.1.5 on 2025-03-22 15:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminDb',
            fields=[
                ('username', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('fullname', models.CharField(default='Administrator', max_length=200)),
                ('password', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(max_length=6, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Division',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='FacultyDb',
            fields=[
                ('facid', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('fullname', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=255)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='osasapp.department')),
            ],
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.department')),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.division')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.semester')),
            ],
        ),
        migrations.CreateModel(
            name='StudentDb',
            fields=[
                ('studentid', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('fullname', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=255)),
                ('class_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.class')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=6)),
                ('class_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.class')),
            ],
        ),
        migrations.CreateModel(
            name='FacultySubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='osasapp.facultydb')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faculties', to='osasapp.subject')),
            ],
        ),
        migrations.CreateModel(
            name='TimeTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday')], max_length=10)),
                ('period', models.IntegerField()),
                ('class_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.class')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.facultydb')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osasapp.subject')),
            ],
            options={
                'unique_together': {('class_info', 'day', 'period')},
            },
        ),
    ]
