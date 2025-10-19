from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import UserForm  

def edit_profile(request):
    user = get_object_or_404(User, id=request.user.id)
    form = UserForm(request.POST or None, request.FILES or None, instance=user)

    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main_profile')  

    context = {
        'form': form
    }
    return render(request, 'edit_profile.html', context)


def main_profile(request):
    try:
        user_obj = request.user.userprofile
    except Exception:
        user_obj = User.objects.first()

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            return redirect('users:main_profile')
    else:
        form = UserForm(instance=user_obj)
    
    context = {'form': form, 'user_obj': user_obj}

    return render(request, 'edit_profile.html', context)
