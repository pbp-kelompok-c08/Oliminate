from django.forms import ModelForm
from merchandise.models import Merchandise

class MerchandiseForm(ModelForm):
    class Meta:
        model = Merchandise
        fields = ["name", "category", "price", "stock", "description", "image_url"]