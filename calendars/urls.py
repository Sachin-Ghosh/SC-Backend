# calendars/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.calendar_event_list, name='calendar-event-list'),
    path('events/create/', views.create_calendar_event, name='create-calendar-event'),
    path('events/<int:pk>/', views.calendar_event_detail, name='calendar-event-detail'),
    path('events/<int:pk>/attendance/', views.event_attendance, name='event-attendance'),
]