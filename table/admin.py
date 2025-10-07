from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Curriculum

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sync_to_real_link')  # ✅ เพิ่มคอลัมน์แสดงปุ่ม

    def sync_to_real_link(self, obj):
        url = reverse('sync_curriculum_example_to_real', args=[obj.pk])
        return format_html(
            '<a href="{}" style="'
            'background-color: #1976D2; color: white; padding: 6px 12px; '
            'border-radius: 6px; text-decoration: none; font-weight: bold;">'
            'Sync to real</a>',
            url
        )

    sync_to_real_link.short_description = 'Sync this to real'
