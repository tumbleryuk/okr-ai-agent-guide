#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pemeriksa dan pengirim ajuan target kuartal (OKR) buat tim TumblerYuk.

Tiga cara pakai:

    python kirim_ajuan.py --cek-kunci
    python kirim_ajuan.py --cek   ajuan-nur.json --arah turun --nama-saya Nur
    python kirim_ajuan.py --kirim ajuan-nur.json --arah turun --nama-saya Nur

--cek jalan di komputer sendiri, nol nyentuh internet.
--kirim jalanin --cek dulu; kalau ada yang kurang, dia nolak ngirim.

Kunci dibaca dari variabel lingkungan OKR_KUNCI, atau berkas ~/.claude/okr-kunci.txt.
Kunci ga pernah dicetak ke layar dan ga pernah ditulis ke berkas mana pun.
Nol kunci beneran nempel di berkas ini.

Zero dependency, python polos.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

DASAR = "https://okr.tumbleryukoperasional.shop"
RUTE = DASAR + "/api/okr/ajuan"
RUTE_BACA = DASAR + "/api/okr/saya"

# Halaman OKR ada di balik pagar web. Pagar itu nolak 403 kalau pengirimnya ga
# nyebut identitas, dan python isi sendiri "Python-urllib/..." kalau baris ini
# ga dipasang. Jangan dihapus.
IDENTITAS = "TumblerYuk-OKR-Agent/1.0"

# Dua belas nama isian yang boleh dikirim, plus daftar baseline. Nol boleh nambah.
ISIAN_WAJIB = [
    "klaim",
    "jejak",
    "cara_baca",
    "ambang",
    "satuan",
    "jendela_mulai",
    "jendela_selesai",
    "jendela_min_data",
    "dipakein_siapa",
    "merah_kondisi",
    "penjaga_nama",
    "penjaga_ambang",
]
# Isian per langkah yang dikenal halaman OKR. Selain empat ini dibuang, nol dikirim.
# `judul` + `kata_kunci` WAJIB, `bobot` + `repo` boleh kosong.
LANGKAH_ISIAN = ["judul", "bobot", "repo", "kata_kunci"]
LANGKAH_ISIAN_WAJIB = ["judul", "kata_kunci"]

ISIAN_ANGKA = ["ambang", "jendela_min_data", "penjaga_ambang"]
ISIAN_TANGGAL = ["jendela_mulai", "jendela_selesai"]

BASELINE_MINIMAL = 6

WIB = timezone(timedelta(hours=7))

# Jawaban isian 7 yang ga boleh, karena ga nyebut nama orang.
DIPAKEIN_TERLARANG = [
    "tim", "semua orang", "semua", "semua tim", "kita",
    "orang lain", "siapa aja", "belum tau", "nanti",
]

# Kata yang nunjuk diri sendiri. Kalau nongol di isian 7, itu bukan nama orang lain.
KATA_DIRI = ["aku", "saya", "gua", "gue", "sendiri"]

# "Bukan aku" itu SAH, contoh panduan sendiri nulis "Rina dan Dwi. Bukan aku."
# Frasa penyangkalan dicopot dulu sebelum kata diri disapu, biar ga salah tuduh.
SANGKALAN = [
    "bukan diri sendiri", "bukan aku sendiri", "bukan saya sendiri",
    "bukan aku", "bukan saya", "bukan gua", "bukan gue", "bukan sendiri",
]


# ---------------------------------------------------------------- alat kecil


def ke_angka(nilai):
    """Ubah teks jadi angka. Nerima koma desimal Indonesia dan tanda persen."""
    teks = str(nilai).strip().replace("%", "").replace(" ", "")
    if not teks:
        return None
    if "," in teks and "." not in teks:
        teks = teks.replace(",", ".")
    else:
        teks = teks.replace(",", "")
    try:
        return float(teks)
    except ValueError:
        return None


def ke_tanggal(nilai):
    """Baca tanggal format 2026-08-01 (dibaca sebagai tanggal WIB). None kalau ngaco."""
    teks = str(nilai).strip()
    bagian = teks.split("-")
    if len(bagian) != 3:
        return None
    try:
        tahun, bulan, hari = (int(x) for x in bagian)
    except ValueError:
        return None
    if not (2000 <= tahun <= 2100 and 1 <= bulan <= 12 and 1 <= hari <= 31):
        return None
    return (tahun, bulan, hari)


def sisi_gagal(angka, ambang, arah):
    """True kalau angka ini jatuh di sisi GAGAL dari ambang.

    Pas angkanya sama persis sama ambang, itu dihitung LOLOS, sesuai panduan
    yang nulis "turun ke 20% atau kurang".
    """
    if arah == "turun":      # makin kecil makin bagus
        return angka > ambang
    return angka < ambang    # arah naik: makin besar makin bagus


def lebih_bagus_dari_ambang(angka, ambang, arah):
    """True cuma kalau angka ini BENERAN ngelewatin ambang, bukan pas nempel.

    Dipisah dari sisi_gagal sengaja. Pas rata-rata nempel persis di ambang,
    targetnya BELUM kecapai (masih butuh perbaikan biar aman), jadi jebakan 2
    ga boleh nyala di titik itu.
    """
    if arah == "turun":
        return angka < ambang
    return angka > ambang


def ada_kata_diri(jawaban):
    """True kalau isian 7 nunjuk diri sendiri. 'Bukan aku' ga kehitung."""
    polos = " " + jawaban.lower() + " "
    for frasa in SANGKALAN:
        polos = polos.replace(frasa, " ")
    kata = [k for k in "".join(c if c.isalpha() else " " for c in polos).split()]
    return any(k in KATA_DIRI for k in kata)


# ---------------------------------------------------------------------- kunci


def ambil_kunci():
    """Balikin (kunci, dari_mana). Nol ketemu balikin (None, None)."""
    kunci = os.environ.get("OKR_KUNCI", "").strip()
    if kunci:
        return kunci, "variabel lingkungan OKR_KUNCI"

    berkas = os.path.join(os.path.expanduser("~"), ".claude", "okr-kunci.txt")
    if os.path.isfile(berkas):
        try:
            with open(berkas, "r", encoding="utf-8") as f:
                kunci = f.read().strip()
        except OSError:
            kunci = ""
        if kunci:
            return kunci, "berkas " + berkas

    return None, None


def pesan_kunci_nol_ada():
    return (
        "[KURANG] Kuncimu belum kepasang.\n"
        "  Minta kunci ke Louis lewat chat pribadi, terus simpen di berkas\n"
        "  " + os.path.join(os.path.expanduser("~"), ".claude", "okr-kunci.txt") + "\n"
        "  Isinya cuma satu baris kunci itu doang. Jangan dikasih ke siapa pun."
    )


# ------------------------------------------------------------------ pemeriksa


def kuartal_dari(tanggal):
    """(tahun, bulan, hari) -> (tahun, nomor kuartal)."""
    return (tanggal[0], (tanggal[1] - 1) // 3 + 1)


def kuartal_teks(kuartal):
    return str(kuartal[0]) + "-Q" + str(kuartal[1])


def awal_kuartal(kuartal):
    return "%04d-%02d-01" % (kuartal[0], (kuartal[1] - 1) * 3 + 1)


def kuartal_berikut(kuartal):
    tahun, nomor = kuartal
    return (tahun + 1, 1) if nomor == 4 else (tahun, nomor + 1)


def hari_ini_wib():
    sekarang = datetime.now(WIB)
    return (sekarang.year, sekarang.month, sekarang.day)


def periksa(data, arah=None, nama_saya=None, hari_ini=None):
    """Balikin daftar masalah. Daftar kosong artinya lolos semua.

    `hari_ini` cuma buat uji; kosong = tanggal WIB sekarang.
    """
    masalah = []

    if not isinstance(data, dict):
        return ["Isi berkasnya bukan bentuk ajuan. Harusnya kurung kurawal berisi isian."]

    # 1. Isian wajib ada dan ga kosong
    for nama in ISIAN_WAJIB:
        if nama not in data:
            masalah.append("Isian '" + nama + "' belum ada di berkas.")
        elif not str(data[nama]).strip():
            masalah.append("Isian '" + nama + "' masih kosong.")

    # 2. Nol nama isian karangan
    boleh = set(ISIAN_WAJIB + ["baseline", "langkah"])
    for nama in data:
        if nama not in boleh:
            masalah.append(
                "Nama isian '" + nama + "' ga dikenal halaman OKR. "
                "Yang boleh cuma dua belas isian plus baseline dan langkah."
            )

    # 3. Isian yang harus berupa angka
    for nama in ISIAN_ANGKA:
        if nama in data and str(data[nama]).strip():
            if ke_angka(data[nama]) is None:
                masalah.append(
                    "Isian '" + nama + "' harus angka, sekarang isinya '"
                    + str(data[nama]) + "'."
                )

    # 4. Tanggal jendela
    tgl_mulai = tgl_selesai = None
    for nama in ISIAN_TANGGAL:
        if nama in data and str(data[nama]).strip():
            hasil = ke_tanggal(data[nama])
            if hasil is None:
                masalah.append(
                    "Tanggal '" + nama + "' formatnya harus 2026-08-01 (tahun-bulan-tanggal),"
                    " sekarang isinya '" + str(data[nama]) + "'."
                )
            elif nama == "jendela_mulai":
                tgl_mulai = hasil
            else:
                tgl_selesai = hasil
    if tgl_mulai and tgl_selesai and tgl_mulai >= tgl_selesai:
        masalah.append("Tanggal mulai jendela harus lebih awal dari tanggal selesai.")

    # 4b. Jendela wajib mulai di kuartal yang lagi jalan (atau kuartal depan).
    # Halaman OKR naruh ajuan di kuartal TANGGAL MULAI JENDELA, bukan di kuartal
    # hari kirim. Tanggal yang kesalin dari contoh lama bikin ajuan nyasar ke
    # kuartal yang udah lewat: diterima tanpa error, tapi nol muncul di papan.
    if tgl_mulai:
        sekarang = kuartal_dari(hari_ini or hari_ini_wib())
        kuartal_ajuan = kuartal_dari(tgl_mulai)
        if kuartal_ajuan not in (sekarang, kuartal_berikut(sekarang)):
            masalah.append(
                "Tanggal 'jendela_mulai' (" + str(data["jendela_mulai"]).strip() + ") jatuh di "
                "kuartal " + kuartal_teks(kuartal_ajuan) + ", padahal kuartal yang lagi jalan "
                + kuartal_teks(sekarang) + ". Halaman OKR naruh ajuan di kuartal tanggal mulai "
                "jendela, jadi ajuan ini bakal nyasar dan nol muncul di papan. Ganti ke tanggal "
                "di dalam kuartal ini, paling awal " + awal_kuartal(sekarang) + ". Tanggal di "
                "contoh panduan itu cuma contoh, jangan disalin."
            )

    # 5. Isian 7 bukan diri sendiri
    if str(data.get("dipakein_siapa", "")).strip():
        jawaban = str(data["dipakein_siapa"]).strip()
        polos = jawaban.lower().strip(" .!,")
        if polos in DIPAKEIN_TERLARANG:
            masalah.append(
                "Isian 'dipakein_siapa' isinya '" + jawaban + "'. Yang dibutuhin nama orang "
                "yang bakal make barangmu, dan orang itu bukan kamu."
            )
        elif ada_kata_diri(jawaban):
            masalah.append(
                "Isian 'dipakein_siapa' isinya '" + jawaban + "', itu masih nunjuk diri "
                "sendiri. Sebut nama orang lain yang kerjaannya bakal berubah gara-gara "
                "barangmu. Kalau belum ada orangnya, targetnya belum siap diajuin."
            )
        elif nama_saya and nama_saya.strip().lower() in polos.split():
            masalah.append(
                "Isian 'dipakein_siapa' nyebut namamu sendiri (" + nama_saya + "). "
                "Target yang cuma dipakai sendiri ga bisa dibuktiin ngebantu siapa-siapa. "
                "Sebut nama orang lain yang kerjaannya berubah."
            )

    # 6. Baseline: isian 4
    baseline = data.get("baseline")
    angka_baseline = []
    if not isinstance(baseline, list):
        masalah.append(
            "Isian 4 (angka sebelum) belum ada atau bentuknya salah. "
            "Harusnya daftar berisi tanggal_mulai dan angka tiap minggu."
        )
    else:
        if len(baseline) < BASELINE_MINIMAL:
            masalah.append(
                "Isian 4 baru " + str(len(baseline)) + " minggu. Halaman OKR minta paling "
                "sedikit " + str(BASELINE_MINIMAL) + " minggu. Contoh di panduan pakai 8."
            )
        tanggal_kepakai = set()
        for urut, baris in enumerate(baseline, start=1):
            label = "Baseline minggu ke-" + str(urut)
            if not isinstance(baris, dict):
                masalah.append(label + " bentuknya salah.")
                continue
            lebih = [k for k in baris if k not in ("tanggal_mulai", "angka")]
            if lebih:
                masalah.append(
                    label + " punya isian yang ga dikenal: " + ", ".join(lebih) + "."
                )
            tgl = ke_tanggal(baris.get("tanggal_mulai", ""))
            if tgl is None:
                masalah.append(
                    label + " tanggalnya kosong atau formatnya salah. "
                    "Pakai hari Senin minggu itu, format 2026-06-01."
                )
            else:
                if tgl in tanggal_kepakai:
                    masalah.append(label + " tanggalnya kembar sama minggu lain.")
                tanggal_kepakai.add(tgl)
                if tgl_mulai and tgl >= tgl_mulai:
                    masalah.append(
                        label + " tanggalnya di dalam jendela pengukuran. "
                        "Angka sebelum wajib dari sebelum kuartal mulai."
                    )
            nilai = ke_angka(baris.get("angka", ""))
            if nilai is None:
                masalah.append(label + " angkanya kosong atau bukan angka.")
            else:
                angka_baseline.append(nilai)

        if len(angka_baseline) >= 2 and len(set(angka_baseline)) == 1:
            masalah.append(
                "Semua angka mingguan di isian 4 nilainya sama persis. Itu tanda angkanya "
                "dikira-kira, bukan dihitung. Buka data lama, ambil angka tiap minggunya."
            )

    # 6b. Langkah pelaksanaan WAJIB, dan tiap langkah wajib kepakai.
    #
    # Halaman OKR nyocokin PR yang kelar ke langkah lewat `kata_kunci` -- langkah tanpa kata
    # kunci nol pernah kecocok, jadi persen kemajuan pengerjaanmu bakal mentok 0% sepanjang
    # kuartal walau kerjaanmu jalan. Itu sebabnya kata kunci diperlakuin sama wajibnya kayak
    # judul, bukan isian tambahan.
    langkah_mentah = data.get("langkah")
    if "langkah" not in data:
        masalah.append(
            "Isian 'langkah' belum ada di berkas. Wajib minimal satu langkah pelaksanaan: "
            "pekerjaan nyata yang bakal kamu kerjain buat ngejar targetnya."
        )
    elif not isinstance(langkah_mentah, list):
        masalah.append(
            "Isian 'langkah' harus berupa daftar (kurung siku berisi langkah), sekarang "
            "bentuknya beda."
        )
    elif not langkah_mentah:
        masalah.append(
            "Isian 'langkah' masih kosong. Wajib minimal satu langkah pelaksanaan."
        )
    else:
        for nomor, satu in enumerate(langkah_mentah, start=1):
            if not isinstance(satu, dict):
                masalah.append("Langkah ke-" + str(nomor) + " bentuknya bukan isian langkah.")
                continue
            for asing in satu:
                if asing not in LANGKAH_ISIAN:
                    masalah.append(
                        "Langkah ke-" + str(nomor) + " punya isian '" + str(asing)
                        + "' yang ga dikenal halaman OKR. Yang boleh cuma "
                        + ", ".join(LANGKAH_ISIAN) + "."
                    )
            judul_langkah = str(satu.get("judul") or "").strip()
            # Yang wajib dibaca dari `LANGKAH_ISIAN_WAJIB`, jangan diketik ulang di sini
            # -- kalau daftarnya berubah tapi pemeriksanya ketinggalan, alat ini bakal
            # ngelolosin ajuan yang ditolak halaman OKR, dan orangnya baru tau pas kirim.
            for wajib in LANGKAH_ISIAN_WAJIB:
                if str(satu.get(wajib) or "").strip():
                    continue
                if wajib == "judul":
                    masalah.append(
                        "Langkah ke-" + str(nomor) + " belum ada judulnya. Sebut pekerjaannya."
                    )
                elif wajib == "kata_kunci":
                    masalah.append(
                        "Langkah '" + (judul_langkah or "ke-" + str(nomor)) + "' belum ada "
                        "kata kuncinya. Kata kunci itu potongan judul PR yang bakal kamu bikin "
                        "(contoh: 'papan-pesanan'). Tanpa itu PR yang kelar nol pernah kehitung, "
                        "jadi persen kemajuanmu mentok 0% sampai kuartal habis."
                    )
                else:
                    # Isian wajib baru ditambahin ke daftar tapi belum ada penjelasannya di
                    # sini. Mending pesan seadanya daripada lolos diam-diam.
                    masalah.append(
                        "Langkah ke-" + str(nomor) + " belum ngisi '" + wajib + "', padahal wajib."
                    )

    # 7. Jebakan 1 dan 2, butuh arah
    ambang = ke_angka(data.get("ambang", ""))
    if arah is None:
        masalah.append(
            "CATATAN: arah angka belum disebut, jadi jebakan 1 (bisa merah ga) dan "
            "jebakan 2 (udah kecapai duluan) BELUM dicek. Tanya ke pemakai angkanya "
            "bagusnya naik atau turun, terus jalanin lagi pakai --arah."
        )
    elif ambang is not None and angka_baseline:
        gagal = [x for x in angka_baseline if sisi_gagal(x, ambang, arah)]
        if not gagal:
            masalah.append(
                "Jebakan 1 kena. Nol minggu di isian 4 yang jatuh di sisi gagal dari ambang "
                + str(data.get("ambang")) + ". Ukuran yang ga mungkin merah itu bukan "
                "timbangan, itu stiker. Naikin ambangnya atau ganti ukurannya."
            )
        rata = sum(angka_baseline) / len(angka_baseline)
        if lebih_bagus_dari_ambang(rata, ambang, arah):
            masalah.append(
                "Jebakan 2 kena. Rata-rata angka sebelum (" + ("%.2f" % rata).rstrip("0").rstrip(".")
                + ") udah lebih bagus dari ambang " + str(data.get("ambang"))
                + ". Targetnya udah lewat sebelum kuartal mulai, ambangnya harus dinaikin."
            )

    return masalah


def badan_permintaan(data):
    """Rakit badan permintaan. Semua nilai jadi teks, sesuai kontrak halaman OKR."""
    badan = {}
    for nama in ISIAN_WAJIB:
        badan[nama] = str(data.get(nama, "")).strip()
    badan["baseline"] = [
        {
            "tanggal_mulai": str(baris.get("tanggal_mulai", "")).strip(),
            "angka": str(baris.get("angka", "")).strip(),
        }
        for baris in data.get("baseline", [])
        if isinstance(baris, dict)
    ]
    # Langkahnya ikut kekirim. Sebelum tambalan ini `badan_permintaan` cuma mungut
    # `ISIAN_WAJIB` + `baseline`, jadi langkah yang udah diketik orang DIBUANG diam-diam dan
    # nol pernah nyampe server -- itu sebabnya ada ajuan yang persennya 0% sepanjang kuartal.
    badan["langkah"] = [
        {nama: str(satu.get(nama, "")).strip() for nama in LANGKAH_ISIAN}
        for satu in data.get("langkah", [])
        if isinstance(satu, dict)
    ]
    return badan


# -------------------------------------------------------------------- ngirim


def cek_kunci():
    """Cek kunci ke halaman OKR beneran, bukan cuma ngintip berkas di komputer.

    Ngintip berkas doang ga cukup: kunci yang udah dicabut tetap kelihatan
    "kepasang" padahal halaman OKR nolak dia. Jadi kunci itu dipakai sekali buat
    baca punya sendiri, yang ga ngubah apa pun.
    """
    kunci, dari_mana = ambil_kunci()
    if not kunci:
        print(pesan_kunci_nol_ada())
        return 2

    print("Kunci kebaca dari " + dari_mana + ". Nilainya ga ditampilkan.")
    print("Nanya ke halaman OKR, bentar...")

    permintaan = urllib.request.Request(
        RUTE_BACA,
        method="GET",
        headers={
            "Authorization": "Bearer " + kunci,
            "User-Agent": IDENTITAS,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(permintaan, timeout=25) as balasan:
            kode, mentah = balasan.status, balasan.read()
    except urllib.error.HTTPError as e:
        kode, mentah = e.code, e.read()
    except Exception:
        # Sambungan gagal itu BEDA sama kunci ditolak. Jangan sampai kebaca
        # "kuncimu salah" cuma gara-gara wifi lagi mati.
        print(
            "[BELUM KEJAWAB] Halaman OKR-nya ga kejangkau dari komputer ini.\n"
            "  Ini bukan berarti kuncimu salah. Cek sambungan internet, terus coba lagi.\n"
            "  Kalau terus begini, kabarin Louis."
        )
        return 3

    if kode == 200:
        try:
            isi = json.loads(mentah.decode("utf-8"))
        except Exception:
            isi = {}
        nama = (isi.get("pemilik") or {}).get("nama")
        print("[OK] Kuncimu hidup dan dikenali halaman OKR.")
        if nama:
            print("     Kunci ini kedaftar atas nama: " + str(nama) + ".")
            print("     Kalau nama itu bukan kamu, STOP, langsung kabarin Louis.")
        return 0

    if kode == 401:
        print(
            "[KUNCI GA SAH] Kuncimu ga dikenali halaman OKR. Mungkin udah diganti.\n"
            "  Minta kunci baru ke Louis lewat chat pribadi. Jangan nyoba kunci temen."
        )
        return 2

    if kode == 403:
        print(
            "[DITOLAK PAGAR WEB] Ditahan di gerbang, kuncimu belum sempat dicek.\n"
            "  Biasanya artinya alat ini versi lama. Ambil versi terbaru dari halaman\n"
            "  panduan, atau kabarin Louis sambil sebutin kode 403."
        )
        return 3

    if kode >= 500:
        print(
            "[HALAMAN OKR LAGI NGADAT] Kode " + str(kode) + ". Ini bukan soal kuncimu.\n"
            "  Tunggu sebentar terus coba lagi. Masih gagal juga? Kabarin Louis."
        )
        return 4

    print(
        "[BELUM KEJAWAB] Halaman OKR mbalikin kode " + str(kode) + " yang ga dikenal alat ini.\n"
        "  Kabarin Louis sambil sebutin kode itu."
    )
    return 3


def nomor_kirim(path_ajuan, isi):
    """Balikin nomor pengiriman buat isi kiriman ini.

    Nomornya disimpen di berkas pendamping bareng sidik isi kirimannya. Kalau
    pengirimannya diulang dengan isi SAMA (sambungan putus), nomor yang sama
    kepakai lagi, jadi halaman OKR tau itu kiriman yang sama dan ga nyimpen dua
    kali. Kalau isinya BERUBAH (berkas diedit lalu dikirim lagi), nomornya
    dibikin baru. Nomor lama yang dipakai buat isi beda bakal ditolak 409.
    """
    pendamping = str(path_ajuan) + ".nomor-kirim"
    sidik = hashlib.sha256(isi).hexdigest()
    try:
        if os.path.isfile(pendamping):
            with open(pendamping, "r", encoding="utf-8") as f:
                bagian = f.read().split()
            if len(bagian) == 2 and bagian[0] == sidik:
                return bagian[1]
    except OSError:
        pass

    baru = str(uuid.uuid4())
    try:
        with open(pendamping, "w", encoding="utf-8") as f:
            f.write(sidik + " " + baru)
    except OSError:
        pass
    return baru


def kirim(data, path_ajuan):
    """Kirim ajuan. Balikin kode keluar buat shell."""
    kunci, dari_mana = ambil_kunci()
    if not kunci:
        print(pesan_kunci_nol_ada())
        return 2
    print("Kunci kebaca dari " + dari_mana + ". Nilainya ga ditampilkan.")

    isi = json.dumps(badan_permintaan(data), ensure_ascii=False).encode("utf-8")
    permintaan = urllib.request.Request(
        RUTE,
        data=isi,
        method="POST",
        headers={
            "Authorization": "Bearer " + kunci,
            "Content-Type": "application/json",
            "User-Agent": IDENTITAS,
            "Idempotency-Key": nomor_kirim(path_ajuan, isi),
        },
    )

    try:
        with urllib.request.urlopen(permintaan, timeout=25) as balasan:
            return baca_balasan(balasan.status, balasan.read())
    except urllib.error.HTTPError as e:
        return baca_balasan(e.code, e.read())
    except urllib.error.URLError:
        print(
            "[BELUM BISA DIKIRIM] Halaman pengajuannya kelihatannya belum dibuka.\n"
            "  Berkas ajuanmu udah kesimpen rapi di komputer, ga ada yang hilang.\n"
            "  Tinggal dikirim lagi begitu Louis ngabarin halamannya siap dipakai."
        )
        return 3
    except Exception:
        print(
            "[BELUM BISA DIKIRIM] Sambungannya ga jalan. Berkas ajuanmu tetap aman di\n"
            "  komputer. Coba lagi nanti, atau kabarin Louis kalau terus begini."
        )
        return 3


def baca_balasan(kode, isi_mentah):
    try:
        isi = json.loads(isi_mentah.decode("utf-8"))
    except Exception:
        isi = {}

    if kode == 201:
        nomor = isi.get("ajuan_id", "?")
        print(
            "[KESIMPEN] Ajuanmu masuk. Nomornya " + str(nomor) + ".\n"
            "  Simpen nomor itu buat nanya perkembangan. Sekarang tinggal nunggu\n"
            "  laporan penilaian."
        )
        return 0

    if kode == 400:
        print("[ADA YANG SALAH ISI] Halaman OKR mbalikin ajuanmu. Alasannya:")
        for alasan in isi.get("penolakan", []) or ["(alasannya ga kebaca)"]:
            print("  - " + str(alasan))
        print(
            "  Ini cuma benerin isian, bukan penolakan penilaian. Ga makan jatah\n"
            "  ngajuin ulang. Benerin dulu, terus kirim lagi."
        )
        return 1

    if kode == 401:
        print(
            "[KUNCI GA SAH] Kuncimu ga dikenali halaman OKR.\n"
            "  Hubungi Louis lewat chat pribadi buat minta kunci baru.\n"
            "  Jangan nyoba kunci lain dan jangan kirim ulang berkali-kali."
        )
        return 2

    if kode == 403:
        print(
            "[DITOLAK PAGAR WEB] Kiriman kamu ditahan di gerbang, sebelum kuncimu sempat\n"
            "  dicek. Ini bukan salah kuncimu dan bukan salah isian kamu.\n"
            "  Biasanya artinya alat ini versi lama. Ambil versi terbaru dari halaman\n"
            "  panduan yang Louis kasih, atau kabarin Louis sambil sebutin kode 403."
        )
        return 3

    if kode == 409:
        print(
            "[AKUN BELUM KEDAFTAR ATAU KIRIMAN DOBEL] Halaman OKR nolak dengan kode 409.\n"
            "  Bisa berarti namamu belum didaftarin, atau kiriman yang sama masih jalan.\n"
            "  Jangan ngirim ulang berkali-kali. Kabarin Louis dulu."
        )
        return 2

    if kode >= 500:
        print(
            "[HALAMAN OKR LAGI NGADAT] Kode " + str(kode) + ". Belum ketahuan ajuanmu masuk atau\n"
            "  nggak, dan itu WAJAR. Jangan nebak, jangan ngedit berkasnya.\n"
            "  Jalanin ulang perintah yang PERSIS SAMA. Nomor kirimannya otomatis dipakai lagi,\n"
            "  jadi kalaupun tadi sebenernya udah masuk, dia ga bakal kesimpen dobel.\n"
            "  Masih gagal juga sesudah 2-3 kali? Berhenti, kabarin Louis."
        )
        return 4

    print(
        "[BELUM KEKIRIM] Halaman OKR mbalikin kode " + str(kode) + " yang ga dikenal skill ini.\n"
        "  Berkas ajuanmu tetap aman. Kabarin Louis sambil sebutin kode itu."
    )
    return 3


# ---------------------------------------------------------------------- utama


def baca_berkas(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[KURANG] Berkas '" + path + "' ga ketemu.")
        return None
    except json.JSONDecodeError as e:
        print(
            "[KURANG] Berkas '" + path + "' belum bisa dibaca, ada salah ketik di baris "
            + str(e.lineno) + ". Biasanya koma kelebihan atau tanda kutip kurang."
        )
        return None


def main():
    p = argparse.ArgumentParser(
        description="Pemeriksa dan pengirim ajuan target kuartal (OKR)."
    )
    p.add_argument("--cek-kunci", action="store_true",
                   help="cek kuncinya udah kepasang belum, nilainya ga ditampilkan")
    p.add_argument("--cek", metavar="BERKAS",
                   help="periksa berkas ajuan tanpa nyentuh internet")
    p.add_argument("--kirim", metavar="BERKAS",
                   help="periksa lalu kirim berkas ajuan ke halaman OKR")
    p.add_argument("--arah", choices=["naik", "turun"],
                   help="angkanya bagusnya naik atau turun. Wajib buat --kirim.")
    p.add_argument("--nama-saya", metavar="NAMA",
                   help="nama pemakainya, buat mastiin isian 7 bukan diri sendiri")
    a = p.parse_args()

    if a.cek_kunci:
        return cek_kunci()

    path = a.cek or a.kirim
    if not path:
        p.print_help()
        return 2

    if a.kirim and not a.arah:
        print(
            "[KURANG] Sebelum ngirim, tanya dulu ke pemakai: angkanya bagusnya NAIK atau\n"
            "  TURUN? Tanpa itu jebakan 1 dan jebakan 2 ga bisa dicek. Jalanin lagi pakai\n"
            "  --arah naik atau --arah turun."
        )
        return 2

    data = baca_berkas(path)
    if data is None:
        return 2

    masalah = periksa(data, arah=a.arah, nama_saya=a.nama_saya)
    if masalah:
        print("[KURANG] Ada " + str(len(masalah)) + " hal yang perlu dibenerin:")
        for satu in masalah:
            print("  - " + satu)
        if a.kirim:
            print("\nAjuan BELUM dikirim. Benerin dulu, baru jalanin lagi.")
        return 1

    print("[OK] Delapan isian lengkap, jebakan yang bisa dicek mesin lolos semua.")
    if a.kirim:
        print("Mulai ngirim...")
        return kirim(data, path)

    print("Jebakan 3, 4, dan mutu jebakan 5 tetap wajib ditanya ke pemakai.")
    print("Jebakan 6 nyerah ke penilai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
