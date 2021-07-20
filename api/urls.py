from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('logout/', views.logout),
    path('ticket/', views.ticket),
    path('operator/close/', views.operator__close),
    path('operator/take/', views.operator__take),
    path('session/new/', views.session__new),
    path('session/limits/', views.session__limits),
    path('session/<int:session_id>/info/', views.session__info),
    path('session/<int:session_id>/<str:action_type>/', views.session__action),
    path('zone/<int:zone_id>/info/', views.zone__info),
    path('zone/<int:zone_id>/log/', views.zone__log),
]
