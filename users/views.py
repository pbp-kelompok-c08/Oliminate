from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import User
from .forms import UserForm

def register_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:main_profile')
    else:
        form = UserForm()
        
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
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:main_profile')
    else:
        form = UserForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form, 'user_obj': user})