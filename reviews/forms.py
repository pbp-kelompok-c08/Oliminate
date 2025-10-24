# Di file: reviews/forms.py

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating':forms.HiddenInput(attrs={'id': 'rating-value'}),
            'comment': forms.Textarea(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-2 border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-300 focus:ring-opacity-50',
                    'rows': 8,
                    'placeholder': 'Ceritakan pengalaman Anda di sini...'
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating:
            raise forms.ValidationError("Silakan pilih rating Anda.")
        try:
            rating_int = int(float(rating))
            if not 1 <= rating_int <= 5:
                 raise forms.ValidationError("Nilai rating tidak valid.")
        except (ValueError, TypeError):
             raise forms.ValidationError("Format rating tidak valid.")
        return rating_int