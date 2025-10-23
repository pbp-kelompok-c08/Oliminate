from django import forms
# Import kedua model baru dari models.py
from .models import Ticket, EventPrice 

# ==================================
# === 1. FORM BARU UNTUK PANITIA ===
# ==================================
class EventPriceForm(forms.ModelForm):
    """
    Form ini akan dipakai panitia untuk mengatur harga
    untuk sebuah Schedule.
    """
    class Meta:
        model = EventPrice
        fields = ['schedule', 'price']
        widgets = {
            'schedule': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Masukkan harga, misal: 50000'
            }),
        }

# ==================================
# === 2. FORM LAMA (DIUBAH) UNTUK USER ===
# ==================================
class TicketPurchaseForm(forms.ModelForm):
    """
    Form ini untuk user. Hapus 'price' dari sini.
    """
    class Meta:
        model = Ticket
        # HAPUS 'price' DARI SINI
        fields = ['schedule', 'payment_method']
        widgets = {
            'schedule': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'payment_method': forms.RadioSelect(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 cursor-pointer'
            }),
        }
    
    # HAPUS 'clean_price(self)' DARI SINI
    # def clean_price(self):
    #     ...

