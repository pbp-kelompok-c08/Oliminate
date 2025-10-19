from django.shortcuts import render, redirect
from .models import User

'''
# Menampilkan profil user yang sedang login
def main_profile(request):
    user = User.objects.first()
    return render(request, 'main_profile.html', {'user_obj': user})

# Mengedit profil user yang sedang login
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.fakultas = request.POST.get('fakultas')
        if request.FILES.get('foto'):
            user.foto = request.FILES['foto']
        user.save()
        return redirect('users:main_profile')

    return render(request, 'edit_profile.html', {'user_obj': user})
'''

def main_profile(request):
    user = User.objects.first()
    return render(request, 'main_profile.html', {'user_obj': user})

def edit_profile(request):
    user = User.objects.first()
    return render(request, 'edit_profile.html', {'user_obj': user})
