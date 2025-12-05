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


# [MODUL 5 - SUBCLASS - INHERITANCE]
class Kendaraan(KendaraanDasar):
    def __init__(self, nomor_polisi, jenis, bbnkb,
                 pajak_pokok, opsen_pokok,
                 swdkllj, bulan_terlambat):
        super().__init__(nomor_polisi, jenis)
        self.bbnkb = float(bbnkb)
        self.pajak_pokok = float(pajak_pokok)
        self.opsen_pokok = float(opsen_pokok)
        self.swdkllj = float(swdkllj)
        self.bulan_terlambat = int(bulan_terlambat)


# ================= LOGIC SERVICE ==================
# [MODUL 4 - METHOD & RETURN]
class PajakService:
    def __init__(self, kendaraan: Kendaraan):
        self.kendaraan = kendaraan

    def hitung_denda(self):
        return 0.02 * self.kendaraan.pajak_pokok * max(0, self.kendaraan.bulan_terlambat)

    def hitung_total(self):
        return (
            self.kendaraan.bbnkb +
            self.kendaraan.pajak_pokok +
            self.kendaraan.opsen_pokok +
            self.kendaraan.swdkllj +
            self.hitung_denda()
        )


# [MODUL 4 - METHOD]
# [MODUL 2 - IF]
class Pembayaran:
    def __init__(self, total):
        self.total = float(total)

    def proses(self, uang):
        if uang < self.total:
            return None
        return uang - self.total


# ================= GUI APPLICATION ==================
# [MODUL 8 - GUI TKINTER]
class PajakGUI:

    # [MODUL 4 - METHOD CLASS]
    def __init__(self, root):
        self.root = root
        root.title("Sistem Pembayaran Pajak Kendaraan")
        root.geometry("1200x700")
        root.configure(bg="#1E1E2E")

        self.setup_style()

        # [MODUL 1 - VARIABEL]
        self.conn = sqlite3.connect("pajak.db")
        self.create_table()

        self.build_layout()

        # ✅ AUTO LOAD DATA RIWAYAT SAAT APLIKASI DIBUKA
        self.tampilkan_riwayat()

    # ================= STYLE ===================
    def setup_style(self):
        try:
            style = ttkthemes.ThemedStyle(self.root)
            style.set_theme("equilux")
            style.configure("Title.TLabel",
                            font=("Segoe UI", 20, "bold"),
                            foreground="#00D4AA")
        except:
            pass

    # ================= DATABASE =================
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

    # ================= LAYOUT ==================
    # [MODUL 8]
    def build_layout(self):
        header = ttk.Label(
            self.root,
            text="💳 SISTEM PEMBAYARAN PAJAK KENDARAAN",
            style="Title.TLabel"
        )
        header.pack(pady=15)

        container = tk.Frame(self.root, bg="#1E1E2E")
        container.pack(fill="both", expand=True)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)

        self.build_form(container)
        self.build_output(container)


    # ================= FORM =====================
    # [MODUL 1 - VARIABEL]
    # [MODUL 3 - LOOP]
    def build_form(self, parent):
        form = ttk.Labelframe(parent, text="INPUT KENDARAAN", padding=15)
        form.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.entries = {}
        fields = [
            ("Nomor Polisi","nomor"),
            ("Jenis Kendaraan","jenis"),
            ("BBNKB","bbnkb"),
            ("Pajak Pokok","pajak"),
            ("Opsen Pokok","opsen"),
            ("SWDKLLJ","swdkllj"),
            ("Bulan Terlambat","bulan"),
            ("Uang Bayar","uang")
        ]

        for i,(label,key) in enumerate(fields):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky="w",pady=6)
            entry = ttk.Entry(form)
            entry.grid(row=i,column=1,padx=6,pady=6)
            self.entries[key] = entry

        ttk.Button(form,
                   text="✅ PROSES",
                   command=self.proses_pembayaran).grid(columnspan=2,pady=12)

        ttk.Button(form,
                   text="📤 EXPORT PDF",
                   command=self.konfirmasi_export).grid(columnspan=2,sticky="ew")

        ttk.Button(form,
                   text="📊 STATISTIK",
                   command=self.tampilkan_statistik).grid(columnspan=2,sticky="ew",pady=5)


    # ================= OUTPUT ===================
    def build_output(self, parent):
        out = ttk.Labelframe(parent, text="OUTPUT & RIWAYAT", padding=15)
        out.grid(row=0,column=1,sticky="nsew",padx=15,pady=15)

        self.tabs = ttk.Notebook(out)
        self.tabs.pack(fill="both",expand=True)

        # ---- TAB STRUK ----
        self.text_area = tk.Text(
            self.tabs,
            bg="#020617",
            fg="white",
            font=("Consolas",11)
        )
        self.tabs.add(self.text_area, text="🧾 STRUK")

        # ---- TAB RIWAYAT ----
        self.tree = ttk.Treeview(
            self.tabs,
            columns=("tanggal","nomor","jenis","total"),
            show="headings"
        )

        self.tree.heading("tanggal", text="Tanggal")
        self.tree.heading("nomor", text="Nomor Polisi")
        self.tree.heading("jenis", text="Jenis")
        self.tree.heading("total", text="Total")

        self.tabs.add(self.tree, text="📑 RIWAYAT")


    # ================= PROSES ==================
    # [MODUL 2 - IF]
    def proses_pembayaran(self):
        try:
            nomor = self.entries["nomor"].get()
            jenis = self.entries["jenis"].get()

            bbnkb = float(self.entries["bbnkb"].get())
            pajak = float(self.entries["pajak"].get())
            opsen = float(self.entries["opsen"].get())
            swdkllj = float(self.entries["swdkllj"].get())
            bulan = int(self.entries["bulan"].get())
            uang = float(self.entries["uang"].get())
        except:
            messagebox.showerror("ERROR", "Input tidak valid.")
            return

        kendaraan = Kendaraan(nomor,jenis,bbnkb,pajak,opsen,swdkllj,bulan)

        pajakService = PajakService(kendaraan)
        total = pajakService.hitung_total()
        denda = pajakService.hitung_denda()

        bayar = Pembayaran(total)
        kembalian = bayar.proses(uang)

        if kembalian is None:
            messagebox.showerror("ERROR","Uang tidak cukup.")
            return

        self.conn.execute("""
            INSERT INTO pembayaran
            (nomor_polisi,jenis,total,denda,kembalian)
            VALUES (?,?,?,?,?)
        """,(nomor,jenis,total,denda,kembalian))

        self.conn.commit()

        self.last=(kendaraan,total,denda,kembalian)

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.text_area.delete(1.0,tk.END)
        self.text_area.insert(
            tk.END,
f"""
=========== STRUK ============
Tanggal   : {now}
Nomor     : {nomor}
Jenis     : {jenis}

BBNKB     : {int(bbnkb)}
Pajak     : {int(pajak)}
Opsen     : {int(opsen)}
SWDKLLJ   : {int(swdkllj)}
Denda     : {int(denda)}
-----------------------------
TOTAL     : {int(total)}
KEMBALI   : {int(kembalian)}
=============================
"""
        )

        # ✅ PINDAH OTOMATIS KE TAB STRUK
        self.tabs.select(0)

        # ✅ AUTO REFRESH RIWAYAT
        self.tampilkan_riwayat()

        for e in self.entries.values():
            e.delete(0, tk.END)


    # ================= RIWAYAT ==================
    # [MODUL 3 - LOOP]
    def tampilkan_riwayat(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        data = self.conn.execute("""
            SELECT tanggal,nomor_polisi,jenis,total
            FROM pembayaran ORDER BY tanggal DESC
        """).fetchall()

        for r in data:
            self.tree.insert("", "end",
                             values=(r[0], r[1], r[2], int(r[3])))


    # ================= EXPORT ===================
    # [MODUL 4]
    def konfirmasi_export(self):
        if not hasattr(self,"last"):
            messagebox.showerror("ERROR","Belum ada struk.")
            return

        if messagebox.askyesno("Konfirmasi","Export struk ke PDF?"):
            self.export_pdf()

    def export_pdf(self):
        kendaraan,total,denda,kembalian = self.last

        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"struk_{kendaraan.nomor_polisi}.pdf"
        )

        if not file:
            return

        c = canvas.Canvas(file,pagesize=letter)
        y = 750

        data=[
            "===== STRUK PAJAK =====",
            f"Nomor Polisi: {kendaraan.nomor_polisi}",
            f"Jenis: {kendaraan.jenis}",
            "",
            f"BBNKB   : {int(kendaraan.bbnkb)}",
            f"Pajak   : {int(kendaraan.pajak_pokok)}",
            f"Opsen   : {int(kendaraan.opsen_pokok)}",
            f"SWDKLLJ : {int(kendaraan.swdkllj)}",
            f"Denda   : {int(denda)}",
            "",
            f"TOTAL   : {int(total)}",
            f"KEMBALI : {int(kembalian)}"
        ]

        for line in data:
            c.drawString(100,y,line)
            y -= 18

        c.save()
        messagebox.showinfo("SUKSES","PDF berhasil dibuat!")


    # ================= STATISTIK =================
    # [MODUL 2 - IF]
    def tampilkan_statistik(self):
        data = self.conn.execute(
            "SELECT jenis FROM pembayaran"
        ).fetchall()

        if not data:
            messagebox.showerror("ERROR","Belum ada data.")
            return

        stat = Counter([x[0] for x in data])

        plt.figure()
        plt.bar(list(stat.keys()),list(stat.values()))
        plt.title("STATISTIK JENIS KENDARAAN")
        plt.xlabel("Jenis")
        plt.ylabel("Jumlah")
        plt.tight_layout()
        plt.show()


# ================= RUN PROGRAM =================
# [MODUL 8 - MAIN WINDOW]
if __name__ == "__main__":
    root = tk.Tk()
    app = PajakGUI(root)
    root.mainloop()