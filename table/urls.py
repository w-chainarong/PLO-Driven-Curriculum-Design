"""
URL configuration for the 'table' application.
This file defines all route mappings between URLs and view functions
for curriculum management, course lists, CLO–KSEC mapping, and data synchronization.
"""

from django.urls import path
from . import views
from . import views_course
from . import views_plo
from . import views_ylo
from . import views_ksec
from . import views_ksec_select
from . import admin_views
from . import views_clo
from . import views_plo_summary


urlpatterns = [
    # ✅ Curriculum selection page
    path('', views.curriculum_select, name='curriculum_select'),

    # ✅ Main credit table
    path('curriculum/<int:curriculum_id>/credit-table/', views.credit_table, name='credit_table'),
    path('curriculum/<int:curriculum_id>/reset/', views.reset_credit_table, name='reset_credit_table'),

    # ✅ Course list (General, Core, Free Electives)
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/', 
         views_course.course_list, name='course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/save/', 
         views_course.save_course_list, name='save_course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/reset/', 
         views_course.reset_course_list, name='reset_course_list'),

    # ✅ Course list for PLO section
    path('curriculum/<int:curriculum_id>/plo_course_list/<int:row_id>/<int:semester>/', 
         views_plo.plo_course_list, name='plo_course_list'),
    path('curriculum/<int:curriculum_id>/plo_course_list/<int:row_id>/<int:semester>/save/', 
         views_plo.save_plo_course_list, name='save_plo_course_list'),

    # ✅ YLO-based study plan
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/', 
         views_ylo.ylo_study_plan, name='ylo_study_plan'),
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/save/', 
         views_ylo.save_ylo_studyplan, name='save_ylo_studyplan'),

    # ✅ Edit K/S/E/C items
    path('curriculum/<int:curriculum_id>/ksec/<int:semester>/<str:type>/', 
         views_ksec.ksec_edit, name='ksec_edit'),

    # ✅ Popup for K/S/E/C item selection
    path('curriculum/<int:curriculum_id>/select-ksec/', 
         views_ksec_select.ksec_item_select, name='ksec_item_select'),

    # ✅ Synchronization and Backup/Restore
    path('sync-db/', admin_views.sync_real_to_example, name='sync_real_to_example'),
    path('curriculum/<int:curriculum_id>/backup/', 
         views.sync_curriculum_real_to_example, name='sync_curriculum_real_to_example'),
    path('curriculum/<int:curriculum_id>/restore/', 
         views.sync_curriculum_example_to_real, name='sync_curriculum_example_to_real'),

    # ✅ Database download buttons
    path('download-db/all/', views.download_all_databases, name='download_all_databases'),
    path('download-db/<str:db_name>/', views.download_database, name='download_database'),

    # ✅ CLO–KSEC Mapping
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/', 
         views_clo.clo_ksec_map, name='clo_ksec_map'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/save/', 
         views_clo.save_clo_ksec_map, name='save_clo_ksec_map'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/reset/', 
         views_clo.reset_clo_ksec_map, name='reset_clo_ksec_map'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/save-session/', 
         views_clo.save_clo_ksec_to_session, name='save_clo_ksec_to_session'),

    # ✅ CLO summary by PLO
    path('curriculum/<int:curriculum_id>/plo-summary/', 
         views_plo_summary.plo_summary, name='plo_summary'),

    # ✅ Stacked bar graph for PLO credits
    path('curriculum/<int:curriculum_id>/plo-graph/', 
         views.plo_graph_from_creditrow, name='plo_graph_from_creditrow'),
]
