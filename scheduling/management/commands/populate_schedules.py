import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from scheduling.models import Schedule
from datetime import datetime
from django.utils.dateparse import parse_date, parse_time

# [TAMBAHKAN INI]
# Impor 'static' untuk membuat URL /static/images/...
from django.templatetags.static import static

# [TAMBAHKAN INI]
# Buat mapping antara nama Kategori di CSV (setelah di-normalisasi)
# dengan nama file gambar di static/images/
# Kuncinya adalah NAMA KATEGORI (UPPERCASE) dan juga variants
IMAGE_MAP = {
    # Uppercase
    'FUTSAL': 'images/futsal.png',
    'BASKET': 'images/basket.png',
    'SEPAK BOLA': 'images/sepak_bola.png',
    'VALORANT': 'images/valorant.png',
    'TENIS LAPANGAN': 'images/tenis_lapangan.png',
    'VOLI': 'images/voli.png',
    'VOLLY': 'images/voli.png',
    'HOCKEY': 'images/hockey.png',
    'TENIS MEJA': 'images/tenis_meja.png',
    'BADMINTON': 'images/badminton.png',
    'MLBB': 'images/mlbb.jpg',
    # Title case / lowercase variants (for manually created schedules)
    'Futsal': 'images/futsal.png',
    'Basket': 'images/basket.png',
    'Basketball': 'images/basket.png',
    'Sepak Bola': 'images/sepak_bola.png',
    'Valorant': 'images/valorant.png',
    'Tenis Lapangan': 'images/tenis_lapangan.png',
    'Voli': 'images/voli.png',
    'Volly': 'images/voli.png',
    'Hockey': 'images/hockey.png',
    'Tenis Meja': 'images/tenis_meja.png',
    'Badminton': 'images/badminton.png',
    'Mlbb': 'images/mlbb.jpg',
    # Default
    'DEFAULT': 'images/default.png'
}

class Command(BaseCommand):
    help = 'Populate Schedule table from static/csv/schedule.csv'

    def handle(self, *args, **options):
        # Hapus data lama (opsional, tapi bagus untuk testing)
        self.stdout.write('Menghapus data Schedule lama...')
        Schedule.objects.all().delete()

        # Path ke file CSV
        csv_file_path = os.path.join(settings.BASE_DIR, 'static', 'csv', 'schedule.csv')

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f'File CSV tidak ditemukan di: {csv_file_path}'))
            return

        self.stdout.write('Mulai memuat data jadwal...')

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                # Gunakan DictReader agar bisa panggil kolom by nama (cth: row['Kategori'])
                reader = csv.DictReader(file)
                
                count = 0
                for row in reader:
                    # Bersihkan nama kategori (hapus spasi, uppercase)
                    # Ini penting, karena di CSV ada "BASKET " (dengan spasi)
                    kategori_csv = row['Kategori'].strip().upper()
                    # Menangani kasus seperti "TENIS MEJA"
                    kategori_csv = ' '.join(kategori_csv.split())

                    # --- [INI BAGIAN PENTING YANG DIMODIFIKASI] ---
                    
                    # 1. Dapatkan path file gambar dari IMAGE_MAP
                    #    Gunakan .get() untuk fallback ke 'DEFAULT' jika kategori tidak ada di map
                    image_file_path = IMAGE_MAP.get(kategori_csv, IMAGE_MAP['DEFAULT'])
                    
                    # 2. Buat URL statis lengkap (cth: /static/images/futsal.png)
                    #    Ini yang akan disimpan di model URLField
                    gambar_url = static(image_file_path)
                    
                    # ----------------------------------------------

                    # Konversi tanggal dan jam
                    # Format di CSV: DD-MM-YYYY
                    try:
                        tanggal = datetime.strptime(row['Tanggal'], '%d-%m-%Y').date()
                    except ValueError:
                        self.stderr.write(f"Format tanggal salah di baris {reader.line_num}: {row['Tanggal']}")
                        continue
                        
                    # Format di CSV: HH.MM-HH.MM (kita ambil jam mulainya)
                    try:
                        jam_mulai_str = row['Jam'].split('-')[0].strip().replace('.', ':')
                        jam = parse_time(jam_mulai_str)
                    except (IndexError, ValueError):
                        self.stderr.write(f"Format jam salah di baris {reader.line_num}: {row['Jam']}")
                        continue

                    # Buat atau update objek Schedule
                    Schedule.objects.create(
                        category=kategori_csv, # Simpan nama kategori yang sudah bersih
                        team1=row['Tim1'].strip(),
                        team2=row['Tim2'].strip(),
                        location=row['Lokasi'].strip(),
                        date=tanggal,
                        time=jam,
                        image_url=gambar_url,  # <-- [TAMBAHKAN INI] Simpan URL gambar
                        # 'organizer' bisa null/kosong jika script ini tidak punya user
                    )
                    count += 1

            self.stdout.write(self.style.SUCCESS(f'Berhasil! {count} jadwal pertandingan telah dimuat.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Terjadi error: {e}'))