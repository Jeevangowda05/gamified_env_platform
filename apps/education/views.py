"""
Views for education app
"""

#from django.shortcuts import render, get_object_or_404
#from django.contrib.auth.mixins import LoginRequiredMixin
#from django.views.generic import ListView, DetailView, TemplateView
#from .models import EnvironmentalTopic

# REMOVED: Course, CourseEnrollment imports (now in core app)

#class TopicListView(ListView):
  #  """Display all environmental topics"""
  ## template_name = 'core/topic_list.html'
   # context_object_name = 'topics'

   # def get_queryset(self):
    #    return EnvironmentalTopic.objects.filter(is_active=True)

#class TopicDetailView(DetailView):
 #   """Detailed view of an environmental topic"""
  #  model = EnvironmentalTopic
   # template_name = 'core/topic_detail.html'
    #context_object_name = 'topic'

    #def get_queryset(self):
     #   return EnvironmentalTopic.objects.filter(is_active=True)

# REMOVED: CourseListView, CourseDetailView (now in core app)
