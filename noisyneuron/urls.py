"""
URL configuration for the NoisyNeuron project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Create a simple dashboard view
@login_required
def dashboard_view(request):
    from django.shortcuts import render
    return render(request, 'dashboard.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('audio_processor/', include('audio_processor.urls')),
    path('api/audio/', include('audio_processor.urls')),
    path('markov_models/', include('markov_models.urls')),
    path('music_theory/', include('music_theory.urls')),
    path('instruments/', include('instruments.urls')),
    path('premium/', include('premium.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
    path('', TemplateView.as_view(template_name='index-modern.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
