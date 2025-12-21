from django.db import models
from scheduling.models import Schedule
# Ganti ini ke custom user model jika sudah siap, 
# untuk sekarang kita pakai user bawaan
from users.models import User
#from django.contrib.auth.models import User 
from django.utils import timezone

# ==================================
# === 1. TAMBAHKAN MODEL BARU INI ===
# ==================================
class EventPrice(models.Model):
    """
    Model ini menghubungkan Schedule (dari app lain) dengan harga.
    Panitia akan mengisi ini.
    """
    schedule = models.OneToOneField(
        Schedule, 
        on_delete=models.CASCADE, 
        related_name="price_info"
    )
    price = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Harga untuk {self.schedule}: Rp {self.price}"

# ==================================
# === 2. MODEL TICKET KAMU (TETAP SAMA) ===
# ==================================
class Ticket(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('ewallet', 'E-Wallet'),
        ('transfer', 'Transfer Bank'),
        ('credit', 'Kartu Kredit'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Belum Dibayar'),
        ('paid', 'Sudah Dibayar'),
    ]

    id = models.BigAutoField(primary_key=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='tickets')
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    # Field 'price' ini sudah benar. JANGAN DIHAPUS.
    # Ini untuk 'struk' pembelian.
    price = models.DecimalField(max_digits=15, decimal_places=2)
    
    purchase_date = models.DateTimeField(default=timezone.now)
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)

    # tambahan untuk simulasi pembayaran
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='ewallet'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        # Saya ganti 'pending' jadi 'unpaid' agar sesuai pilihan
        default='unpaid' 
    )

    def __str__(self):
        return f"Ticket #{self.id} - {self.buyer.username} ({'Used' if self.is_used else 'Unused'})"