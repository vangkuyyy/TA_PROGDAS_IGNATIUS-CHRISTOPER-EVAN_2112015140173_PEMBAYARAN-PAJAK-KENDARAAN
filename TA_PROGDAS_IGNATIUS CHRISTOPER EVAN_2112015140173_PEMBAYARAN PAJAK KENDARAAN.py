import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from collections import Counter
from PIL import Image, ImageTk
import datetime

# ================= DATA MODEL ==================
class KendaraanDasar:
    def __init__(self, nomor_polisi: str, jenis: str):
        self.nomor_polisi = nomor_polisi
        self.jenis = jenis


class Kendaraan(KendaraanDasar):
    def __init__(
        self,
        nomor_polisi,
        jenis,
        bbnkb,
        pajak_pokok,
        opsen_pokok,
        swdkllj,
        bulan_terlambat,
    ):
        super().__init__(nomor_polisi, jenis)
        self.bbnkb = float(bbnkb)
        self.pajak_pokok = float(pajak_pokok)
        self.opsen_pokok = float(opsen_pokok)
        self.swdkllj = float(swdkllj)
        self.bulan_terlambat = int(bulan_terlambat)


class PajakService:
    def __init__(self, kendaraan: Kendaraan):
        self.kendaraan = kendaraan

    def hitung_denda(self) -> float:
        return 0.02 * self.kendaraan.pajak_pokok * max(0, self.kendaraan.bulan_terlambat)

    def hitung_total(self) -> float:
        return (
            self.kendaraan.bbnkb
            + self.kendaraan.pajak_pokok
            + self.kendaraan.opsen_pokok
            + self.kendaraan.swdkllj
            + self.hitung_denda()
        )


class Pembayaran:
    def __init__(self, total: float):
        self.total = float(total)

    def proses(self, uang: float):
        uang = float(uang)
        if uang < self.total:
            return None
        return uang - self.total


# ================= GUI APP =====================
class PajakGUI:
    def __init__(self, root):
        self.root = root
        root.title("Sistem Pembayaran Pajak Kendaraan")
        root.geometry("1200x700")
        root.configure(bg="#1E1E2E")

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.conn = sqlite3.connect("pajak.db")
        self.create_table()

        self.build_layout()

    # ================= DB =====================
    def create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pembayaran(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomor_polisi TEXT,
                jenis TEXT,
                total REAL,
                denda REAL,
                kembalian REAL,
                tanggal TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    # ================= UI =====================
    def build_layout(self):
        header = tk.Label(
            self.root,
            text="💳 SISTEM PEMBAYARAN PAJAK KENDARAAN",
            fg="#00ffcc",
            bg="#1E1E2E",
            font=("Segoe UI", 22, "bold"),
        )
        header.pack(pady=15)

        container = tk.Frame(self.root, bg="#1E1E2E")
        container.pack(fill="both", expand=True)

        self.build_form(container)
        self.build_output(container)

    # ================= FORM INPUT =====================
    def build_form(self, parent):
        form = tk.LabelFrame(
            parent,
            text=" INPUT DATA ",
            bg="#2A2D3A",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        form.pack(side="left", fill="y", padx=10, pady=10)

        self.entries = {}

        fields = [
            ("Nomor Polisi", "nomor"),
            ("Jenis Kendaraan", "jenis"),
            ("BBNKB", "bbnkb"),
            ("Pajak Pokok", "pajak"),
            ("Opsen Pokok", "opsen"),
            ("SWDKLLJ", "swdkllj"),
            ("Bulan Terlambat", "bulan"),
            ("Uang Bayar", "uang"),
        ]

        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, bg="#2A2D3A", fg="white").grid(
                row=i, column=0, sticky="w", pady=5
            )
            ent = ttk.Entry(form, width=26)
            ent.grid(row=i, column=1, pady=5, padx=6)
            self.entries[key] = ent

        ttk.Button(form, text="✅ PROSES PEMBAYARAN", command=self.proses_pembayaran).grid(
            row=len(fields),
            columnspan=2,
            pady=15,
            ipadx=10,
        )

        ttk.Button(form, text="📤 EXPORT PDF", command=self.konfirmasi_export).grid(
            row=len(fields) + 1,
            columnspan=2,
            pady=5,
        )

        ttk.Button(form, text="📊 STATISTIK", command=self.tampilkan_statistik).grid(
            row=len(fields) + 2,
            columnspan=2,
            pady=5,
        )

    # ================= OUTPUT =====================
    def build_output(self, parent):
        out = tk.LabelFrame(
            parent,
            text=" OUTPUT & RIWAYAT ",
            bg="#2A2D3A",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        out.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.tabs = ttk.Notebook(out)
        self.tabs.pack(fill="both", expand=True)

        # ---- STRUK
        self.text_area = tk.Text(
            self.tabs, bg="#020617", fg="white", font=("Consolas", 11)
        )
        self.tabs.add(self.text_area, text="🧾 STRUK")

        # ---- RIWAYAT AUTO
        self.tree = ttk.Treeview(
            self.tabs,
            columns=("tanggal", "nomor", "jenis", "total"),
            show="headings",
        )

        self.tree.heading("tanggal", text="Tanggal")
        self.tree.heading("nomor", text="Nomor Polisi")
        self.tree.heading("jenis", text="Jenis")
        self.tree.heading("total", text="Total Bayar")

        self.tree.column("tanggal", width=170)
        self.tree.column("nomor", width=120)
        self.tree.column("jenis", width=120)
        self.tree.column("total", width=120)

        self.tabs.add(self.tree, text="📑 RIWAYAT")

        self.refresh_history()

    # ================= PROSES =====================
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

            kendaraan = Kendaraan(nomor, jenis, bbnkb, pajak, opsen, swdkllj, bulan)

        except:
            messagebox.showerror("ERROR", "Input data tidak lengkap atau salah.")
            return

        pajak = PajakService(kendaraan)

        total = pajak.hitung_total()
        denda = pajak.hitung_denda()

        bayar = Pembayaran(total)
        kembalian = bayar.proses(uang)

        if kembalian is None:
            messagebox.showerror("ERROR", "Uang tidak cukup!")
            return

        self.conn.execute(
            """
            INSERT INTO pembayaran
            (nomor_polisi,jenis,total,denda,kembalian)
            VALUES (?,?,?,?,?)
            """,
            (kendaraan.nomor_polisi, kendaraan.jenis, total, denda, kembalian),
        )
        self.conn.commit()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(
            tk.END,
            f"""
======= STRUK PAJAK =======
Tanggal      : {now}
Nomor Polisi : {kendaraan.nomor_polisi}
Jenis        : {kendaraan.jenis}

TOTAL PAJAK  : Rp {int(total)}
DENDA        : Rp {int(denda)}
KEMBALIAN    : Rp {int(kembalian)}

==========================
""",
        )

        self.last = (kendaraan, total, denda, kembalian)

        for ent in self.entries.values():
            ent.delete(0, tk.END)

        self.refresh_history()

    # ================= RIWAYAT =====================
    def refresh_history(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        rows = self.conn.execute(
            """
            SELECT tanggal, nomor_polisi, jenis, total
            FROM pembayaran
            ORDER BY tanggal DESC
            """
        ).fetchall()

        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], int(r[3])))

    # ================= EXPORT =====================
    def konfirmasi_export(self):
        if not hasattr(self, "last"):
            messagebox.showerror("ERROR", "Belum ada struk.")
            return

        if messagebox.askyesno("Konfirmasi", "Export struk ke PDF?"):
            self.export_pdf()

    def export_pdf(self):
        kendaraan, total, denda, kembalian = self.last

        file = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")]
        )

        if not file:
            return

        c = canvas.Canvas(file, pagesize=letter)
        y = 750

        lines = [
            "===== STRUK PAJAK =====",
            f"Nomor Polisi : {kendaraan.nomor_polisi}",
            f"Jenis        : {kendaraan.jenis}",
            "",
            f"TOTAL        : Rp {int(total)}",
            f"DENDA        : Rp {int(denda)}",
            f"KEMBALIAN    : Rp {int(kembalian)}",
        ]

        for l in lines:
            c.drawString(100, y, l)
            y -= 22

        c.save()
        messagebox.showinfo("SUKSES", "PDF berhasil dibuat.")

    # ================= STATISTIK =====================
    def tampilkan_statistik(self):
        rows = self.conn.execute(
            """
            SELECT substr(tanggal,1,4) as tahun,
                   SUM(total) as total_pajak
            FROM pembayaran
            GROUP BY tahun
            ORDER BY tahun
            """
        ).fetchall()

        if not rows:
            messagebox.showerror("ERROR", "Belum ada data.")
            return

        tahun = [r[0] for r in rows]
        total = [r[1] for r in rows]

        plt.figure()

        plt.plot(tahun, total, marker="o", linewidth=2)

        info = "Data belum cukup"
        if len(total) >= 2:
            last = total[-1]
            prev = total[-2]
            persen = ((last - prev) / prev) * 100

            if persen > 0:
                info = f"📈 Naik {persen:.2f}%"
            elif persen < 0:
                info = f"📉 Turun {abs(persen):.2f}%"
            else:
                info = "➡️ Stabil"

        plt.title("Tren Pajak Tahunan")
        plt.xlabel("Tahun")
        plt.ylabel("Total Pajak (Rp)")
        plt.grid(True)

        plt.text(
            0.5,
            0.92,
            info,
            transform=plt.gca().transAxes,
            ha="center",
            fontsize=12,
            bbox=dict(boxstyle="round"),
        )

        plt.tight_layout()
        plt.show()

    # ================= EXIT =====================
    def on_closing(self):
        self.conn.commit()
        self.conn.close()
        self.root.destroy()


# ================= RUN APP =====================
if __name__ == "__main__":
    root = tk.Tk()
    app = PajakGUI(root)
    root.mainloop()