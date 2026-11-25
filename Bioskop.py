import json
import random
import re
import sys
import threading
import webbrowser
from datetime import date, datetime, time
from http.server import BaseHTTPRequestHandler, HTTPServer

NAMA_BIOSKOP = "Tixket"
NAMA_HARI = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")


#class film
class Film:
    jumlah_film = 0
    total_harga = 0

    #constructor
    def __init__ (self, kode, judul, durasi, harga, usia_min = 0, genre = "", tagline = ""):
        self.kode = kode
        self.judul = judul
        self.usia_min = usia_min
        self.genre = genre
        self.tagline = tagline
        self.__durasi = 0    #private
        self.__harga = 0     #private
        self.durasi = durasi #lewat setter
        self.harga = harga   #lewat setter
        Film.jumlah_film += 1
        Film.total_harga += harga

    #property & setter
    @property
    def durasi (self):
        return self.__durasi

    @durasi.setter
    def durasi (self, nilai):
        if not Film.validasi_durasi(nilai):
            raise ValueError(f"Durasi film tidak valid: {nilai} menit")
        self.__durasi = nilai

    @property
    def harga (self):
        return self.__harga

    @harga.setter
    def harga (self, nilai):
        if nilai <= 0:
            raise ValueError("Harga tiket harus lebih dari 0")
        self.__harga = nilai

    def ke_dict (self):
        return {"id": self.kode, "judul": self.judul, "durasi": self.__durasi,
                "harga": self.__harga, "usia_min": self.usia_min,
                "genre": self.genre, "tagline": self.tagline}

    def __str__ (self):
        return f"{self.judul} ({self.durasi} menit) - Rp{self.harga}"

    #class method
    @classmethod
    def dari_string (cls, teks):
        #format: kode;judul;durasi;harga;usia;genre;tagline
        kode, judul, durasi, harga, usia, genre, tagline = teks.split(";")
        return cls(kode, judul, int(durasi), int(harga), int(usia), genre, tagline)

    @classmethod
    def jumlah (cls):
        return f"Jumlah film = {cls.jumlah_film}"

    @classmethod
    def rata_rata_harga (cls):
        return f"Rata-rata harga tiket = {cls.total_harga / cls.jumlah_film}"

    #static method
    @staticmethod
    def validasi_durasi (durasi):
        return isinstance(durasi, int) and 30 <= durasi <= 300


#class jadwal
class Jadwal:
    BARIS = "ABCDE"
    KOLOM = 6

    #constructor
    def __init__ (self, id_jadwal, film, studio, tanggal, jam):
        self.id_jadwal = id_jadwal
        self.film = film
        self.studio = studio
        self.tanggal = tanggal
        self.jam = jam            #contoh "13:15"
        self.__terpesan = set()   #private, kursi yang sudah dipesan

    @property
    def hari (self):
        return NAMA_HARI[self.tanggal.weekday()]

    @property
    def sisa_kursi (self):
        return Jadwal.total_kursi() - len(self.__terpesan)

    @property
    def kursi_terpesan (self):
        return sorted(self.__terpesan)

    def sudah_lewat (self):
        #true kalau jam tayang sudah lewat dari sekarang
        jam, menit = (int(x) for x in self.jam.split(":"))
        return datetime.combine(self.tanggal, time(jam, menit)) <= datetime.now()

    def kursi_tersedia (self, kode):
        return kode not in self.__terpesan

    def pesan_kursi (self, kode):
        if not Jadwal.validasi_kode_kursi(kode):
            raise ValueError(f"Kode kursi tidak valid: {kode}")
        if not self.kursi_tersedia(kode):
            raise ValueError(f"Kursi {kode} sudah dipesan")
        self.__terpesan.add(kode)

    def ke_dict (self):
        return {"id": self.id_jadwal, "film_id": self.film.kode, "studio": self.studio,
                "tanggal": self.tanggal.isoformat(), "hari": self.hari, "jam": self.jam,
                "sisa": self.sisa_kursi, "terpesan": self.kursi_terpesan,
                "lewat": self.sudah_lewat(),
                "akhir_pekan": Bioskop.akhir_pekan(self.hari),
                "harga": Bioskop.hitung_harga(self.film.harga, self.hari)}

    def __str__ (self):
        return f"{self.film.judul} | {self.hari} {self.jam} | Studio {self.studio}"

    #class method
    @classmethod
    def total_kursi (cls):
        return len(cls.BARIS) * cls.KOLOM

    #static method
    @staticmethod
    def validasi_kode_kursi (kode):
        #kode yang benar: baris A-E, kolom 1-6 (contoh B3)
        return re.fullmatch(f"[{Jadwal.BARIS}][1-{Jadwal.KOLOM}]", kode) is not None


#class tiket
class Tiket:
    nomor_berikutnya = 1

    #constructor with validation (email dicek lewat setter)
    def __init__ (self, email, metode, jadwal, kursi, harga):
        self.kode = Tiket.buat_kode()
        self.__email = ""
        self.email = email
        self.metode = metode
        self.jadwal = jadwal
        self.kursi = kursi
        self.__harga = harga

    @property
    def email (self):
        return self.__email

    @email.setter
    def email (self, nilai):
        nilai = nilai.strip().lower()
        if not Tiket.validasi_email(nilai):
            raise ValueError("Format email tidak valid")
        self.__email = nilai

    @property
    def harga (self):
        return self.__harga

    def ke_dict (self):
        return {"kode": self.kode, "email": self.__email, "metode": self.metode,
                "kursi": self.kursi, "harga": self.__harga,
                "film": self.jadwal.film.judul, "film_id": self.jadwal.film.kode,
                "studio": self.jadwal.studio, "hari": self.jadwal.hari,
                "tanggal": self.jadwal.tanggal.isoformat(), "jam": self.jadwal.jam}

    def __str__ (self):
        return f"Tiket {self.kode} | {self.jadwal.film.judul} | kursi {self.kursi} | {self.__email}"

    #class method
    @classmethod
    def buat_kode (cls):
        kode = f"TKT{cls.nomor_berikutnya:03d}"
        cls.nomor_berikutnya += 1
        return kode

    #static method
    @staticmethod
    def validasi_email (email):
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()) is not None


#class bioskop
class Bioskop:
    TAMBAHAN_AKHIR_PEKAN = 10000
    MAKS_KURSI = 8
    METODE_BAYAR = ("QRIS", "Transfer Bank", "E-Wallet", "Kartu Debit")

    #constructor
    def __init__ (self, nama):
        self.nama = nama
        self.__daftar_film = {}
        self.__daftar_jadwal = {}
        self.__riwayat = []
        self.__pendapatan = 0

    @property
    def pendapatan (self):
        return self.__pendapatan

    @property
    def riwayat (self):
        return list(self.__riwayat)

    def tambah_film (self, film):
        self.__daftar_film[film.kode] = film

    def tambah_jadwal (self, jadwal):
        if jadwal.film.kode not in self.__daftar_film:
            raise ValueError("Film belum terdaftar di bioskop")
        self.__daftar_jadwal[jadwal.id_jadwal] = jadwal

    def cari_jadwal (self, id_jadwal):
        jadwal = self.__daftar_jadwal.get(id_jadwal)
        if jadwal is None:
            raise ValueError("Jadwal tidak ditemukan")
        return jadwal

    def rincian_harga (self, id_jadwal, jumlah):
        jadwal = self.cari_jadwal(id_jadwal)
        satuan = Bioskop.hitung_harga(jadwal.film.harga, jadwal.hari)
        return {"satuan": satuan, "jumlah": jumlah, "total": Bioskop.hitung_total(satuan, jumlah)}

    def pesan_tiket (self, email, metode, id_jadwal, daftar_kursi, usia_ok = False):
        #cek semua dulu, kalau ada yang salah pesanan dibatalkan semua
        jadwal = self.cari_jadwal(id_jadwal)
        if jadwal.sudah_lewat():
            raise ValueError("Film ini sudah mulai tayang. Pilih jam tayang lain.")
        if not Tiket.validasi_email(email):
            raise ValueError("Format email tidak valid")
        if metode not in Bioskop.METODE_BAYAR:
            raise ValueError("Pilih metode pembayaran")
        if jadwal.film.usia_min and not usia_ok:
            raise ValueError(f"Film ini untuk usia {jadwal.film.usia_min}+. "
                             "Centang konfirmasi usia terlebih dahulu.")
        kode_kursi = [k.upper() for k in daftar_kursi]
        if not kode_kursi:
            raise ValueError("Pilih minimal 1 kursi")
        if len(kode_kursi) > Bioskop.MAKS_KURSI:
            raise ValueError(f"Maksimal {Bioskop.MAKS_KURSI} kursi per pemesanan")
        if len(set(kode_kursi)) != len(kode_kursi):
            raise ValueError("Ada kursi yang dipilih dua kali")
        for kode in kode_kursi:
            if not Jadwal.validasi_kode_kursi(kode):
                raise ValueError(f"Kode kursi tidak valid: {kode}")
            if not jadwal.kursi_tersedia(kode):
                raise ValueError(f"Kursi {kode} sudah dipesan")

        harga = Bioskop.hitung_harga(jadwal.film.harga, jadwal.hari)
        total = Bioskop.hitung_total(harga, len(kode_kursi))
        hasil = []
        for kode in kode_kursi:
            jadwal.pesan_kursi(kode)
            hasil.append(Tiket(email, metode, jadwal, kode, harga))
        self.__riwayat.extend(hasil)
        self.__pendapatan += total
        return hasil, total

    def ringkasan (self):
        #semua data dikirim ke browser dalam bentuk dict
        return {
            "bioskop": self.nama,
            "hari_ini": date.today().isoformat(),
            "films": [f.ke_dict() for f in self.__daftar_film.values()],
            "jadwal": [j.ke_dict() for j in self.__daftar_jadwal.values()],
            "denah": {"baris": Jadwal.BARIS, "kolom": Jadwal.KOLOM},
            "aturan": {"maks_kursi": Bioskop.MAKS_KURSI,
                       "metode_bayar": list(Bioskop.METODE_BAYAR),
                       "tambahan_akhir_pekan": Bioskop.TAMBAHAN_AKHIR_PEKAN},
        }

    #static method
    @staticmethod
    def akhir_pekan (hari):
        return hari in ("Sabtu", "Minggu")

    @staticmethod
    def hitung_harga (harga_dasar, hari):
        #sabtu & minggu harganya naik
        if Bioskop.akhir_pekan(hari):
            return harga_dasar + Bioskop.TAMBAHAN_AKHIR_PEKAN
        return harga_dasar

    @staticmethod
    def hitung_total (harga_satuan, jumlah):
        return harga_satuan * jumlah

    #class method
    @classmethod
    def ubah_tarif_akhir_pekan (cls, tambahan):
        cls.TAMBAHAN_AKHIR_PEKAN = tambahan


#class penghubung browser dan bioskop (khusus untuk GUI web)
class PenanganRequest(BaseHTTPRequestHandler):
    bioskop = None   #diisi di main()

    def log_message (self, *args):
        pass   #supaya terminal tidak penuh log

    def _kirim (self, data, tipe = "application/json; charset=utf-8", kode = 200):
        isi = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(kode)
        self.send_header("Content-Type", tipe)
        self.send_header("Content-Length", str(len(isi)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(isi)

    def do_GET (self):
        if self.path == "/api/data":
            self._kirim(self.bioskop.ringkasan())
        elif self.path == "/favicon.ico":
            self._kirim(b"", "image/x-icon", 204)
        elif self.path in ("/", "/index.html"):
            self._kirim(halaman().encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._kirim({"error": "Halaman tidak ditemukan"}, kode = 404)

    def do_POST (self):
        panjang = int(self.headers.get("Content-Length", 0))
        try:
            d = json.loads(self.rfile.read(panjang) or b"{}")
            self._kirim(self._proses(self.path, d))
        except (ValueError, KeyError, TypeError) as e:
            self._kirim({"error": str(e) or "Data tidak valid."}, kode = 400)

    def _proses (self, jalur, d):
        b = self.bioskop
        if jalur == "/api/harga":
            return b.rincian_harga(d.get("id_jadwal", ""), int(d.get("jumlah", 0)))
        if jalur == "/api/pesan":
            kursi = d.get("kursi")
            if not isinstance(kursi, list):
                raise ValueError("Daftar kursi tidak valid")
            tiket, total = b.pesan_tiket(str(d.get("email", "")), str(d.get("metode", "")),
                                         d.get("id_jadwal", ""), [str(k) for k in kursi],
                                         bool(d.get("usia_ok")))
            for t in tiket:
                print("Tiket terbit:", t.kode, t.email, t.kursi)
            return {"total": total, "tiket": [t.ke_dict() for t in tiket]}
        raise ValueError("Alamat tidak dikenal.")


def buat_data_contoh ():
    bioskop = Bioskop(NAMA_BIOSKOP)

    #film dibuat lewat constructor dan lewat class method dari_string
    film = {
        "f1": Film("f1", "Petualangan Nusantara", 110, 45000, 0, "Petualangan",
                   "Satu peta tua, tujuh pulau, tanpa jalan pulang."),
        "f2": Film.dari_string("f2;Misteri Rumah Tua;95;45000;17;Misteri;"
                               "Lampu di lantai dua itu selalu menyala sendiri."),
        "f3": Film.dari_string("f3;Cinta di Kota Hujan;102;45000;13;Drama;"
                               "Hujan turun tiga hari, dan dia belum juga pergi."),
        "f4": Film("f4", "Gol di Menit Terakhir", 98, 45000, 0, "Olahraga",
                   "Skor imbang, waktu hampir habis, dan satu tendangan penentu."),
    }
    for f in film.values():
        bioskop.tambah_film(f)

    #jam tayang hari ini, tiap film punya studio sendiri
    jam_tayang = {"f1": ("10:45", "13:15", "16:00", "18:45", "21:30"),
                  "f2": ("11:30", "14:00", "17:00", "19:30", "22:00"),
                  "f3": ("10:30", "12:45", "15:30", "18:15", "21:00"),
                  "f4": ("11:00", "13:30", "16:15", "19:00", "21:45")}

    #sebagian kursi diisi acak biar denahnya tidak kosong semua
    acak = random.Random(7)
    semua_kursi = [f"{b}{k}" for b in Jadwal.BARIS for k in range(1, Jadwal.KOLOM + 1)]
    hari_ini = date.today()
    nomor = 1
    for studio, (kode_film, daftar_jam) in enumerate(jam_tayang.items(), start = 1):
        for jam in daftar_jam:
            jadwal = Jadwal(f"J{nomor}", film[kode_film], studio, hari_ini, jam)
            for kode in acak.sample(semua_kursi, acak.randint(5, 14)):
                jadwal.pesan_kursi(kode)
            bioskop.tambah_jadwal(jadwal)
            nomor += 1
    return bioskop


def halaman ():
    depan, _, belakang = NAMA_BIOSKOP.partition(" ")
    return (HALAMAN.replace("{{DEPAN}}", depan.upper())
                   .replace("{{BELAKANG}}", belakang.upper())
                   .replace("{{NAMA}}", NAMA_BIOSKOP))


#demo di terminal (tanpa GUI): python bioskop.py terminal
def demo_terminal ():
    bioskop = Bioskop(NAMA_BIOSKOP)
    film1 = Film("f1", "Petualangan Nusantara", 110, 45000)
    film2 = Film.dari_string("f2;Misteri Rumah Tua;95;50000;17;Misteri;tagline")
    bioskop.tambah_film(film1)
    bioskop.tambah_film(film2)

    print (film1)
    print (film2)
    print (Film.jumlah())
    print (Film.rata_rata_harga())

    #coba setter, durasi minus ditolak
    try:
        film1.durasi = -5
    except ValueError as e:
        print ("Setter menolak:", e)

    #jadwal 23:59 supaya selalu bisa dipesan
    jadwal = Jadwal("J1", film1, 1, date.today(), "23:59")
    bioskop.tambah_jadwal(jadwal)
    print (jadwal)

    hasil, total = bioskop.pesan_tiket("budi@mail.com", "QRIS", "J1", ["A1", "A2"])
    for t in hasil:
        print (t)
    print ("Total bayar:", total)
    print ("Sisa kursi:", jadwal.sisa_kursi)

    #kursi yang sama dipesan lagi, harus ditolak
    try:
        bioskop.pesan_tiket("andi@mail.com", "QRIS", "J1", ["A1"])
    except ValueError as e:
        print ("Ditolak:", e)

    print ("Harga hari Sabtu:", Bioskop.hitung_harga(45000, "Sabtu"))


def main ():
    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        demo_terminal()
        return
    PenanganRequest.bioskop = buat_data_contoh()
    server = None
    for port in range(8000, 8020):
        try:
            server = HTTPServer(("127.0.0.1", port), PenanganRequest)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("Tidak ada port yang kosong (8000-8019).")
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"{NAMA_BIOSKOP} berjalan di {url}  (tekan Ctrl+C untuk berhenti)")
    threading.Timer(0.6, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSampai jumpa!")


#tampilan web (html, css, javascript)
HALAMAN = r"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{NAMA}} | Pesan Tiket Bioskop</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='13' fill='%23E4472B' stroke='%231B1A17' stroke-width='3'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#F4EDE0; --paper-2:#EADFC9; --paper-3:#FBF7EE; --ink:#1B1A17;
  --red:#E4472B; --mustard:#F0B429; --teal:#1F6F6B;
  --line:2px solid var(--ink); --shadow:6px 6px 0 var(--ink);
  --pad:clamp(18px,4vw,56px);
  --font:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif;
  --mono:'DM Mono',ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace;
  --ease:cubic-bezier(.2,.8,.2,1);
}
*,*::before,*::after{box-sizing:border-box}
*{margin:0}
[hidden]{display:none!important}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--paper);color:var(--ink);line-height:1.5;-webkit-font-smoothing:antialiased;min-height:100vh;overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;z-index:100;pointer-events:none;opacity:.09;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
button{font:inherit;color:inherit;cursor:pointer}
.mono{font-family:var(--mono)}
:focus-visible{outline:3px solid var(--red);outline-offset:3px}
::selection{background:var(--mustard);color:var(--ink)}

.rise{animation:rise .8s var(--ease) both;animation-delay:calc(var(--i,0)*90ms)}
@keyframes rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}

/* header */
.bar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px var(--pad);border-bottom:var(--line)}
.logo{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none;font-size:1.2rem;letter-spacing:-.03em}
.logo i{width:16px;height:16px;border-radius:50%;background:var(--red);border:var(--line)}
.logo b{font-weight:800}
.logo span{font-weight:400;letter-spacing:.08em;font-size:.8rem;padding-top:3px}
.logo span:empty{display:none}
.bar-note{font-size:.76rem;opacity:.7}

/* hero */
.hero{position:relative;padding:clamp(40px,8vw,96px) var(--pad) clamp(36px,6vw,72px)}
.kicker{display:inline-flex;align-items:center;gap:10px;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:22px}
.live{width:10px;height:10px;border-radius:50%;background:var(--red);animation:kedip 1.6s ease-in-out infinite}
@keyframes kedip{50%{opacity:.25}}
.hero h1{font-size:clamp(3.3rem,11vw,9.6rem);line-height:.9;font-weight:800;letter-spacing:-.05em}
.hero h1 em{position:relative;display:inline-block;font-style:normal;color:var(--red)}
.scribble{position:absolute;left:-2%;bottom:-.1em;width:104%;height:.22em;overflow:visible}
.scribble path{fill:none;stroke:var(--mustard);stroke-width:9;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;animation:gambar 1.1s .7s var(--ease) forwards}
@keyframes gambar{to{stroke-dashoffset:0}}
.lead{margin-top:30px;font-size:clamp(1.05rem,1.6vw,1.3rem)}
.lead span{display:block}
@media(min-width:760px){.lead .l1{white-space:nowrap}}
.badge{position:absolute;right:var(--pad);top:clamp(28px,6vw,70px);width:clamp(104px,15vw,176px);height:auto;rotate:8deg}
.badge-ring{transform-origin:60px 60px;animation:putar 24s linear infinite}
@keyframes putar{to{transform:rotate(360deg)}}

.sec-title{display:flex;align-items:center;gap:14px;font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;letter-spacing:-.03em;margin-bottom:36px}
.num{display:grid;place-items:center;width:38px;height:38px;border:var(--line);border-radius:50%;font-size:.8rem;font-weight:500;letter-spacing:0;background:var(--mustard)}

/* poster */
.films,.booking{padding:28px var(--pad) 64px}
.films{border-top:var(--line);padding-top:48px}
.poster-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:44px 36px}
.poster{display:block;text-align:left;background:none;border:0;padding:0;animation:rise .8s var(--ease) both;animation-delay:calc(var(--i,0)*110ms + 200ms)}
.poster-art{position:relative;aspect-ratio:3/4;border:var(--line);box-shadow:var(--shadow);background:var(--paper-2);transition:transform .3s var(--ease),box-shadow .3s var(--ease)}
.poster-art svg{display:block;width:100%;height:100%}
.poster:hover .poster-art{transform:translate(-4px,-4px) rotate(-.8deg);box-shadow:11px 11px 0 var(--ink)}
.poster.is-active .poster-art{box-shadow:8px 8px 0 var(--red)}
.age{position:absolute;top:-14px;right:-12px;display:grid;place-items:center;width:46px;height:46px;border:var(--line);border-radius:50%;background:var(--mustard);font-family:var(--mono);font-weight:500;font-size:.82rem;rotate:10deg}
.chosen{position:absolute;left:-12px;top:20px;padding:4px 12px;background:var(--red);color:var(--paper);border:var(--line);font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;rotate:-5deg;opacity:0;transform:scale(.7);transition:.3s var(--ease)}
.poster.is-active .chosen{opacity:1;transform:none}
.poster h3{margin-top:22px;font-size:1.45rem;line-height:1.1;font-weight:800;letter-spacing:-.03em}
.poster .meta{margin-top:6px;font-size:.8rem;opacity:.7}
.poster .from{margin-top:10px;font-size:.95rem}
.poster .from b{font-weight:800}

/* booking */
.booking{padding-top:40px;background:var(--paper-2);min-height:70vh;animation:rise .7s var(--ease) both}
.back{display:inline-block;margin-bottom:22px;padding:6px 14px;border:var(--line);border-radius:99px;background:var(--paper);color:var(--ink);text-decoration:none;font-size:.8rem;transition:background .18s,transform .18s var(--ease)}
.back:hover{background:var(--mustard);transform:translateX(-3px)}
.pick-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:0}
.pick-seat{width:100%;max-width:720px;margin:0 auto}
.film-head{display:flex;align-items:flex-end;gap:26px;margin-bottom:44px}
.film-head .thumb{flex:none;width:118px;aspect-ratio:3/4;border:var(--line);box-shadow:4px 4px 0 var(--ink);rotate:-3deg}
.film-head .thumb svg{display:block;width:100%;height:100%}
.film-head h3{font-size:clamp(1.9rem,4vw,3rem);line-height:1;font-weight:800;letter-spacing:-.04em}
.film-head .tagline{margin-top:10px;max-width:38ch;font-size:1.05rem}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.pill{padding:3px 12px;border:var(--line);border-radius:99px;font-size:.76rem;background:var(--paper)}
.pill.age-pill{background:var(--mustard)}
.block{margin-bottom:48px}
.block-title{display:flex;align-items:baseline;gap:14px;margin-bottom:18px;font-size:1.2rem;font-weight:800;letter-spacing:-.02em}
.hint{font-size:.76rem;font-weight:400;opacity:.65}

.day{display:flex;align-items:center;flex-wrap:wrap;gap:10px 14px;margin-bottom:14px}
.day-label{width:108px;font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;line-height:1.3}
.day-label small{display:block;font-size:.68rem;letter-spacing:0;text-transform:none;opacity:.65}
.show{display:flex;flex-direction:column;align-items:flex-start;padding:8px 18px 8px 16px;background:var(--paper);border:var(--line);border-radius:14px;line-height:1.2;text-align:left;transition:transform .2s var(--ease),background .2s,color .2s}
.show b{font-family:var(--mono);font-weight:500;font-size:1.1rem}
.show small{font-family:var(--mono);font-size:.68rem;opacity:.7}
.show:hover:not(:disabled){transform:translateY(-2px);background:var(--mustard)}
.show.is-on{background:var(--ink);color:var(--paper)}
.show:disabled{opacity:.4;cursor:not-allowed}
.show:disabled b{text-decoration:line-through}

.hall{max-width:720px;padding:28px clamp(14px,3vw,32px) 22px;background:var(--paper);border:var(--line);box-shadow:var(--shadow)}
.screen{position:relative;height:54px;margin:0 6% 34px;border-top:6px solid var(--ink);border-radius:50% 50% 0 0/100% 100% 0 0;background:linear-gradient(to bottom,rgba(240,180,41,.55),transparent)}
.screen span{position:absolute;left:50%;top:14px;translate:-50% 0;font-size:.7rem;letter-spacing:.4em;opacity:.7}
.seats{display:grid;gap:10px}
.seat-row{display:grid;gap:10px;align-items:center}
.row-label{font-family:var(--mono);font-size:.76rem;text-align:center;opacity:.55}
.seat{aspect-ratio:1/.92;min-width:0;padding:0;background:var(--paper-3);border:var(--line);border-radius:12px 12px 5px 5px;font-family:var(--mono);font-size:.7rem;transition:transform .18s var(--ease),background .18s,box-shadow .18s}
.seat:hover:not(:disabled){transform:translateY(-3px);background:var(--mustard)}
.seat.is-pick{background:var(--red);color:var(--paper);transform:translateY(-3px);box-shadow:0 4px 0 var(--ink)}
.seat:disabled{cursor:not-allowed;color:transparent;border-color:rgba(27,26,23,.3);background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(27,26,23,.22) 4px 6px),var(--paper-2)}
.legend{display:flex;flex-wrap:wrap;gap:8px 22px;margin-top:26px;padding:0;list-style:none;font-size:.74rem}
.legend li{display:flex;align-items:center;gap:8px}
.sw{width:18px;height:16px;border:var(--line);border-radius:6px 6px 3px 3px}
.sw-free{background:var(--paper-3)}
.sw-pick{background:var(--red)}
.sw-taken{background:repeating-linear-gradient(135deg,transparent 0 3px,rgba(27,26,23,.3) 3px 5px),var(--paper-2);border-color:rgba(27,26,23,.35)}

/* kartu tiket (di bawah pilih kursi) */
.ticket-card{display:grid;grid-template-columns:minmax(0,.85fr) 26px minmax(0,1.15fr);max-width:1000px;margin:8px auto 0;background:var(--paper-3);border:var(--line);box-shadow:var(--shadow)}
.tc-left{padding:24px 26px 26px;background:var(--mustard)}
.tc-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em}
.tc-left h3{margin-top:6px;font-size:1.7rem;line-height:1.05;font-weight:800;letter-spacing:-.035em}
.tc-when{margin-top:8px;font-size:.8rem}
.tc-perf{position:relative;margin:-2px 0;
  background:radial-gradient(circle at 50% 0,var(--paper-2) 0 11px,var(--ink) 11px 13px,transparent 13px),
             radial-gradient(circle at 50% 100%,var(--paper-2) 0 11px,var(--ink) 11px 13px,transparent 13px),
             linear-gradient(to right,var(--mustard) 50%,var(--paper-3) 50%)}
.tc-perf::before{content:"";position:absolute;top:20px;bottom:20px;left:50%;border-left:2px dashed var(--ink)}
.tc-body{padding:18px 24px 26px}
.tc-seats{display:flex;flex-wrap:wrap;gap:8px;min-height:36px;align-items:center;margin-top:20px}
.seat-chip{padding:3px 12px;background:var(--red);color:var(--paper);border:var(--line);border-radius:8px 8px 4px 4px;font-family:var(--mono);font-size:.85rem;animation:pop .25s var(--ease)}
@keyframes pop{from{transform:scale(.6);opacity:0}}
.tc-seats .empty{font-size:.9rem;opacity:.65}
.tc-price{margin:18px 0 0;padding-top:14px;border-top:2px solid var(--ink)}
.tc-price .total{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.tc-price dt{font-weight:800}
.tc-price dt small{display:block;font-family:var(--mono);font-weight:400;font-size:.72rem;opacity:.7;min-height:1.2em}
.tc-price dd{font-family:var(--mono);font-size:1.7rem;font-weight:500;letter-spacing:-.04em}

.field{display:block;margin-bottom:20px}
.field span,.pay legend{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;opacity:.7}
.field input{width:100%;padding:6px 0 8px;background:transparent;border:0;border-bottom:var(--line);border-radius:0;font:inherit;font-size:1.1rem;color:var(--ink);transition:border-color .2s,background .2s}
.field input::placeholder{color:rgba(27,26,23,.38);font-size:.95rem}
.field input:focus{outline:none;border-color:var(--red);background:rgba(240,180,41,.18)}

.pay{border:0;padding:0;margin:0 0 20px;min-width:0}
.pay legend{padding:0;margin-bottom:10px}
.pay-opts{display:flex;flex-wrap:wrap;gap:8px}
.pay-opt{position:relative}
.pay-opt input{position:absolute;opacity:0;inset:0;cursor:pointer}
.pay-opt span{display:block;padding:6px 14px;border:var(--line);border-radius:99px;background:var(--paper);font-family:var(--mono);font-size:.78rem;transition:background .18s,color .18s,transform .18s var(--ease)}
.pay-opt:hover span{background:var(--mustard)}
.pay-opt input:checked + span{background:var(--ink);color:var(--paper)}
.pay-opt input:focus-visible + span{outline:3px solid var(--red);outline-offset:3px}

.check{display:flex;align-items:flex-start;gap:12px;margin-bottom:18px;font-size:.9rem;line-height:1.35;cursor:pointer}
.check input{position:absolute;opacity:0}
.check i{flex:none;width:22px;height:22px;margin-top:1px;border:var(--line);border-radius:6px;background:var(--paper);display:grid;place-items:center;transition:background .18s}
.check i::after{content:"";width:6px;height:11px;border:solid var(--paper);border-width:0 3px 3px 0;rotate:45deg;translate:0 -1px;scale:0;transition:scale .18s var(--ease)}
.check input:checked + i{background:var(--red)}
.check input:checked + i::after{scale:1}
.check input:focus-visible + i{outline:3px solid var(--red);outline-offset:3px}

.tc-note{min-height:1.5em;margin:2px 0 14px;font-size:.84rem}
.tc-note.is-bad{color:var(--red);font-weight:600}

.btn{width:100%;padding:15px 22px;background:var(--red);color:var(--paper);border:var(--line);font-weight:800;font-size:1.05rem;letter-spacing:-.01em;box-shadow:4px 4px 0 var(--ink);transition:transform .15s var(--ease),box-shadow .15s var(--ease),background .2s}
.btn:hover:not(:disabled){transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}
.btn:active:not(:disabled){transform:translate(3px,3px);box-shadow:0 0 0 var(--ink)}
.btn:disabled{background:var(--paper-2);color:rgba(27,26,23,.45);box-shadow:none;cursor:not-allowed}
.btn-light{width:auto;background:var(--paper);color:var(--ink)}

/* footer */
.foot{background:var(--ink);color:var(--paper);padding:26px var(--pad) 22px}
.foot-row{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px 36px}
.foot-row .logo{font-size:1.05rem}
.foot-row .logo i{border-color:var(--paper)}
.foot-info{display:flex;flex-wrap:wrap;gap:6px 28px;font-size:.74rem;opacity:.8}
.foot-copy{margin-top:16px;padding-top:14px;border-top:1px solid rgba(244,237,224,.22);font-size:.7rem;opacity:.6}

.toast{position:fixed;left:50%;bottom:28px;z-index:120;max-width:calc(100vw - 32px);padding:14px 20px;background:var(--ink);color:var(--paper);border-left:6px solid var(--red);font-size:.95rem;translate:-50% 30px;opacity:0;pointer-events:none;transition:.35s var(--ease)}
.toast.is-on{translate:-50% 0;opacity:1}

/* layar "tiket jadi" */
.takeover{position:fixed;inset:0;z-index:50;overflow-y:auto;background:var(--red);color:var(--paper);animation:tirai .5s var(--ease) both}
@keyframes tirai{from{clip-path:inset(100% 0 0 0)}to{clip-path:inset(0)}}
.takeover-inner{max-width:940px;margin:0 auto;padding:clamp(32px,6vw,72px) var(--pad) 64px}
.kicker-light{font-size:.8rem;text-transform:uppercase;letter-spacing:.12em}
.takeover h2{margin:12px 0 30px;font-size:clamp(2.4rem,6.5vw,4.6rem);line-height:.95;font-weight:800;letter-spacing:-.05em}
.takeover h2 span{color:var(--mustard)}
.stubs{display:grid;gap:28px}
.stub{display:flex;background:var(--paper-3);color:var(--ink);border:var(--line);box-shadow:7px 7px 0 var(--ink);animation:rise .7s var(--ease) both;animation-delay:calc(var(--i,0)*120ms + 350ms)}
.stub:nth-child(odd){rotate:-.5deg}
.stub:nth-child(even){rotate:.4deg}
.stub-main{flex:1;display:flex;gap:22px;padding:22px 24px;min-width:0}
.stub-poster{flex:none;width:84px;aspect-ratio:3/4;border:var(--line);align-self:center}
.stub-poster svg{display:block;width:100%;height:100%}
.stub-info{min-width:0}
.stub-info .mono{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;opacity:.65}
.stub-info h3{margin:4px 0 12px;font-size:1.6rem;line-height:1.05;font-weight:800;letter-spacing:-.035em}
.stub-info dl{display:grid;grid-template-columns:repeat(3,auto);gap:8px 30px;justify-content:start}
.stub-info dl .wide{grid-column:1/-1}
.stub-info dt{font-family:var(--mono);font-size:.64rem;text-transform:uppercase;letter-spacing:.1em;opacity:.6}
.stub-info dd{font-weight:600;overflow-wrap:anywhere}
.stub-cut{position:relative;flex:none;width:26px;margin:-2px 0;
  background:radial-gradient(circle at 50% 0,var(--red) 0 11px,var(--ink) 11px 13px,transparent 13px),
             radial-gradient(circle at 50% 100%,var(--red) 0 11px,var(--ink) 11px 13px,transparent 13px)}
.stub-cut::before{content:"";position:absolute;top:20px;bottom:20px;left:50%;border-left:2px dashed var(--ink)}
.stub-side{flex:none;width:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:18px 16px;background:var(--mustard)}
.stub-side .mono{font-size:.68rem;letter-spacing:.1em}
.kursi-list{display:flex;flex-wrap:wrap;justify-content:center;gap:4px 12px;line-height:1;font-weight:800;letter-spacing:-.04em}
.kursi-list.k1{font-size:3rem}
.kursi-list.k2{font-size:2.1rem}
.kursi-list.k3{font-size:1.5rem}
.barcode{width:100%;height:34px;fill:var(--ink)}
.takeover-foot{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;margin-top:44px}
.takeover-foot .mono{font-size:.95rem}

@media(max-width:960px){
  .ticket-card{grid-template-columns:minmax(0,1fr);max-width:560px}
  .tc-perf{height:26px;margin:0 -2px;
    background:radial-gradient(circle at 0 50%,var(--paper-2) 0 11px,var(--ink) 11px 13px,transparent 13px),
               radial-gradient(circle at 100% 50%,var(--paper-2) 0 11px,var(--ink) 11px 13px,transparent 13px),
               linear-gradient(var(--mustard) 50%,var(--paper-3) 50%)}
  .tc-perf::before{top:50%;bottom:auto;left:20px;right:20px;border-left:0;border-top:2px dashed var(--ink)}
}
@media(max-width:640px){
  .bar-note{display:none}
  .badge{position:static;display:block;margin:36px 0 0;width:120px}
  .film-head{flex-direction:column;align-items:flex-start}
  .day-label{width:100%}
  .seats,.seat-row{gap:7px}
  .poster-grid{grid-template-columns:minmax(0,330px)}
  .stub{flex-direction:column}
  .stub-main{padding:18px}
  .stub-info dl{grid-template-columns:repeat(2,auto)}
  .stub-cut{width:auto;height:26px;margin:0 -2px;
    background:radial-gradient(circle at 0 50%,var(--red) 0 11px,var(--ink) 11px 13px,transparent 13px),
               radial-gradient(circle at 100% 50%,var(--red) 0 11px,var(--ink) 11px 13px,transparent 13px)}
  .stub-cut::before{top:50%;bottom:auto;left:20px;right:20px;border-left:0;border-top:2px dashed var(--ink)}
  .stub-side{width:auto;flex-direction:row;justify-content:space-between}
  .barcode{width:110px}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
  .scribble path{stroke-dashoffset:0}
  html{scroll-behavior:auto}
}
</style>
</head>
<body>

<!-- filter grain (efek cetak risograph) dipakai ulang oleh semua poster -->
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
  </defs>
</svg>

<header class="bar">
  <a class="logo" href="#/" aria-label="{{NAMA}}"><i></i><b>{{DEPAN}}</b><span>{{BELAKANG}}</span></a>
  <p class="bar-note mono">Studio 1–4 · Buka 10.00–23.00</p>
</header>

<main id="top">
  <!-- HALAMAN 1: beranda + pilih film -->
  <div id="halamanFilm">
  <section class="hero">
    <p class="kicker mono rise" style="--i:0"><span class="live"></span> Sedang tayang · <span id="jumlahFilm">4</span> film</p>
    <h1 class="rise" style="--i:1">Hari ini<br>mau
      <em>nonton<svg class="scribble" viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path d="M3 12 C 60 3, 120 19, 180 9 S 270 6, 297 11" pathLength="1"/></svg></em>
      apa?</h1>
    <p class="lead rise" style="--i:2"><span class="l1">Pilih film, jadwal film, kursi favorit, dan dapatkan e-ticket secara instan.</span><span>Tanpa antre, tanpa ribet.</span></p>
    <svg class="badge rise" style="--i:3" viewBox="0 0 120 120" aria-label="E-ticket instan" role="img">
      <circle cx="60" cy="60" r="58" fill="#F0B429" stroke="#1B1A17" stroke-width="2"/>
      <g class="badge-ring">
        <path id="lingkar" d="M60 60 m-44 0 a44 44 0 1 1 88 0 a44 44 0 1 1 -88 0" fill="none"/>
        <text font-size="9" letter-spacing="1" fill="#1B1A17" style="font-family:var(--mono);font-weight:500">
          <textPath href="#lingkar" textLength="270" lengthAdjust="spacing">E-TICKET INSTAN • KURSI PILIHANMU • </textPath>
        </text>
      </g>
      <g transform="translate(60 60) rotate(-12)">
        <path d="M-22 -13 H22 V-5 A5 5 0 0 0 22 5 V13 H-22 V5 A5 5 0 0 0 -22 -5 Z" fill="#E4472B" stroke="#1B1A17" stroke-width="2.4" stroke-linejoin="round"/>
        <path d="M-5 -10 V10" stroke="#1B1A17" stroke-width="2" stroke-dasharray="3 3"/>
      </g>
    </svg>
  </section>

  <section class="films" id="films">
    <h2 class="sec-title"><span class="num mono">01</span> Pilih film</h2>
    <div class="poster-grid" id="posterGrid"></div>
  </section>

  </div>

  <!-- HALAMAN 2: jam tayang, kursi, dan e-ticket (alamat #/pesan/<kode film>) -->
  <section class="booking" id="booking" hidden>
    <a class="back mono" href="#/">← Ganti film</a>
    <h2 class="sec-title"><span class="num mono">02</span> Atur jam &amp; kursi</h2>
    <div class="film-head" id="filmHead"></div>

    <div class="pick-grid">
      <div class="block">
        <h3 class="block-title">Jam tayang</h3>
        <div class="showtimes" id="showtimes"></div>
      </div>
      <div class="block pick-seat">
        <h3 class="block-title">Pilih kursi <span class="hint mono" id="seatHint"></span></h3>
        <div class="hall">
          <div class="screen"><span class="mono">LAYAR</span></div>
          <div class="seats" id="seats"></div>
          <ul class="legend mono">
            <li><i class="sw sw-free"></i> Kosong</li>
            <li><i class="sw sw-pick"></i> Pilihanmu</li>
            <li><i class="sw sw-taken"></i> Terisi</li>
          </ul>
        </div>
      </div>

      <!-- kartu tiket di bawah denah kursi -->
      <form class="ticket-card" id="form" novalidate>
      <div class="tc-left">
        <p class="mono tc-label">E-ticket</p>
        <h3 id="tcFilm">—</h3>
        <p class="mono tc-when" id="tcWhen"></p>
        <div class="tc-seats" id="tcSeats"></div>
        <dl class="tc-price" id="tcPrice"></dl>
      </div>
      <div class="tc-perf" aria-hidden="true"></div>
      <div class="tc-body">
        <label class="field"><span class="mono">Kirim e-ticket ke</span>
          <input id="email" type="email" autocomplete="email" inputmode="email" placeholder="nama@email.com" maxlength="60"></label>

        <fieldset class="pay">
          <legend class="mono">Bayar dengan</legend>
          <div class="pay-opts" id="metode"></div>
        </fieldset>

        <label class="check" id="usiaWrap" hidden>
          <input type="checkbox" id="usia"><i aria-hidden="true"></i><span id="usiaTeks"></span>
        </label>

        <p class="tc-note" id="tcNote" aria-live="polite"></p>
        <button class="btn" id="btnPesan" type="submit" disabled>Pesan tiket</button>
      </div>
      </form>
    </div>
  </section>
</main>

<footer class="foot">
  <div class="foot-row">
    <a class="logo" href="#/" aria-label="{{NAMA}}"><i></i><b>{{DEPAN}}</b><span>{{BELAKANG}}</span></a>
    <div class="foot-info mono">
      <span>Setiap hari 10.00–23.00</span>
      <span>4 studio</span>
      <span>Loket bantuan di lobi lantai 1</span>
    </div>
  </div>
  <p class="foot-copy mono">© <span id="tahun">2026</span> {{NAMA}} · E-ticket berlaku untuk satu kali masuk</p>
</footer>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<div class="takeover" id="takeover" hidden role="dialog" aria-modal="true" aria-labelledby="toJudul">
  <div class="takeover-inner">
    <p class="mono kicker-light">Pembayaran berhasil</p>
    <h2 id="toJudul">Tiketmu sudah <span>siap.</span></h2>
    <div class="stubs" id="stubs"></div>
    <div class="takeover-foot">
      <p class="mono" id="toTotal"></p>
      <button class="btn btn-light" id="btnSelesai" type="button">Selesai</button>
    </div>
  </div>
</div>

<script>
const $ = (sel, el = document) => el.querySelector(sel);
const rupiah = (n) => 'Rp' + Number(n).toLocaleString('id-ID');
const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const RE_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const state = { data: null, filmId: null, jadwalId: null, kursi: new Set(), metode: null, token: 0, mengirim: false };

/* Tanggal */
const tglPendek = (iso) => new Date(iso + 'T00:00:00').toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
function labelHari(j) {
  const beda = Math.round((new Date(j.tanggal + 'T00:00:00') - new Date(state.data.hari_ini + 'T00:00:00')) / 864e5);
  return beda === 0 ? 'Hari ini' : beda === 1 ? 'Besok' : j.hari;
}

/* Poster: ilustrasi vektor bergaya cetak riso */
const C = { paper: '#F4EDE0', ink: '#1B1A17', red: '#E4472B', mustard: '#F0B429', teal: '#1F6F6B' };
const TEMA = {
  f1: {
    bg: C.mustard, teks: C.paper, aksen: C.mustard,
    baris: ['PETUALANGAN', 'NUSANTARA'], fs: 36, ty: 336, lh: 33,
    gambar: () => `
      <circle cx="205" cy="118" r="68" fill="${C.red}"/>
      <path d="M0 250 L88 128 L158 218 L212 156 L300 262 V400 H0Z" fill="${C.teal}"/>
      <path d="M0 300 L72 214 L142 290 L222 200 L300 300 V400 H0Z" fill="${C.ink}"/>
      <path d="M42 62 q8 -9 16 0 q8 -9 16 0 M92 40 q6 -7 12 0 q6 -7 12 0" fill="none" stroke="${C.ink}" stroke-width="3" stroke-linecap="round"/>`,
  },
  f2: {
    bg: C.ink, teks: C.paper, aksen: C.mustard,
    baris: ['MISTERI', 'RUMAH', 'TUA'], fs: 32, ty: 324, lh: 30,
    gambar: () => `
      <circle cx="208" cy="104" r="58" fill="${C.paper}"/>
      <circle cx="190" cy="92" r="9" fill="#DDD2BA"/><circle cx="226" cy="122" r="6" fill="#DDD2BA"/><circle cx="224" cy="80" r="4" fill="#DDD2BA"/>
      <path d="M0 168 H300 M0 184 H300 M0 200 H300" stroke="${C.teal}" stroke-width="5" opacity=".55"/>
      <path d="M52 222 L118 160 L184 222Z" fill="${C.red}"/>
      <rect x="68" y="222" width="100" height="66" fill="${C.teal}"/>
      <rect x="84" y="238" width="20" height="26" fill="${C.mustard}"/>
      <rect x="132" y="238" width="20" height="26" fill="${C.ink}" stroke="${C.paper}" stroke-width="2"/>
      <path d="M0 288 H300" stroke="${C.paper}" stroke-width="3"/>`,
  },
  f3: {
    bg: C.teal, teks: C.paper, aksen: C.mustard,
    baris: ['CINTA DI', 'KOTA', 'HUJAN'], fs: 32, ty: 326, lh: 30,
    gambar: () => {
      let hujan = '';
      for (let i = 0; i < 28; i++) { hujan += `M${(i * 13 + (i % 3) * 5) % 320} ${(i * 47) % 230} l-10 30 `; }
      const jendela = [[44, 256], [92, 262], [124, 270], [200, 250], [210, 266], [270, 258]]
        .map(([x, y]) => `<rect x="${x}" y="${y}" width="8" height="8"/>`).join('');
      return `
        <path d="${hujan}" stroke="${C.paper}" stroke-width="2" stroke-linecap="round" opacity=".38"/>
        <path d="M62 160 A88 88 0 0 1 238 160 Q216 142 194 160 Q172 142 150 160 Q128 142 106 160 Q84 142 62 160Z" fill="${C.red}" stroke="${C.ink}" stroke-width="3"/>
        <path d="M150 160 V238 q0 20 -20 20" fill="none" stroke="${C.ink}" stroke-width="6" stroke-linecap="round"/>
        <path d="M150 72 v-12" stroke="${C.ink}" stroke-width="6" stroke-linecap="round"/>
        <path d="M0 300 V270 H34 V246 H70 V280 H104 V256 H146 V284 H188 V240 H228 V274 H262 V252 H300 V300Z" fill="${C.ink}"/>
        <rect y="298" width="300" height="102" fill="${C.ink}"/>
        <g fill="${C.mustard}">${jendela}</g>`;
    },
  },
  f4: {
    bg: C.red, teks: C.paper, aksen: C.mustard,
    baris: ['GOL DI', 'MENIT', 'TERAKHIR'], fs: 32, ty: 326, lh: 30,
    gambar: () => {
      const t = (v) => v.toFixed(1);
      let sinar = '';
      for (let i = 0; i < 14; i++) {
        const a1 = (i * 2 * Math.PI) / 14, a2 = a1 + Math.PI / 14;
        const p = (a) => `${t(150 + 320 * Math.cos(a))} ${t(150 + 320 * Math.sin(a))}`;
        sinar += `<path d="M150 150 L${p(a1)} L${p(a2)}Z"/>`;
      }
      const titik = [], garis = [];
      for (let i = 0; i < 5; i++) {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
        titik.push(`${t(150 + 24 * Math.cos(a))},${t(150 + 24 * Math.sin(a))}`);
        garis.push(`M${t(150 + 24 * Math.cos(a))} ${t(150 + 24 * Math.sin(a))} L${t(150 + 70 * Math.cos(a))} ${t(150 + 70 * Math.sin(a))}`);
      }
      return `
        <g fill="${C.mustard}" opacity=".4">${sinar}</g>
        <circle cx="150" cy="150" r="70" fill="${C.paper}" stroke="${C.ink}" stroke-width="4"/>
        <path d="${garis.join(' ')}" stroke="${C.ink}" stroke-width="3" stroke-linecap="round"/>
        <polygon points="${titik.join(' ')}" fill="${C.ink}"/>
        <rect y="298" width="300" height="102" fill="${C.ink}"/>
        <rect y="284" width="300" height="14" fill="${C.teal}"/>
        <path d="M0 291 H300" stroke="${C.paper}" stroke-width="2" stroke-dasharray="14 10"/>`;
    },
  },
};

function posterSVG(id, { judul = true } = {}) {
  const t = TEMA[id] || TEMA.f1;
  const teks = judul ? t.baris.map((b, i) => `
      <text x="20" y="${t.ty + i * t.lh}" font-size="${t.fs}" font-weight="800" letter-spacing="-1.5"
            fill="${i === t.baris.length - 1 ? t.aksen : t.teks}" style="font-family:var(--font)">${b}</text>`).join('') : '';
  return `<svg viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Poster film">
    <rect width="300" height="400" fill="${t.bg}"/>${t.gambar()}${teks}
    <rect width="300" height="400" filter="url(#grain)" opacity=".3" style="mix-blend-mode:multiply"/></svg>`;
}

/* API (semua hitungan & validasi ada di class Python) */
async function api(path, body) {
  const res = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Terjadi kesalahan');
  return json;
}
const muatData = async () => { state.data = await api('/api/data'); };

let timerToast;
function toast(pesan) {
  const el = $('#toast');
  el.textContent = pesan;
  el.classList.add('is-on');
  clearTimeout(timerToast);
  timerToast = setTimeout(() => el.classList.remove('is-on'), 3800);
}

const filmAktif = () => state.data.films.find((f) => f.id === state.filmId);
const jadwalAktif = () => state.data.jadwal.find((j) => j.id === state.jadwalId);
const bisaDipesan = (j) => j.sisa > 0 && !j.lewat;

/* Daftar film */
function renderFilm() {
  const grid = $('#posterGrid');
  grid.innerHTML = '';
  $('#jumlahFilm').textContent = state.data.films.length;
  state.data.films.forEach((f, i) => {
    const termurah = Math.min(...state.data.jadwal.filter((j) => j.film_id === f.id).map((j) => j.harga));
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'poster' + (f.id === state.filmId ? ' is-active' : '');
    btn.style.setProperty('--i', i);
    btn.innerHTML = `
      <div class="poster-art">${posterSVG(f.id)}
        ${f.usia_min ? `<span class="age" title="Usia minimal ${f.usia_min} tahun">${f.usia_min}+</span>` : ''}
        <span class="chosen mono">Dipilih</span></div>
      <h3>${esc(f.judul)}</h3>
      <p class="meta mono">${esc(f.genre)} · ${f.durasi} mnt</p>
      <p class="from">Mulai <b>${rupiah(termurah)}</b></p>`;
    btn.addEventListener('click', () => { location.hash = '#/pesan/' + f.id; });   // pindah ke halaman 2
    grid.append(btn);
  });
}

/* Dua halaman: beranda (#/) dan pesan tiket (#/pesan/<film>) */
function bukaHalamanPesan(id) {
  state.filmId = id;
  state.kursi.clear();
  $('#usia').checked = false;
  const daftar = state.data.jadwal.filter((j) => j.film_id === id);
  state.jadwalId = (daftar.find(bisaDipesan) || daftar[0]).id;

  $('#halamanFilm').hidden = true;
  const halaman = $('#booking');
  halaman.hidden = false;
  halaman.style.animation = 'none'; void halaman.offsetWidth; halaman.style.animation = '';   // ulang animasi masuk

  renderHeadFilm(); renderJadwal(); renderKursi(); perbaruiRingkasan();
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function bukaBeranda() {
  state.filmId = null;
  state.kursi.clear();
  $('#booking').hidden = true;
  $('#halamanFilm').hidden = false;
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function router() {
  const cocok = location.hash.match(/^#\/pesan\/([\w-]+)/);
  const film = cocok && state.data.films.find((f) => f.id === cocok[1]);
  if (film) bukaHalamanPesan(film.id);
  else bukaBeranda();
}

function renderHeadFilm() {
  const f = filmAktif();
  $('#filmHead').innerHTML = `
    <div class="thumb">${posterSVG(f.id, { judul: false })}</div>
    <div><h3>${esc(f.judul)}</h3><p class="tagline">“${esc(f.tagline)}”</p>
      <div class="pills mono"><span class="pill">${esc(f.genre)}</span><span class="pill">${f.durasi} menit</span>
        ${f.usia_min ? `<span class="pill age-pill">Usia ${f.usia_min}+</span>` : '<span class="pill">Semua umur</span>'}</div></div>`;
}

/* Jam tayang */
function renderJadwal() {
  const wadah = $('#showtimes');
  wadah.innerHTML = '';
  const perTanggal = new Map();
  state.data.jadwal.filter((j) => j.film_id === state.filmId).forEach((j) => {
    if (!perTanggal.has(j.tanggal)) perTanggal.set(j.tanggal, []);
    perTanggal.get(j.tanggal).push(j);
  });
  perTanggal.forEach((daftar, tanggal) => {
    const baris = document.createElement('div');
    baris.className = 'day';
    baris.innerHTML = `<span class="day-label mono">${esc(labelHari(daftar[0]))}<small>${esc(daftar[0].hari)}, ${tglPendek(tanggal)}</small></span>`;
    daftar.forEach((j) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'show' + (j.id === state.jadwalId ? ' is-on' : '');
      b.disabled = !bisaDipesan(j);
      const ket = j.lewat ? 'sudah mulai' : j.sisa === 0 ? 'penuh' : 'sisa ' + j.sisa;
      b.innerHTML = `<b>${esc(j.jam)}</b><small>Studio ${j.studio} · ${ket}</small>`;
      b.addEventListener('click', () => {
        state.jadwalId = j.id; state.kursi.clear();
        renderJadwal(); renderKursi(); perbaruiRingkasan();
      });
      baris.append(b);
    });
    wadah.append(baris);
  });
}

/* Denah kursi */
function renderKursi() {
  const j = jadwalAktif();
  const { baris, kolom } = state.data.denah;
  const separuh = Math.ceil(kolom / 2);
  const wadah = $('#seats');
  wadah.innerHTML = '';
  const kolomCss = `26px repeat(${separuh}, 1fr) 18px repeat(${kolom - separuh}, 1fr)`;
  for (const b of baris) {
    const row = document.createElement('div');
    row.className = 'seat-row';
    row.style.gridTemplateColumns = kolomCss;
    row.innerHTML = `<span class="row-label">${b}</span>`;
    for (let k = 1; k <= kolom; k++) {
      if (k === separuh + 1) row.insertAdjacentHTML('beforeend', '<span></span>');   // lorong
      const kode = `${b}${k}`;
      const terisi = j.terpesan.includes(kode) || j.lewat;
      const dipilih = state.kursi.has(kode);
      const s = document.createElement('button');
      s.type = 'button';
      s.className = 'seat' + (dipilih ? ' is-pick' : '');
      s.textContent = kode;
      s.disabled = terisi;
      s.setAttribute('aria-pressed', dipilih);
      s.setAttribute('aria-label', `Kursi ${kode}, ${terisi ? 'tidak tersedia' : dipilih ? 'dipilih' : 'kosong'}`);
      s.addEventListener('click', () => ubahKursi(kode));
      row.append(s);
    }
    wadah.append(row);
  }
  $('#seatHint').textContent = `sisa ${j.sisa} dari ${baris.length * kolom}`;
}

function ubahKursi(kode) {
  const maks = state.data.aturan.maks_kursi;
  if (state.kursi.has(kode)) state.kursi.delete(kode);
  else {
    if (state.kursi.size >= maks) return toast(`Maksimal ${maks} kursi per pemesanan.`);
    state.kursi.add(kode);
  }
  renderKursi(); perbaruiRingkasan();
}

/* Ringkasan tiket & harga */
async function perbaruiRingkasan() {
  const f = filmAktif(), j = jadwalAktif();
  const kursi = [...state.kursi].sort();
  $('#tcFilm').textContent = f.judul;
  $('#tcWhen').textContent = `${labelHari(j)} · ${j.jam} · Studio ${j.studio}`;
  $('#tcSeats').innerHTML = kursi.length
    ? kursi.map((k) => `<span class="seat-chip">${k}</span>`).join('')
    : '<span class="empty">Belum ada kursi. Ketuk kursi di denah.</span>';

  const token = ++state.token;
  let h = { satuan: j.harga, jumlah: 0, total: 0 };
  if (kursi.length) {
    try { h = await api('/api/harga', { id_jadwal: j.id, jumlah: kursi.length }); }
    catch (e) { toast(e.message); }
  }
  if (token !== state.token) return;    // ada pembaruan yang lebih baru

  $('#tcPrice').innerHTML = `
    <div class="total"><dt>Total<small>${kursi.length ? `${kursi.length} × ${rupiah(h.satuan)}` : ''}</small></dt><dd>${rupiah(h.total)}</dd></div>`;
  validasi();
}

function validasi() {
  const f = filmAktif(), j = jadwalAktif();
  const email = $('#email').value.trim();
  const n = state.kursi.size;
  const emailOk = RE_EMAIL.test(email);

  $('#usiaWrap').hidden = !f.usia_min;
  $('#usiaTeks').textContent = `Saya berusia ${f.usia_min} tahun atau lebih`;
  const usiaOk = !f.usia_min || $('#usia').checked;

  const note = $('#tcNote');
  note.className = 'tc-note';
  note.textContent = '';
  if (email && !emailOk) {
    note.textContent = 'Format email belum benar.';
    note.classList.add('is-bad');
  } else if (n > 0 && f.usia_min && !usiaOk) {
    note.textContent = `Film ini untuk usia ${f.usia_min}+. Centang konfirmasi usia.`;
  } else if (j.akhir_pekan) {
    note.textContent = `Tarif akhir pekan berlaku (+${rupiah(state.data.aturan.tambahan_akhir_pekan)} per tiket).`;
  }
  $('#btnPesan').disabled = state.mengirim || !(n > 0 && emailOk && state.metode && usiaOk);
}

function renderMetode() {
  const wadah = $('#metode');
  state.metode = state.data.aturan.metode_bayar[0];
  wadah.innerHTML = state.data.aturan.metode_bayar.map((m, i) => `
    <label class="pay-opt"><input type="radio" name="metode" value="${esc(m)}" ${i === 0 ? 'checked' : ''}><span>${esc(m)}</span></label>`).join('');
  wadah.addEventListener('change', (e) => { state.metode = e.target.value; validasi(); });
}

/* Kirim pesanan */
async function kirimPesanan(e) {
  e.preventDefault();
  if ($('#btnPesan').disabled) return;
  state.mengirim = true;
  const tombol = $('#btnPesan');
  tombol.textContent = 'Memproses…';
  validasi();
  try {
    const hasil = await api('/api/pesan', {
      email: $('#email').value, metode: state.metode, usia_ok: $('#usia').checked,
      id_jadwal: state.jadwalId, kursi: [...state.kursi],
    });
    tampilkanTiket(hasil);
  } catch (err) {
    toast(err.message);
    await muatData();                        // segarkan kursi yang mungkin sudah diambil orang lain
    const j = jadwalAktif();
    state.kursi.forEach((k) => { if (j.terpesan.includes(k)) state.kursi.delete(k); });
    renderJadwal(); renderKursi(); perbaruiRingkasan();
  } finally {
    state.mengirim = false;
    tombol.textContent = 'Pesan tiket';
    validasi();
  }
}

/* Layar tiket jadi */
function barcode(seed) {
  let h = 7;
  for (const c of seed) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  let x = 0, batang = '';
  while (x < 108) {
    h = (h * 1664525 + 1013904223) >>> 0;
    const lebar = 1 + (h >>> 28) % 4, jeda = 1 + (h >>> 24) % 3;
    batang += `<rect x="${x}" y="0" width="${lebar}" height="40"/>`;
    x += lebar + jeda;
  }
  return `<svg class="barcode" viewBox="0 0 110 40" preserveAspectRatio="none" aria-hidden="true">${batang}</svg>`;
}

function tampilkanTiket(hasil) {
  // satu pesanan = satu tiket yang memuat semua kursi
  const t = hasil.tiket[0];
  const kursi = hasil.tiket.map((x) => x.kursi);
  const n = kursi.length;
  const kode = n > 1 ? `${t.kode}–${hasil.tiket[n - 1].kode}` : t.kode;
  $('#toTotal').textContent = `${n} tiket · total ${rupiah(hasil.total)}`;
  $('#stubs').innerHTML = `
    <article class="stub" style="--i:0">
      <div class="stub-main">
        <div class="stub-poster">${posterSVG(t.film_id, { judul: false })}</div>
        <div class="stub-info">
          <p class="mono">${esc(state.data.bioskop)} · E-ticket</p>
          <h3>${esc(t.film)}</h3>
          <dl>
            <div><dt>Tanggal</dt><dd>${esc(t.hari.slice(0, 3))}, ${tglPendek(t.tanggal)}</dd></div>
            <div><dt>Jam</dt><dd>${esc(t.jam)}</dd></div>
            <div><dt>Studio</dt><dd>${t.studio}</dd></div>
            <div><dt>Jumlah</dt><dd>${n} tiket</dd></div>
            <div><dt>Bayar</dt><dd>${esc(t.metode)}</dd></div>
            <div><dt>Total</dt><dd>${rupiah(hasil.total)}</dd></div>
            <div class="wide"><dt>Dikirim ke</dt><dd>${esc(t.email)}</dd></div>
          </dl>
        </div>
      </div>
      <div class="stub-cut" aria-hidden="true"></div>
      <div class="stub-side">
        <span class="mono">KURSI</span>
        <span class="kursi-list k${Math.min(n, 3)}">${kursi.map((k) => `<span>${esc(k)}</span>`).join('')}</span>
        ${barcode(t.kode)}<span class="mono">${esc(kode)}</span>
      </div>
    </article>`;
  const layar = $('#takeover');
  layar.hidden = false;
  layar.scrollTop = 0;
  document.body.style.overflow = 'hidden';
  $('#btnSelesai').focus();
}

async function tutupTiket() {
  $('#takeover').hidden = true;
  document.body.style.overflow = '';
  state.kursi.clear();
  $('#usia').checked = false;
  await muatData();                // sisa kursi di beranda ikut diperbarui
  renderFilm();
  if (location.hash === '#/') router(); else location.hash = '#/';   // kembali ke halaman 1
}

async function mulai() {
  $('#tahun').textContent = new Date().getFullYear();
  try { await muatData(); renderFilm(); }
  catch (e) {
    $('#posterGrid').innerHTML = '<p class="mono">Server belum berjalan. Jalankan <b>python bioskop.py</b> lalu muat ulang halaman.</p>';
    return;
  }
  renderMetode();
  $('#form').addEventListener('submit', kirimPesanan);
  $('#email').addEventListener('input', validasi);
  $('#usia').addEventListener('change', validasi);
  $('#btnSelesai').addEventListener('click', tutupTiket);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#takeover').hidden) tutupTiket(); });
  window.addEventListener('hashchange', router);
  router();                        // tampilkan halaman sesuai alamat saat ini
}
mulai();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()