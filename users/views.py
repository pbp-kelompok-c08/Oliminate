from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserEditForm
from .models import User

# ==========================================================
# FUNGSI LOGIN YANG HILANG (TAMBAHKAN INI)
# ==========================================================
def login_user(request):
    if request.method == 'POST':
        username_from_form = request.POST.get('username')
        password_from_form = request.POST.get('password')
        
        try:
            # 1. Cari user di model kustom Anda
            user = User.objects.get(username=username_from_form)
            
            # 2. Cek password plain text (SANGAT TIDAK AMAN!)
            if user.password == password_from_form:
                # 3. Login manual dengan menyimpan ID user di session
                request.session['user_id'] = user.id
                return redirect('users:main_profile')
            else:
                # Password salah
                return render(request, 'login.html', {'error': 'Password atau username salah'})
        except User.DoesNotExist:
            # User tidak ada
            return render(request, 'login.html', {'error': 'Password atau username salah'})
    
    # Jika method-nya GET, tampilkan halaman login
    return render(request, 'login.html')

# ==========================================================
# FUNGSI LOGOUT (ANDA AKAN BUTUH INI)
# ==========================================================
def logout_user(request):
    try:
        # Hapus user_id dari session
        del request.session['user_id']
    except KeyError:
        pass
    return redirect('users:login')

# ==========================================================
# FUNGSI ANDA YANG SUDAH ADA (DENGAN PERBAIKAN)
# ==========================================================
def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Redirect ke view login KUSTOM Anda, bukan 'login' global
            return redirect('users:login') 
    else:
        form = UserRegisterForm()
        
    return render(request, 'register.html', {'form': form})


def main_profile(request):
    # PERBAIKAN: Ambil user dari session, bukan request.user
    try:
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
    except (KeyError, User.DoesNotExist):
        # Jika tidak ada di session, paksa login
        return redirect('users:login')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'main_profile.html', context)


def edit_profile(request):
    # PERBAIKAN: Ambil user dari session, bukan request.user
    try:
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
    except (KeyError, User.DoesNotExist):
        return redirect('users:login')

    if request.method == 'POST':
        # Gunakan 'instance=user' yang sudah kita dapatkan dari session
        form = UserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:main_profile')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form, 'user_obj': user})