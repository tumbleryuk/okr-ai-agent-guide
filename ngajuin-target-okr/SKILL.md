---
name: ngajuin-target-okr
description: >-
  Mandu Nur, Ida, atau Alda ngisi 8 isian pengajuan target kuartal sampai lengkap, nyegat 6 jebakan yang paling sering bikin ditolak, lalu ngirim ke halaman OKR internal dan jelasin balikannya pakai bahasa sehari-hari. Buat orang non-teknis, ga perlu ngerti coding. Trigger - "mau ngajuin target kuartal", "ngajuin objective", "isi formulir OKR", "bantu bikin target kuartal gua", "cek ajuan target gua udah bener belum", "kirim pengajuan target", "target kuartal gua udah layak belum", "ngajuin-target-okr".
domain: tim-okr
status: active
reversibility: irreversible
invoke: auto
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Ngajuin Target Kuartal

Buat Nur, Ida, dan Alda. Kamu ga perlu ngerti coding. Kamu ngobrol biasa, agent ini
yang nyusun dan ngirim.

**OKR** itu istilah buat "target kuartal yang diukur pakai angka". Tiap kali ketemu kata
OKR di sini, artinya itu.

---

## Buat siapa dan buat apa

Kamu bebas milih mau ngerjain apa kuartal ini. Yang ga bebas cuma satu: cara mbuktiin
kerjaanmu berhasil harus berbentuk angka yang orang lain bisa hitung ulang.

Anggap target kamu kayak timbangan di dapur. Kalau jarumnya bisa gerak ke kiri dan ke
kanan, itu timbangan. Kalau jarumnya cuma bisa nunjuk "berhasil", itu bukan timbangan,
itu stiker.

---

## Cara pasang, 3 langkah

Buat kamu yang belum pernah masang skill sama sekali.

Dua langkah pertama nyuruh kamu nempatin berkas di **folder rumah kamu**, alamatnya
`C:\Users\<nama-kamu>\`. Belum tau `<nama-kamu>` isinya apa? Buka File Explorer, klik kolom
alamat di atas, ketik `%USERPROFILE%`, tekan Enter. Folder yang kebuka itu folder rumahmu,
dan alamat lengkapnya kelihatan di kolom yang sama.

1. **Taruh foldernya.** Salin folder `ngajuin-target-okr` (folder yang lagi kamu baca ini)
   ke `C:\Users\<nama-kamu>\.claude\skills\`. Kalau folder `.claude` atau `skills` belum
   ada, bikin dulu. Hasil akhirnya jadi begini:
   `C:\Users\<nama-kamu>\.claude\skills\ngajuin-target-okr\SKILL.md`.

   Ambil foldernya dari halaman panduan yang Louis kasih linknya, jangan dari salinan lama
   yang beredar di chat. Salinan lama ada yang ketahan pagar web dan ga bisa ngirim.
2. **Simpen kunci dari Louis.** Louis ngasih kamu satu baris kunci lewat jalur pribadi.
   Bikin berkas namanya `okr-kunci.txt` di `C:\Users\<nama-kamu>\.claude\`, jadi alamat
   lengkapnya `C:\Users\<nama-kamu>\.claude\okr-kunci.txt`. Tempel kunci itu di dalamnya,
   simpan. Isinya cuma kuncinya doang, ga usah nulis apa-apa lagi. Kunci ini punya kamu
   sendiri, jangan dikasih ke siapa pun, termasuk temen se-tim.
3. **Panggil.** Buka Claude Code, ketik: `mau ngajuin target kuartal`. Selesai.

Catatan buat yang pakai Mac: folder rumahnya `/Users/<nama-kamu>/` dan garis miringnya
kebalik, sisanya sama. Tim ini pakai Windows, jadi ikutin yang di atas.

---

## Kunci

Agent baca kunci dari salah satu dari dua tempat ini, urut:

1. Variabel lingkungan `OKR_KUNCI`
2. Berkas `~/.claude/okr-kunci.txt` (di Windows: `C:\Users\<nama-kamu>\.claude\okr-kunci.txt`)

**Kalau dua-duanya nol ada:** berhenti di situ. Bilang ke pemakai "kuncimu belum kepasang,
minta ke Louis dulu lewat chat pribadi, terus simpen sesuai langkah 2 di atas". JANGAN
nebak kunci, JANGAN bikin kunci sendiri, JANGAN lanjut ngirim.

Kunci ga pernah ditampilkan di layar, ga pernah ditulis ke berkas ajuan, ga pernah masuk
catatan. Dia cuma lewat sekali waktu ngirim.

---

## Alur yang agent ikutin

### Langkah 0. Alamat alatnya
Alatnya ada di folder skill ini, bukan di folder kerja pemakai. Jadi PINDAH DULU ke folder
alatnya, baru jalanin perintahnya:

```bash
cd C:\Users\<nama-kamu>\.claude\skills\ngajuin-target-okr
```

Ganti `<nama-kamu>` sama nama folder rumah pemakai. Belum tau isinya apa? Cari sekali,
sesuai jendela hitam yang kepakai:
- PowerShell: `echo $env:USERPROFILE`
- Command Prompt (cmd): `echo %USERPROFILE%`
- Git Bash: `echo $HOME`

Sesudah pindah, semua perintah di bawah ditulis pendek: `python kirim_ajuan.py ...`.

⛔ Aturannya sempit, baca persis: JANGAN pakai `~` atau `%USERPROFILE%` sebagai POTONGAN
ALAMAT di dalam perintah — mis. `python ~/.claude/skills/.../kirim_ajuan.py` atau
`cd %USERPROFILE%\.claude\skills\...`. Tiap singkatan itu cuma diterjemahin di satu jenis
jendela: `~` di Git Bash, `%USERPROFILE%` di cmd. Di jendela lain dia dianggap nama folder
beneran dan perintahnya mentok `No such file or directory`.

Yang di atas itu BEDA sama tiga perintah pencarian di daftar barusan. Di situ singkatannya
bukan potongan alamat, dan tiap baris udah dipasangin jendelanya sendiri — jadi aman.
Ambil jawabannya sekali, terus tulis alamat PENUH di semua perintah sesudah itu.

Kalau `python` ga dikenal komputernya, coba `py` atau `python3`. Kalau tiga-tiganya nol
jalan, bilang ke pemakai suruh kabarin Louis, jangan diakalin.

### Langkah 1. Cek kunci dulu

```bash
python kirim_ajuan.py --cek-kunci
```

Perintah ini nanya ke halaman OKR beneran, bukan cuma ngintip berkas di komputer. Empat
kemungkinan jawabannya, dan empat-empatnya beda artinya:

- **Kunci hidup** - dia sebutin nama pemilik kuncinya. Cocokin sama nama pemakai. Kalau
  namanya orang lain, STOP, suruh kabarin Louis.
- **Kunci belum kepasang** - berhenti sesuai bagian Kunci di atas. Boleh tetap bantu nyusun
  isian, tapi jangan janji bisa ngirim.
- **Kunci ga sah** - kuncinya udah diganti. Suruh minta kunci baru ke Louis. Jangan nyoba
  kunci lain.
- **Belum kejawab** (sambungan gagal atau kode 403) - ini BUKAN kunci salah. Jangan bilang ke
  pemakai kuncinya bermasalah. Suruh coba lagi; kalau kode 403 yang keluar, alatnya versi
  lama dan wajib diambil ulang dari halaman panduan.

### Langkah 2. Tanya isian satu per satu
Buka `references/formulir-8-isian.md`, di situ ada arti tiap isian plus contoh bener dan
salah. **Tanya satu isian per giliran, jangan borong delapan sekaligus.** Orangnya lagi
mikir, bukan lagi ngisi formulir kantor.

Kalau jawabannya masih kabur, pantulin balik pakai contoh salah yang ada di berkas itu,
lalu tanya ulang. Jangan diterima mentah cuma karena kolomnya udah keisi.

Isian nomor 4 (angka sebelum) yang paling makan waktu, karena dia butuh buka data lama.
Kalau orangnya belum siap, bilang terus terang: isian ini ga bisa dikebut semalam, mending
disiapin dulu baru balik lagi ke sini.

### Langkah 3. Tanya arah angkanya
Sesudah isian 4 dan 5 keisi, tanya satu hal yang ga ada di formulir tapi wajib buat ngecek:

> "Angka ini bagusnya NAIK atau TURUN?"

Contoh: "persen pesanan yang disalin manual" bagusnya turun. "Jumlah desain yang lolos
sekali jadi" bagusnya naik. Jawaban ini nentuin isian 4 dan 5 masuk akal apa nggak. Agent
JANGAN nebak sendiri arahnya, tanya orangnya.

### Langkah 3b. Tanya langkah pelaksanaannya (WAJIB, jangan dilewat)
Delapan isian di atas njelasin apa yang mau DIUKUR. Bagian ini njelasin pekerjaan apa yang
bakal DIKERJAIN. Halaman OKR ngitung dua persen yang beda, dan yang kedua cuma bisa jalan
kalau bagian ini keisi:

| Yang diitung | Sumbernya |
|---|---|
| Kemajuan dampak | angkanya gerak dari angka sebelum ke ambang |
| Kemajuan pengerjaan | PR yang kelar, dicocokin ke langkah lewat `kata_kunci` |

**Ajuan tanpa langkah bikin kemajuan pengerjaan mentok 0% sepanjang kuartal** — bukan karena
orangnya ga kerja, tapi karena nol ada yang bisa dicocokin.

Tanya dua hal per langkah, minimal satu langkah:

1. "Pekerjaan apa aja yang bakal kamu kerjain buat ngejar ini?" -> jadi `judul`
2. "Nanti judul PR-nya kira-kira ada kata apa?" -> jadi `kata_kunci`

Pencocoknya harfiah: **kata kunci wajib muncul apa adanya di judul PR.** `papan-pesanan` nol
cocok sama judul "papan pesanan" (spasi vs strip). Agent JANGAN ngarang kata kunci sendiri —
tanya orangnya, terus bacain balik contoh judul PR yang bakal cocok, biar dia bisa mbantah
sebelum kekirim.

Dua aturan yang bikin server nolak: nol boleh dua langkah pakai kata kunci yang sama, dan nol
boleh satu kata kunci jadi potongan kata kunci lain (`papan` vs `papan-pesanan` bentrok).

`bobot` dan `repo` boleh kosong. Bobot kosong = dibagi rata otomatis. Detailnya di
`references/formulir-8-isian.md` bagian "Plus: langkah pelaksanaan".

### Langkah 4. Cegat 6 jebakan
Buka `references/6-jebakan.md`. Lewatin ajuan itu ke enam pertanyaannya SEBELUM dikirim.
Ini bagian paling penting dari skill ini. Server juga ngecek, tapi kalau nunggu ditolak
server, orangnya kebuang satu ronde percuma.

### Langkah 5. Rakit berkas ajuan lalu cek mesin
Tulis jawabannya jadi satu berkas, misal `ajuan-<nama>.json`, di folder kerja pemakai
(JANGAN di dalam folder skill). Nama isian di berkas itu wajib persis kayak tabel di bawah,
nol boleh nambah atau ngarang nama baru.

Terus jalanin pemeriksanya:

```bash
python kirim_ajuan.py --cek ajuan-nur.json --arah turun --nama-saya Nur
```

Pemeriksa ini jalan di komputer sendiri, nol nyentuh internet. Kalau dia nemu yang kurang,
benerin dulu bareng pemakai, ulangi sampai bersih.

**Kuartal baru = berkas baru.** Ajuan kuartal ini JANGAN ngedit berkas ajuan kuartal lalu.
Bikin berkas baru, misal `ajuan-nur-2026-Q4.json`. Halaman OKR naruh ajuan di kuartal
**tanggal `jendela_mulai`**, bukan di kuartal hari ngirim. Tanggal yang kesalin dari contoh
atau dari ajuan lama bikin ajuan nyasar ke kuartal yang udah lewat. Ajuannya diterima tanpa
error, tapi nol muncul di papan dan persennya 0% sepanjang kuartal. Pemeriksa sekarang nolak
`jendela_mulai` di luar kuartal yang lagi jalan (atau kuartal depan), jadi kalau dia protes
soal kuartal, ganti tanggalnya, jangan diakalin.

### Langkah 6. Bacain ulang, minta izin, baru kirim
Tampilkan ringkasan delapan isian PLUS langkah pelaksanaannya pakai bahasa sehari-hari,
bukan tampilan berkas mentah. Langkahnya ikut dibacain: judul + kata kuncinya.
Terus tanya: "udah pas? kirim sekarang?" Tunggu jawaban jelas.

Ngirim itu **ga bisa ditarik**. Begitu masuk, penilai lihat. Jadi jangan main kirim duluan.

```bash
python kirim_ajuan.py --kirim ajuan-nur.json --arah turun --nama-saya Nur
```

### Langkah 6b. ⚠️ Kirim ulang = RONDE BARU, dan langkah lama kamu ikut dipensiunin

Ini jebakan yang paling gampang kena dan paling susah keliatan, karena **nol ada pesan error
sama sekali**.

Tiap ajuan baru yang mendarat bikin halaman OKR **nyetempel `ganti_arah` ke SEMUA langkah
punya orang itu di kuartal yang sama**, bukan cuma langkah di ajuan lama yang mau diganti.
Yang dilewatin cuma langkah yang statusnya udah nol-aktif dari sananya.

Akibatnya, kalau kamu kirim ulang cuma buat NAMBAH satu langkah baru:

- langkah baru itu masuk dengan status `jalan`, dan
- **semua langkah lamamu yang masih kamu kerjain berubah jadi `ganti_arah`**, artinya
  "ditinggal, sengaja dibuang dari hitungan". Di papan penilai targetnya jadi kosong, bukan 0%.

**Jadi aturannya:** berkas kiriman ulang WAJIB bawa **SEMUA langkah yang masih dikerjain**,
bukan cuma yang baru. Perlakuin dia sebagai daftar utuh yang menggantikan daftar lama, bukan
sebagai tambahan.

Sebelum ngirim ulang, agent WAJIB:

1. Tarik dulu daftar langkah yang sekarang: `GET /api/okr/saya`, lihat tiap butir `langkah`
   beserta `id` dan `status`-nya.
2. Bacain ke pemakai: "langkah kamu sekarang ada N. Yang masih kamu kerjain yang mana aja?"
3. Tulis ulang SEMUA yang masih dikerjain ke berkas kiriman, plus yang baru.
4. Baru kirim.

**Nol ada tombol buat ngebalikin status langkah satu-satu.** Langkah yang terlanjur
ke-`ganti_arah` cuma bisa idup lagi lewat kiriman berikutnya yang nyebut dia lagi. Ini yang
bikin langkah 1-3 di atas bukan saran, tapi wajib.

⚠️ Nomor `ronde` mentok di 2. Kiriman ketiga dan seterusnya TETAP diterima dan langkah
lamanya TETAP dipensiunin, cuma nomor rondenya nol naik lagi.

### Langkah 7. Terjemahin balikannya
Lihat bagian "Balikan dan artinya" di bawah. Jangan nempel balasan mentah ke pemakai.

### Langkah 8. Sesudah ajuan masuk: nyantolin PR ke langkah

Ajuan yang kesimpen belum ngasih persen apa-apa. Persen kemajuan naik cuma kalau PR yang
kamu bikin **kesambung ke salah satu langkah** di ajuanmu. Nyambungnya lewat JUDUL PR, dan
ada dua jalan.

**Jalan pintas yang dipakai duluan: tempel `[okr: <nomor langkah>]` di judul PR.**

```
[okr: 12] Rapiin papan protes di Konsol Revisi
```

- Nomornya = `id` langkah punyamu, ambil dari `GET /api/okr/saya` (tiap butir di daftar
  `langkah` bawa `id`-nya sendiri). Bukan nomor ajuan, bukan nomor urut di formulir.
- Bentuk yang dikenal: `[okr: 12]`, `[okr:12]`, `[OKR: 12]` — besar-kecil huruf bebas, spasi
  sesudah titik dua bebas. Spasi sesudah `[` atau sebelum `:` (`[ okr: 12]`, `[okr : 12]`)
  NOL dikenal.
- Bentuk yang **NOL dikenal**: `[okr-12]`, `[okr 12]`, `(okr: 12)`, `[okr: #12]`. Titik dua
  itu wajib, dan kurungnya wajib kurung siku.
- Boleh ditaruh di depan atau di belakang judul, asal masih di judul PR — bukan di badan PR,
  bukan di nama cabang, bukan di pesan commit.

**Jalan cadangan kalau labelnya nol dipasang: kata kunci.** Sistemnya bakal nyari teks
`kata_kunci` langkahmu di dalam judul PR, apa adanya. Ini yang sering **gagal senyap**:
kata kunci biasanya ditulis pakai strip (`papan-pesanan-otomatis`) sedangkan judul PR ditulis
kalimat biasa pakai spasi ("Papan pesanan otomatis"). Dua-duanya kelihatan sama di mata
orang, tapi buat mesin nol nyambung — PR-nya kelar, persennya tetap 0%, dan **nol ada pesan
error sama sekali**.

**Yang wajib agent kasih tau ke pemakai, dua hal:**

1. Label yang salah bentuk, atau nomor langkah punya orang lain, **nol bikin error**. Dia
   diam-diam jatuh ke jalan cadangan kata kunci — jadi "PR-nya nol ketolak" BUKAN bukti
   labelnya kebaca.
2. Kalau langkahnya diisi `repo`, PR-nya wajib di repo itu juga. Beda repo = nol nyantol,
   walau kata kuncinya cocok.

Saran paling aman: pas ngerakit ajuan, bikin `kata_kunci` yang bakal kepakai apa adanya di
judul PR (satu-dua kata biasa, tanpa strip), DAN tetap pasang label `[okr: <nomor>]` tiap
bikin PR. Dua-duanya nyala = nol gantung di satu jalur.

---

## Peta isian ke nama yang dikirim

Delapan isian yang diisi pemakai, dua belas nama isian plus satu daftar yang dikirim ke
halaman OKR. Yang bikin jumlahnya beda: isian 5, 6, dan 8 pecah jadi beberapa bagian.

| Isian yang ditanya ke pemakai | Nama isian waktu dikirim |
|---|---|
| 1. Klaim | `klaim` |
| 2. Jejak | `jejak` |
| 3. Cara baca | `cara_baca` |
| 4. Angka sebelum (rincian per minggu) | `baseline`, daftar berisi `tanggal_mulai` + `angka` tiap minggu |
| 5. Ambang | `ambang` + `satuan` |
| 6. Jendela | `jendela_mulai` + `jendela_selesai` + `jendela_min_data` |
| 7. Siapa yang dipakein | `dipakein_siapa` |
| 8. Kalau gagal ketahuannya gimana | `merah_kondisi` + `penjaga_nama` + `penjaga_ambang` |
| **Plus: langkah pelaksanaan (wajib)** | `langkah`, daftar berisi `judul` + `kata_kunci` (wajib) dan `bobot` + `repo` (boleh kosong) |

Aturan nulisnya:
- **Semua isian ditulis sebagai teks**, termasuk yang isinya angka. `"ambang": "20"`, bukan
  `"ambang": 20`. Pemeriksanya benerin ini sendiri, tapi jangan diandelin.
- **Tanggal formatnya `2026-08-01`** (tahun, bulan, tanggal). Tanggal apa pun di sini
  dibaca sebagai tanggal Indonesia, jam WIB.
- `tanggal_mulai` di daftar `baseline` = hari Senin minggu itu.
- `satuan` diisi kayak `persen`, `menit`, `pesanan`, `kali`. Satu kata, sesuai yang dihitung
  di isian 3.
- `jendela_min_data` = minimal berapa kali kepakai dalam seminggu supaya minggu itu ikut
  dihitung. Contoh panduan pakai `10`.
- `penjaga_ambang` = angka batas buat angka penjaga, bukan kalimat.

Contoh berkas yang udah kebentuk lengkap ada di `references/contoh-ajuan.json`. Contoh itu
isinya cerita bohongan buat belajar, bukan punya siapa-siapa.

---

## Balikan dan artinya

Enam kemungkinan. Terjemahin ke bahasa sehari-hari, jangan tempel apa adanya.

**Kesimpen (kode 201).** Ajuan masuk dan dapet nomor. Sebutin nomornya ke pemakai, misal
"ajuanmu kesimpen, nomornya 12, simpen nomor ini buat nanya perkembangan". Sesudah ini
pemakai nunggu laporan penilaian.

**Ada yang salah isi (kode 400).** Halaman OKR balikin daftar alasan. Bacain satu per satu
pakai kalimat biasa, ajak benerin bareng, terus kirim ulang. **Ini bukan penolakan
penilaian**, jadi ga makan jatah "boleh ngajuin ulang 2 kali". Bilang gitu ke pemakai biar
dia ga panik.

**Kunci ga sah (kode 401).** Berhenti total. Bilang: "kuncimu ga dikenali, hubungi Louis
lewat chat pribadi buat minta kunci baru". JANGAN nebak-nebak, JANGAN nyoba kunci lain,
JANGAN kirim ulang berkali-kali.

**Ditolak pagar web (kode 403).** Kiriman ketahan di gerbang, kunci belum sempat dicek. Ini
bukan salah kunci dan bukan salah isian. Hampir selalu artinya alat ini versi lama. Bilang:
"alatnya perlu diambil ulang dari halaman panduan yang Louis kasih". Jangan kirim ulang
pakai alat yang sama, hasilnya bakal sama terus.

**Akun belum kedaftar atau kiriman dobel (kode 409).** Bilang: "namamu belum didaftarin di
halaman OKR, atau kiriman yang sama masih jalan. Hubungi Louis dulu". Berhenti juga.
Cara mastiin akunnya beres: `--cek-kunci` nyebut nama kamu = akunnya kedaftar, jadi 409-nya
soal nomor kiriman. Alat versi sekarang bikin nomor kiriman BARU tiap isi berkas berubah, jadi
409 gara-gara "berkas lama diedit lalu dikirim lagi" nol kejadian lagi. Kalau tetap 409, alatnya
hampir pasti versi lama: ambil ulang dari halaman panduan.

**Halaman OKR lagi ngadat (kode 500 ke atas).** Ini SATU-SATUNYA kode yang boleh diulang.
Halamannya yang lagi sakit, bukan kunci dan bukan isian, dan belum ketahuan ajuannya masuk
atau nggak. Jangan nebak, jangan ngedit berkas ajuannya, jangan bikin berkas baru. Jalanin
ulang perintah yang PERSIS SAMA. Nomor kiriman otomatis kepakai lagi, jadi kalaupun tadi
sebenernya udah masuk, halaman OKR nolak nyimpen dobel. Masih gagal sesudah 2 sampai 3
kali, berhenti dan kabarin Louis.

**Halamannya belum bisa dibuka (nyambungnya gagal).** Halaman OKR-nya lagi disiapin dan
belum tentu udah nyala. Kalau nyambungnya gagal, JANGAN tampilin pesan error mentah.
Bilang apa adanya: "halaman pengajuannya kelihatannya belum dibuka. Berkas ajuanmu udah
kesimpen rapi di komputer, tinggal dikirim begitu Louis ngabarin halamannya siap." Terus
tunjukin di mana berkasnya disimpan.

---

## Pagar

- **Ngirim ga bisa ditarik.** Wajib ada izin jelas dari pemakai di langkah 6.
- **Nomor kiriman ngikutin isi berkas.** Nomornya disimpen di berkas pendamping
  `<nama-ajuan>.json.nomor-kirim` bareng sidik isinya. Isi SAMA dikirim ulang (sambungan
  putus, kode 500) = nomor sama, halaman OKR nol nyimpen dobel. Isi DIEDIT lalu dikirim = nomor
  baru = ronde baru (baca Langkah 6b dulu). JANGAN hapus berkas pendamping itu, dan jangan
  bikin salinan berkas ajuan buat ngirim ulang.

---

## Kalau mentok

Kalau alatnya error yang nol kejelasan di bagian "Balikan dan artinya", atau panduan ini
nyuruh sesuatu yang nol jalan di komputermu: **jangan diakalin, jangan nyoba-nyoba kunci**.
Bikin laporan di repo ERP TumblerYuk (yang biasa dipakai tim buat lapor), pasang label
`lapor-tim`, judulnya diawali `[okr]`. Tempel perintah yang kamu jalanin + pesan yang keluar
apa adanya, **tanpa kunci**. Laporan di situ yang bikin panduan ini dibenerin buat semua orang;
keluhan lewat chat pribadi gampang ketelen.
- **Nol kunci nempel di berkas skill.** Kunci cuma dari `OKR_KUNCI` atau `okr-kunci.txt`.
- **Nol nama isian karangan.** Cuma dua belas nama plus `baseline` dan `langkah` yang ada di tabel atas.
- **Nol ngisiin jawaban pemakai.** Agent boleh mancing, mantulin, ngasih contoh. Agent
  JANGAN ngarang angka isian 4, ngarang nama sistem di isian 2, atau ngarang nama orang di
  isian 7. Yang dinilai kerjaan pemakai, bukan kerjaan agent.
- **Jam apa pun yang disebut = WIB.**

---

## Rujukan

- `references/PANDUAN-NGAJUIN-OBJECTIVE-BUAT-TIM.md` - panduan buat dibaca manusia, mulai dari sini
- `references/formulir-8-isian.md` - arti tiap isian, contoh bener dan salah, contoh jadi
- `references/6-jebakan.md` - enam pertanyaan yang wajib dilewatin sebelum kirim
- `references/contoh-ajuan.json` - contoh berkas ajuan yang udah kebentuk
- `kirim_ajuan.py` - pemeriksa dan pengirim

Tingkat 1, 2, dan 3 nentuin **skor final** per orang per kuartal di halaman OKR. Nol angka
uang yang nempel di tingkat. Arti tiap tingkat ada di `references/formulir-8-isian.md`.
