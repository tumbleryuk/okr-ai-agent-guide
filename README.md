# API OKR TumblerYuk untuk AI agent

Halaman ini punya dua pembaca.

**Kalau kamu anggota tim (Nur, Ida, Alda):** yang kamu butuhkan ada di folder
[`ngajuin-target-okr/`](ngajuin-target-okr/). Buka
[`ngajuin-target-okr/references/PANDUAN-NGAJUIN-OBJECTIVE-BUAT-TIM.md`](ngajuin-target-okr/references/PANDUAN-NGAJUIN-OBJECTIVE-BUAT-TIM.md)
dulu untuk memahami isinya, lalu ikuti "Cara pasang, 3 langkah" di
[`ngajuin-target-okr/SKILL.md`](ngajuin-target-okr/SKILL.md). Sisa halaman ini teknis dan
tidak perlu dibaca.

> ⚠️ Salinan paket yang beredar sebelum 10 Agustus 2026 tidak mengirim identitas client,
> sehingga selalu ditolak `403` di pagar web sebelum key sempat diperiksa. Ambil ulang dari
> folder di atas dan hapus salinan lama.

**Kalau kamu AI agent:** kontrak lengkap yang bisa
dibaca mesin ada di [`openapi.json`](openapi.json), sedangkan aturan ringkas untuk agent ada di
[`agent-guide.json`](agent-guide.json). Contoh request dan response ada di
[`examples.json`](examples.json).

## Yang boleh dilakukan

| Operasi | Kegunaan | Izin pemakai |
|---|---|---|
| `GET /api/okr/saya` | Baca pengajuan, langkah, dan kemajuan pemilik key | Boleh langsung |
| `POST /api/okr/ajuan` | Ajukan target baru atas nama pemilik key | Wajib minta persetujuan jelas tepat sebelum kirim |

Tidak ada operasi untuk membaca orang lain, memberi vonis, mengubah status, atau membuka konsol
admin. Nama/nomor orang di badan permintaan tidak pernah menentukan pemilik; server mengambil
pemilik dari key.

## Sambungan

- Alamat dasar: `https://okr.tumbleryukoperasional.shop`
- Autentikasi setiap permintaan: `Authorization: Bearer <KEY_PRIBADI_STAF>`
- Identitas client wajib jelas: `User-Agent: TumblerYuk-OKR-Agent/1.0` (atau nama agent lain
  yang jelas). Jangan biarkan nilai bawaan `Python-urllib`, karena pagar web menolaknya `403`.
- Key adalah rahasia pribadi. Jangan tempelkan ke chat, prompt tersimpan, repo, log, screenshot,
  atau link. Simpan di secret store/variabel lingkungan milik agent.
- Jangan pernah memakai key rekan kerja untuk "menguji" akses.

Contoh membaca milik sendiri:

```http
GET /api/okr/saya HTTP/1.1
Host: okr.tumbleryukoperasional.shop
Authorization: Bearer <KEY_PRIBADI_STAF>
User-Agent: TumblerYuk-OKR-Agent/1.0
Accept: application/json
```

Contoh mengirim ada di [`contoh-ajuan.json`](contoh-ajuan.json). Saat mengirim, tambahkan:

```http
POST /api/okr/ajuan HTTP/1.1
Authorization: Bearer <KEY_PRIBADI_STAF>
User-Agent: TumblerYuk-OKR-Agent/1.0
Content-Type: application/json
Idempotency-Key: <UUID_YANG_DIBUAT_SEKALI_UNTUK_PENGAJUAN_INI>
```

Gunakan `Idempotency-Key` yang sama saat mengulang permintaan yang sama karena sambungan putus
atau server menjawab `500`. Jangan membuat nomor baru untuk retry. Nomor yang sama dengan isi
berbeda ditolak `409`.

## Cara menangani jawaban

- `200`: pembacaan berhasil.
- `201`: pengajuan tersimpan. Catat `ajuan_id` tanpa mencatat key.
- `400`: isian atau `Idempotency-Key` salah; perbaiki dahulu, jangan retry buta.
- `401`: key kosong, salah, atau sudah dicabut. Semua sengaja memakai pesan yang sama; hubungi
  Louis lewat jalur pribadi untuk rotasi.
- `409`: nomor retry dipakai untuk isi berbeda, permintaan masih berjalan, atau akun belum
  lengkap. Jangan mengganti identitas di badan; laporkan pesan aman yang diterima.
- `500`: jangan tebak apakah pengajuan masuk. Ulangi isi yang sama dengan `Idempotency-Key` yang
  sama. Jika tetap gagal, berhenti dan laporkan ke Louis.

Contoh response berhasil:

```json
{"ok": true, "ajuan_id": 123}
```

Contoh response ditolak aman:

```json
{"ok": false, "pesan": "kunci ga sah"}
```

Bentuk lengkap response baca—termasuk `ajuan`, `langkah`, dan `pr`—ada di `examples.json` agar
agent tidak menebak struktur data.

## Menyambungkan PR ke langkah

Pengajuan yang tersimpan belum menaikkan persen apa pun. Persen kemajuan bergerak hanya bila
pull request yang dibuat pemilik key **tersambung ke salah satu langkah** di pengajuannya, dan
penyambungnya adalah **judul PR**.

Cara utama, tempelkan label ini di judul PR:

```
[okr: 12] Rapikan papan protes di Konsol Revisi
```

- Angkanya adalah `id` langkah milik sendiri, dibaca dari `GET /api/okr/saya`; setiap butir
  pada daftar `langkah` membawa `id`-nya. Bukan `ajuan_id`, bukan nomor urut formulir.
- Bentuk yang dikenali: `[okr: 12]`, `[okr:12]`, `[OKR: 12]`. Besar-kecil huruf bebas, spasi sesudah
  titik dua bebas. Spasi sesudah `[` atau sebelum `:` (`[ okr: 12]`, `[okr : 12]`) tidak dikenali.
- Bentuk yang **tidak** dikenali: `[okr-12]`, `[okr 12]`, `(okr: 12)`, `[okr: #12]`.
- Label harus berada di judul PR. Nama cabang dan pesan commit tidak dibaca.

Bila label tidak dipasang, penyambungan jatuh ke cadangan: teks `kata_kunci` langkah dicari
apa adanya di dalam judul PR. Cadangan ini **gagal tanpa suara** ketika kata kunci ditulis
memakai strip (`papan-pesanan-otomatis`) sedangkan judul PR ditulis sebagai kalimat biasa.
Pekerjaan selesai, persen tetap 0%, dan tidak ada pesan kesalahan yang muncul di mana pun.

Dua hal yang wajib agent sampaikan kepada pemilik key:

1. Label yang salah bentuk, atau menunjuk langkah milik orang lain, **tidak menghasilkan
   error**. Ia diam-diam jatuh ke pencocokan kata kunci. Jadi "PR tidak ditolak" bukan bukti
   bahwa labelnya terbaca.
2. Bila langkah mengisi `repo`, PR harus berada di repo yang sama. Repo berbeda tidak
   tersambung meski kata kuncinya cocok.

Saran paling aman: isi `kata_kunci` dengan kata yang memang akan muncul apa adanya di judul PR,
**dan** tetap pasang label `[okr: <nomor>]` setiap membuat PR.

## Aturan wajib untuk AI agent

1. Mulai dengan `GET /api/okr/saya` untuk memastikan key terhubung ke nama yang benar. Tampilkan
   hanya nama pemilik dan ringkasan yang diperlukan; jangan menampilkan header autentikasi.
2. Rakit dan validasi pengajuan secara offline. Tunjukkan ringkasannya kepada pemilik key.
3. Berhenti dan minta persetujuan jelas sebelum satu-satunya operasi tulis, yaitu `POST`.
4. Setelah disetujui, kirim satu kali. Retry hanya dengan isi dan `Idempotency-Key` yang sama.
5. Jika respons memuat nomor HP, key, hash, data orang lain, atau jejak error server, jangan
   sebarkan; hentikan pemakaian dan laporkan sebagai insiden.

Key lama yang pernah dibagikan boleh dipakai hanya bila uji `GET /api/okr/saya` di server hidup
menjawab `200` dan nama pemiliknya benar. Awalan atau nama file key saja bukan bukti bahwa key
masih aktif.
