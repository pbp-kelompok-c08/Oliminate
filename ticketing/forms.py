from django import forms
from .models import Ticket

class TicketPurchaseForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['schedule', 'price', 'payment_method']
        widgets = {
            # TAMBAHKAN kelas Tailwind di sini
            'schedule': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            
            # TAMBAHKAN kelas Tailwind di sini
            'price': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 bg-gray-100 text-gray-600 focus:outline-none'
            }),
            
            # TAMBAHKAN kelas Tailwind di sini
            'payment_method': forms.RadioSelect(attrs={
                # Kelas ini akan diterapkan ke setiap <input type="radio">
                'class': 'h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 cursor-pointer'
            }),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Harga tiket tidak valid.")
        return price