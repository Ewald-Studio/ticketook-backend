from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('logout/', views.logout),
    path('ticket/', views.ticket),
    path('operator/take/', views.operator__take),
    path('session/new/', views.session__new),
    path('session/info/<int:session_id>/', views.session__info),
    path('session/<str:action_type>/', views.session__action),
]
