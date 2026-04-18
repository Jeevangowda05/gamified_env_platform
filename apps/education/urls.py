"""
URL configuration for education app
"""

from django.urls import path
#from . import views

app_name = 'api_education'

urlpatterns = [
 #   path('topics/', views.TopicListView.as_view(), name='topic_list'),
  #  path('topics/<slug:slug>/', views.TopicDetailView.as_view(), name='topic_detail'),
    # REMOVED: course URLs (now handled by core app)
]
