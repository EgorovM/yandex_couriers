from django.urls import path

from orders import views


app_name = 'orders'

urlpatterns = [
    path('', views.orders),
    path('assign/', views.assign),
    path('complete/', views.complete),
]

