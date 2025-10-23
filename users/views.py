from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserEditForm
from .models import User 

def register_user(request):
    if request.user.is_authenticated:
        return redirect('users:main_profile')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return redirect('users:main_profile') 
    else:
        form = UserRegisterForm()
        
    return render(request, 'register.html', {'form': form})

@login_required
def main_profile(request):
    user = request.user 
    
    context = {
        'user_obj': user,
    }
    return render(request, 'main_profile.html', context)

@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            
            user_instance = form.save(commit=False)
            
            new_password = form.cleaned_data.get('password')
            
            if new_password:
                user_instance.set_password(new_password)
            
            user_instance.save()
            
            if new_password:
                update_session_auth_hash(request, user_instance)
            
            return redirect('users:main_profile')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form, 'user_obj': user})