from django.contrib import admin
from .models import FacultyDb,AdminDb,StudentDb,Subject,FacultySubject,Department,Class,TimeTable, Semester, Division
# Register your models here.
admin.site.register(FacultyDb)
admin.site.register(AdminDb)
admin.site.register(StudentDb)
admin.site.register(Subject)
admin.site.register(FacultySubject)
admin.site.register(Department)
admin.site.register(Class)
admin.site.register(TimeTable)
admin.site.register(Semester)
admin.site.register(Division)
