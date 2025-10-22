from django.forms import ModelForm
from ticketing.models import Ticket

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ['schedule', 'price', 'payment_method']
        widgets = {
            'schedule': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'payment_method': forms.RadioSelect(),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Harga tiket tidak valid.")
        return price