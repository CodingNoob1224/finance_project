from django.urls import path
from finance import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add_fixed_deposit/', views.add_fixed_deposit, name='add_fixed_deposit'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('sell_stock/<int:stock_id>/', views.sell_stock, name='sell_stock'),
    path('analyze_stock/<int:stock_id>/', views.analyze_stock, name='analyze_stock'),
]