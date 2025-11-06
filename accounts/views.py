from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from .models import CustomUser, UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from .forms import SignUpForm, ProfileUpdateForm, UserUpdateForm
from audio_processor.models import AudioProject


class SignUpView(CreateView):
    """User registration view."""
    model = CustomUser
    form_class = SignUpForm
    template_name = 'accounts/signup_modern.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        """Process valid signup form."""
        response = super().form_valid(form)
        user = self.object
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Log the user in
        login(self.request, user)
        messages.success(self.request, 'Welcome to NoisyNeuron! Your account has been created successfully.')
        
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view."""
    model = UserProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        """Get or create user profile."""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user statistics
        audio_projects = AudioProject.objects.filter(user=user)
        
        context.update({
            'total_projects': audio_projects.count(),
            'completed_projects': audio_projects.filter(processing_status='completed').count(),
            'recent_projects': audio_projects[:5],
        })
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile."""
    model = UserProfile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """Get or create user profile."""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        """Process valid form."""
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile has been updated successfully.')
        return response


@login_required
def dashboard_view(request):
    """User dashboard view."""
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Get user statistics
    audio_projects = AudioProject.objects.filter(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'total_projects': audio_projects.count(),
        'completed_projects': audio_projects.filter(processing_status='completed').count(),
        'recent_projects': audio_projects[:5],
    }
    
    return render(request, 'accounts/dashboard.html', context)


def login_view(request):
    """Custom login view."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse('accounts:dashboard'))
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login_modern.html')


@login_required
def logout_view(request):
    """Custom logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')


# API Views for AJAX/REST functionality
@login_required
@require_http_methods(["GET"])
def api_user_profile(request):
    """Get user profile data as JSON."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return JsonResponse(serializer.data)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def api_update_profile(request):
    """Update user profile via API."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.POST, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True, 'data': serializer.data})
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors}, status=400)
    
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)