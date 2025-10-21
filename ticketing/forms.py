from django.forms import ModelForm
from ticketing.models import Ticket

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["schedule", "buyer", "price", "purchase_date"]
    
    