from django.contrib import admin

from .models import StudentNotification, TeacherCourse, TeacherNotification, TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'years_of_experience')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'department')


@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'course', 'created_at')
    search_fields = ('teacher__email', 'course__title')


@admin.register(TeacherNotification)
class TeacherNotificationAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'event_type', 'title', 'is_read', 'is_archived', 'created_at')
    list_filter = ('event_type', 'is_read', 'is_archived', 'created_at')
    search_fields = ('teacher__email', 'title', 'message', 'actor__email')


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'event_type', 'title', 'is_read', 'is_archived', 'created_at')
    list_filter = ('event_type', 'is_read', 'is_archived', 'created_at')
    search_fields = ('recipient__email', 'title', 'message', 'actor__email')
