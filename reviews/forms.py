from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(attrs={'id': 'id_rating_value'}), 
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please share your thoughts...'}),
        }