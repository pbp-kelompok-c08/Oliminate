from django import forms
from .models import User

# Form ini KHUSUS untuk registrasi
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
        # PERINGATAN KERAS: 
        # Kode ini menyimpan password sebagai plain text.
        # Metode set_password() tidak ada karena ini models.Model
        user = super().save(commit=True)
        return user

# Form ini KHUSUS untuk edit profil
class UserEditForm(forms.ModelForm):
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
        ]