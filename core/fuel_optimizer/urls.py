from django.urls import path
from . import views

urlpatterns = [
    path('api/optimal-route/', views.OptimalRouteView.as_view(), name='optimal_route'),
]