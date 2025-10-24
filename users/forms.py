from django import forms
from .models import User

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
            'role',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
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
            'password',
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
            'password': 'Fill with old password if not changing' 
        }

        for field_name, placeholder_text in placeholders.items():
            if field_name in self.fields:
                field = self.fields[field_name]
                field.widget.attrs['placeholder'] = placeholder_text
                