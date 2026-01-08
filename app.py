from flask import Flask, render_template, request

app = Flask(__name__)

def fmt(x, ndigits=None):
    """
    Format angka untuk tampilan:
    - 4.0 -> '4'
    - 3.5 -> '3.5'
    - hasil bisa dibulatkan dengan ndigits
    """
    if ndigits is not None:
        x = round(x, ndigits)
    if isinstance(x, (int, float)) and float(x).is_integer():
        return str(int(x))
    return str(x)

def hitung_mm2(interarrival_min: float, service_min: float) -> dict:
    """
    Hitung parameter antrian M/M/2 sesuai rumus pada tugas:
    λ  = 1 / interarrival
    μ  = 1 / service
    ρ  = λ / (2μ)
    W  = 1 / (μ - λ/2)
    Wq = λ^2 / (2μ(μ - λ/2))
    """
    # ===== Validasi input =====
    if interarrival_min is None or service_min is None:
        raise ValueError("Input tidak boleh kosong.")
    if interarrival_min <= 0 or service_min <= 0:
        raise ValueError("Input harus bernilai positif (> 0).")

    # ===== Langkah 1: λ =====
    lam = 1.0 / interarrival_min  # pelanggan/menit

    # ===== Langkah 2: μ =====
    mu = 1.0 / service_min        # pelanggan/menit (per loket)

    # ===== Langkah 3: ρ =====
    dua_mu = 2.0 * mu
    rho = lam / dua_mu

    # ===== Langkah 4: W =====
    lam_per_2 = lam / 2.0
    denom_w = mu - lam_per_2
    if denom_w <= 0:
        raise ValueError("Sistem tidak stabil: (μ - λ/2) harus > 0. Coba perbesar waktu pelayanan? (atau perbesar interarrival).")

    W = 1.0 / denom_w  # menit

    # ===== Langkah 5: Wq =====
    lam_sq = lam ** 2
    denom_wq = (2.0 * mu) * denom_w
    Wq = lam_sq / denom_wq  # menit

    # ===== Langkah-langkah untuk ditampilkan di web (rumus -> substitusi -> hasil) =====
    pembulatan = 4  # konsisten untuk hasil
    langkah = [
    {
        "judul": "Langkah 1 — Hitung λ (laju kedatangan)",
        "rumus": "λ = 1 / (waktu antar kedatangan)",
        "substitusi_lines": [
            "λ = 1 / (waktu antar kedatangan)",
            f"λ = 1 / {fmt(interarrival_min)}",
            f"λ = {fmt(lam, pembulatan)}",
        ],
        "hasil": lam,
    },
    {
        "judul": "Langkah 2 — Hitung μ (laju pelayanan per loket)",
        "rumus": "μ = 1 / (waktu pelayanan)",
        "substitusi_lines": [
            "μ = 1 / (waktu pelayanan)",
            f"μ = 1 / {fmt(service_min)}",
            f"μ = {fmt(mu, pembulatan)}",
        ],
        "hasil": mu,
    },
    {
        "judul": "Langkah 3 — Hitung ρ (utilisasi)",
        "rumus": "ρ = λ / (2μ)",
        "substitusi_lines": [
            "ρ = λ / (2μ)",
            f"ρ = {fmt(lam, pembulatan)} / (2 × {fmt(mu, pembulatan)})",
            f"ρ = {fmt(lam, pembulatan)} / {fmt(2*mu, pembulatan)}",
            f"ρ = {fmt(rho, pembulatan)}",
        ],
        "hasil": rho,
    },
    {
        "judul": "Langkah 4 — Hitung W (waktu dalam sistem)",
        "rumus": "W = 1 / (μ - λ/2)",
        "substitusi_lines": [
            "W = 1 / (μ - λ/2)",
            f"W = 1 / ({fmt(mu, pembulatan)} - {fmt(lam, pembulatan)}/2)",
            f"W = 1 / ({fmt(mu, pembulatan)} - {fmt(lam/2, pembulatan)})",
            f"W = 1 / {fmt(mu - lam/2, pembulatan)}",
            f"W = {fmt(W, pembulatan)}",
        ],
        "hasil": W,
    },
    {
        "judul": "Langkah 5 — Hitung Wq (waktu tunggu antrian)",
        "rumus": "Wq = λ² / (2μ(μ - λ/2))",
        "substitusi_lines": [
            "Wq = λ² / (2μ(μ - λ/2))",
            f"Wq = {fmt(lam**2, pembulatan)} / ({fmt(2*mu, pembulatan)} × {fmt(mu - lam/2, pembulatan)})",
            f"Wq = {fmt(lam**2, pembulatan)} / {fmt((2*mu)*(mu - lam/2), pembulatan)}",
            f"Wq = {fmt(Wq, pembulatan)}",
        ],
        "hasil": Wq,
        },
]
    return {
        "input": {"interarrival_min": interarrival_min, "service_min": service_min},
        "hasil": {"lambda": lam, "mu": mu, "rho": rho, "W": W, "Wq": Wq},
        "langkah": langkah,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            interarrival_str = request.form.get("interarrival_min", "").strip()
            service_str = request.form.get("service_min", "").strip()

            if interarrival_str == "" or service_str == "":
                raise ValueError("Kolom input tidak boleh kosong.")

            interarrival = float(interarrival_str)
            service = float(service_str)

            data = hitung_mm2(interarrival, service)

            # pembulatan tampilan (biar rapih di web)
            pembulatan = 4
            return render_template(
                "result.html",
                data=data,
                pembulatan=4,
                fmt=fmt
            )

        except ValueError as e:
            # Balik ke halaman input dengan pesan error
            return render_template("index.html", error=str(e),
                                   interarrival_min=request.form.get("interarrival_min", ""),
                                   service_min=request.form.get("service_min", ""))
        except Exception:
            return render_template("index.html", error="Terjadi error tidak terduga. Coba input angka yang valid.",
                                   interarrival_min=request.form.get("interarrival_min", ""),
                                   service_min=request.form.get("service_min", ""))

    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)  