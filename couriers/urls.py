from django.urls import path, include

from couriers import views


app_name = 'couriers'


urlpatterns = [
    path('', views.couriers),
    path('<int:courier_id>', views.courier_view)
]

