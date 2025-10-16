from django import forms
from .models import Schedule

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['category', 'team1', 'team2', 'location', 'date', 'time', 'status', 'image_url', 'caption']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'caption': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tambahkan deskripsi atau caption...'}),
        }
