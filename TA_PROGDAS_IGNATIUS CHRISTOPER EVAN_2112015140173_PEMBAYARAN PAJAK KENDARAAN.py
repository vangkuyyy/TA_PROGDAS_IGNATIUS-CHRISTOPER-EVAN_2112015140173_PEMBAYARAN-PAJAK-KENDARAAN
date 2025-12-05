import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from collections import Counter
import ttkthemes
from PIL import Image, ImageTk
import datetime

# ================= DATA MODEL / OOP ==================
# [MODUL 5 - INHERITANCE]
class KendaraanDasar:
    """Superclass sederhana berisi atribut dasar kendaraan."""
    def __init__(self, nomor_polisi: str, jenis: str):
        self.nomor_polisi = nomor_polisi
        self.jenis = jenis


# [MODUL 5 - INHERITANCE - Subclass]
class Kendaraan(KendaraanDasar):
    """Kelas Kendaraan yang mewarisi KendaraanDasar dan menambahkan atribut pajak."""
    def __init__(self, nomor_polisi, jenis, bbnkb, pajak_pokok, opsen_pokok, swdkllj, bulan_terlambat):
        super().__init__(nomor_polisi, jenis)
        # Simpan nilai moneter sebagai float untuk akurasi
        self.bbnkb = float(bbnkb)
        self.pajak_pokok = float(pajak_pokok)
        self.opsen_pokok = float(opsen_pokok)
        self.swdkllj = float(swdkllj)
        self.bulan_terlambat = int(bulan_terlambat)


# [MODUL 4 - METHOD dengan RETURN]
class PajakService:
    def __init__(self, kendaraan: Kendaraan):
        self.kendaraan = kendaraan

    def hitung_denda(self) -> float:
        # Denda 2% per bulan terlambat dari pajak pokok
        return 0.02 * self.kendaraan.pajak_pokok * max(0, self.kendaraan.bulan_terlambat)

    def hitung_total(self) -> float:
        return (
            self.kendaraan.bbnkb +
            self.kendaraan.pajak_pokok +
            self.kendaraan.opsen_pokok +
            self.kendaraan.swdkllj +
            self.hitung_denda()
        )


# [MODUL 4 - METHOD & RETURN]
class Pembayaran:
    def __init__(self, total: float):
        self.total = float(total)

    def proses(self, uang: float):
        uang = float(uang)
        # [MODUL 2 - PENGKONDISIAN IF]
        if uang < self.total:
            return None
        return uang - self.total


# ================= GUI APP =====================
# [MODUL 8 - GUI - Tkinter]
# [MODUL 4 - METHOD dalam class]
class PajakGUI:

    def __init__(self, root):
        self.root = root
        root.title("Sistem Pembayaran Pajak Kendaraan")
        root.geometry("1200x700")
        root.configure(bg="#1E1E2E")

        self.setup_style()
        # DB connection
        self.conn = sqlite3.connect("pajak.db")
        self.create_table()

        # build UI
        self.build_layout()

    # =================== STYLE ===================
    def setup_style(self):
        # Menggunakan ttkthemes untuk tema gelap modern (jika tersedia)
        try:
            style = ttkthemes.ThemedStyle(self.root)
            style.set_theme("equilux")
            style.configure("TLabel", font=("Segoe UI", 10), foreground="white")
            style.configure("Title.TLabel",
                            font=("Segoe UI", 20, "bold"),
                            foreground="#00D4AA")
            style.configure("TButton",
                            font=("Segoe UI", 10, "bold"),
                            padding=8,
                            background="#00D4AA")
            style.configure("Card.TLabelframe",
                            background="#2A2D3A",
                            relief="flat")
            style.configure("Card.TLabelframe.Label",
                            font=("Segoe UI", 11, "bold"),
                            foreground="white")
        except Exception:
            # Jika ttkthemes tidak tersedia, tetap pakai ttk default
            pass

    # ============== CREATE TABLE ==================
    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pembayaran(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomor_polisi TEXT,
                jenis TEXT,
                total REAL,
                denda REAL,
                kembalian REAL,
                tanggal TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    # ================= MAIN LAYOUT ================
    def build_layout(self):
        header_frame = tk.Frame(self.root, bg="#1E1E2E")
        header_frame.pack(pady=10)

        # Logo kecil (jika ada)
        try:
            self.logo_img = ImageTk.PhotoImage(Image.open("logo.png").resize((50, 50)))
            logo_label = tk.Label(header_frame, image=self.logo_img, bg="#1E1E2E")
            logo_label.pack(side="left", padx=10)
        except Exception:
            pass

        header = ttk.Label(
            header_frame,
            text="💳 SISTEM PEMBAYARAN PAJAK KENDARAAN",
            style="Title.TLabel"
        )
        header.pack(side="left")

        container = tk.Frame(self.root, bg="#1E1E2E")
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)

        self.build_form(container)
        self.build_output(container)

    # ================= FORM =====================
    # [MODUL 8 - GUI - FORM INPUT]
    # [MODUL 1 - Variabel & tipe data digunakan pada entries]
    def build_form(self, parent):
        form = ttk.Labelframe(
            parent,
            text=" Input Kendaraan ",
            style="Card.TLabelframe",
            padding=15
        )
        form.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.entries = {}

        fields = [
            ("Nomor Polisi", "nomor"),
            ("Jenis Kendaraan", "jenis"),
            ("BBNKB", "bbnkb"),
            ("Pajak Pokok", "pajak"),
            ("Opsen Pokok", "opsen"),
            ("SWDKLLJ", "swdkllj"),
            ("Bulan Terlambat", "bulan"),
            ("Uang Bayar", "uang")
        ]

        # [MODUL 3 - PERULANGAN FOR]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(form, width=28)
            entry.grid(row=i, column=1, pady=5, padx=8)
            self.entries[key] = entry

        btn_frame = tk.Frame(form, bg="#2A2D3A")
        btn_frame.grid(row=len(fields), columnspan=2, pady=15)

        # Progress bar untuk feedback saat proses
        self.progress = ttk.Progressbar(btn_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)
        self.progress.pack_forget()  # sembunyikan sampai dipakai

        ttk.Button(btn_frame, text="✅ PROSES", width=20,
                   command=self.proses_pembayaran).pack(pady=5)

        ttk.Button(btn_frame, text="🗃️ RIWAYAT",
                   command=self.tampilkan_riwayat).pack(fill="x", pady=3)

        ttk.Button(btn_frame, text="📤 EXPORT PDF",
                   command=self.konfirmasi_export).pack(fill="x", pady=3)

        ttk.Button(btn_frame, text="📊 STATISTIK",
                   command=self.tampilkan_statistik).pack(fill="x", pady=3)

    # ================= OUTPUT ===================
    def build_output(self, parent):
        out = ttk.Labelframe(
            parent,
            text=" Output & Riwayat ",
            style="Card.TLabelframe",
            padding=15
        )
        out.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.tabs = ttk.Notebook(out)
        self.tabs.pack(fill="both", expand=True)

        # ---------- TAB STRUK ----------
        self.text_area = tk.Text(
            self.tabs,
            font=("Consolas", 11),
            bg="#020617",
            fg="#F8FAFC",
            wrap="word"
        )
        self.tabs.add(self.text_area, text="🧾 STRUK")

        # ---------- TAB RIWAYAT ----------
        tree_frame = tk.Frame(self.tabs, bg="#2A2D3A")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("tanggal", "nomor", "jenis", "total"),
            show="headings"
        )

        self.tree.heading("tanggal", text="Tanggal")
        self.tree.heading("nomor", text="Nomor Polisi")
        self.tree.heading("jenis", text="Jenis")
        self.tree.heading("total", text="Total Bayar")

        self.tree.column("tanggal", width=170)
        self.tree.column("nomor", width=140)
        self.tree.column("jenis", width=150)
        self.tree.column("total", width=120)

        # Scrollbar untuk treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tabs.add(tree_frame, text="📑 RIWAYAT")

    # ================= PROCESS ==================
    def proses_pembayaran(self):
        try:
            nomor = self.entries["nomor"].get().strip()
            jenis = self.entries["jenis"].get().strip()

            # Validasi minimal
            if not nomor or not jenis:
                raise ValueError("Nomor polisi atau jenis kosong")

            bbnkb = float(self.entries["bbnkb"].get())
            pajak = float(self.entries["pajak"].get())
            opsen = float(self.entries["opsen"].get())
            swdkllj = float(self.entries["swdkllj"].get())
            bulan = int(self.entries["bulan"].get())
            uang = float(self.entries["uang"].get())

            kendaraan = Kendaraan(nomor, jenis, bbnkb, pajak, opsen, swdkllj, bulan)

        except ValueError:
            messagebox.showerror("ERROR", "Input belum lengkap atau bukan angka.")
            return

        # Mulai progress bar
        self.progress.pack(fill="x", pady=5)
        self.progress.start()

        # Simulasi proses (gunakan after untuk delay agar terlihat)
        self.root.after(1200, lambda: self.finalize_proses(kendaraan, uang))

    def finalize_proses(self, kendaraan, uang):
        self.progress.stop()
        self.progress.pack_forget()  # Sembunyikan progress bar

        pajak = PajakService(kendaraan)
        total = pajak.hitung_total()
        denda = pajak.hitung_denda()

        bayar = Pembayaran(total)
        kembalian = bayar.proses(uang)

        if kembalian is None:
            messagebox.showerror("ERROR", f"Uang tidak cukup. Total yang harus dibayar: {int(total)}")
            return

        try:
            self.conn.execute(
                """INSERT INTO pembayaran
                (nomor_polisi,jenis,total,denda,kembalian)
                VALUES (?,?,?,?,?)""",
                (kendaraan.nomor_polisi, kendaraan.jenis, total, denda, kembalian)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Gagal simpan data: {e}")
            return

        # SIMPAN SESSION
        self.last = (kendaraan, total, denda, kembalian)

        # CETAK STRUK
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(
            tk.END,
f"""
========== STRUK PAJAK ==========
Tanggal      : {now}
Nomor Polisi : {kendaraan.nomor_polisi}
Jenis        : {kendaraan.jenis}

BBNKB        : {int(kendaraan.bbnkb)}
Pajak Pokok  : {int(kendaraan.pajak_pokok)}
Opsen Pokok  : {int(kendaraan.opsen_pokok)}
SWDKLLJ      : {int(kendaraan.swdkllj)}
Denda        : {int(denda)}
-----------------------------
TOTAL        : {int(total)}
KEMBALIAN    : {int(kembalian)}
================================
"""
        )

        for e in self.entries.values():
            e.delete(0, tk.END)

    # ================= HISTORY ==================
    def tampilkan_riwayat(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.conn.execute("""
            SELECT tanggal,nomor_polisi,jenis,total
            FROM pembayaran
            ORDER BY tanggal DESC
        """).fetchall()

        for r in rows:
            # r = (tanggal, nomor_polisi, jenis, total)
            self.tree.insert("", "end", values=(r[0], r[1], r[2], int(r[3])))

    # ================= EXPORT ===================
    def konfirmasi_export(self):
        if not hasattr(self, "last"):
            messagebox.showerror("ERROR", "Tidak ada struk.")
            return
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin export struk ke PDF?"):
            self.export_pdf()

    def export_pdf(self):
        kendaraan, total, denda, kembalian = self.last

        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"struk_{kendaraan.nomor_polisi}.pdf"
        )

        if not file: return

        c = canvas.Canvas(file, pagesize=letter)
        y=750
        lines=[
            "===== STRUK PAJAK =====",
            f"Nomor Polisi : {kendaraan.nomor_polisi}",
            f"Jenis        : {kendaraan.jenis}",
            "",
            f"BBNKB        : {int(kendaraan.bbnkb)}",
            f"Pajak Pokok  : {int(kendaraan.pajak_pokok)}",
            f"Opsen Pokok  : {int(kendaraan.opsen_pokok)}",
            f"SWDKLLJ      : {int(kendaraan.swdkllj)}",
            f"Denda        : {int(denda)}",
            "",
            f"TOTAL        : {int(total)}",
            f"Kembalian    : {int(kembalian)}"
        ]

        for l in lines:
            c.drawString(100,y,l)
            y-=20

        c.save()
        messagebox.showinfo("SUKSES","PDF berhasil dibuat!")

    # ================= STAT =====================
    def tampilkan_statistik(self):
        data = self.conn.execute(
            "SELECT jenis FROM pembayaran"
        ).fetchall()

        # [MODUL 2 - IF CEK DATA]
        if not data:
            messagebox.showerror("ERROR","Belum ada data.")
            return

        stat = Counter([x[0] for x in data])

        plt.figure()
        plt.bar(list(stat.keys()), list(stat.values()))
        plt.title("Statistik Kendaraan")
        plt.xlabel("Jenis")
        plt.ylabel("Jumlah Transaksi")
        plt.tight_layout()
        plt.show()


# ================= RUN =========================
if __name__ == "__main__":
    # [GUI - MAIN WINDOW]
    root = tk.Tk()
    app = PajakGUI(root)
    root.mainloop()