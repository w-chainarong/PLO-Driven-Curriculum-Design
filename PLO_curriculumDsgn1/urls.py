from django.contrib import admin
from django.urls import path, include
from table import views
from table.admin_views import sync_real_to_example  # ✅ เพิ่มตรงนี้

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/sync/', sync_real_to_example, name='sync_real_to_example'),  # ✅ เพิ่มเส้นทางให้ปุ่ม Sync ใช้ได้
    path('', views.curriculum_select, name='curriculum_select'),
    path('', include('table.urls')),
]