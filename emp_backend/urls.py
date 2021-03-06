"""emp_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""#
from django.contrib import admin
from django.urls import path
from emergency_app import views

urlpatterns = [
    # path('admin/', admin.site.urls),
	path('login/', views.login),
	path('getEmergencyContacts/', views.get_emergency_contacts),
	path('updateEmergencyContact/', views.update_emergency_contact),
	path('updateEmergencyContact/<int:surrogate_id>/', views.update_emergency_contact),
	path('getEmergencyNotifications/', views.get_emergency_notifications),
	path('setEmergencyNotifications/', views.set_emergency_notifications),
    path('getEvacuationAssistance/', views.get_evacuation_assistance),
    path('setEvacuationAssistance/', views.set_evacuation_assistance),
    path('getRelations/', views.get_relations),
    path('getNationCodes/', views.get_nation_codes),
    path('getStateCodes/', views.get_state_codes),
]
