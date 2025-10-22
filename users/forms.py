# users/forms.py
from django import forms
from .models import User

# UserRegisterForm Anda (tidak berubah)
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',      
            'phone_number',
        ]

    def save(self, commit=True):
        user = super().save(commit=True)
        return user


# ==========================================================
# PERBARUI UserEditForm ANDA DENGAN INI
# ==========================================================
class UserEditForm(forms.ModelForm):
    # TAMBAHKAN: Buat field password baru yang tidak wajib diisi
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'profile_picture',
            'fakultas',
            'password',  # TAMBAHKAN: 'password' di sini
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        placeholders = {
            'username': 'Your Username',
            'first_name': 'Your First Name',
            'last_name': 'Your Last Name',
            'email': 'your.email@example.com',
            'phone_number': '+628123456789',
            'fakultas': 'Choose your faculty',
            # TAMBAHKAN: Placeholder untuk password baru
            'password': 'Leave blank if not changing' 
        }

        for field_name, placeholder_text in placeholders.items():
            if field_name in self.fields:
                field = self.fields[field_name]
                # Atur atribut placeholder
                field.widget.attrs['placeholder'] = placeholder_text
                
    # TAMBAHKAN: save() method untuk handle password opsional
    def save(self, commit=True):
        user = super().save(commit=False)
        # Ambil password dari data yang sudah divalidasi
        password = self.cleaned_data.get("password")
        
        # Hanya update password jika pengguna memasukkan password baru
        if password:
            # Karena Anda pakai models.Model, kita simpan sbg plain text
            user.password = password
        
        if commit:
            user.save()
            
        return user