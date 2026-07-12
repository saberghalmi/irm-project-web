from django.contrib import admin
from .models import IRMImage, Annotation


@admin.register(IRMImage)
class IRMImageAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'exam_date', 'avc_type', 'uploaded_at')
    search_fields = ('patient_name', 'avc_type')
    list_filter = ('avc_type', 'exam_date')


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('image', 'user', 'created_at')
    search_fields = ('user__username', 'image__patient_name')
    list_filter = ('created_at',)
