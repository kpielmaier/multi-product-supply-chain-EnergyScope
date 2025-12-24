import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Colors import colors_end_use_type

# -----------------------------
# Matplotlib configuration
# -----------------------------
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# -----------------------------
# Paths
# -----------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, "DataNormalPrice", "elast_5pct_eps_0.00")
output_dir = os.path.join(project_root, "Results", "Figures", "Elasticity")
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# Readers
# -----------------------------
def read_param(filename):
    df = pd.read_csv(os.path.join(data_dir, filename))
    df.rename(columns={
        "index0": "k",
        "index1": "ct",
        "index2": "n",
        "index3": "h",
        "index4": "td",
        df.columns[-1]: "val"
    }, inplace=True)
    return {(r.k, r.ct, r.n, r.h, r.td): r.val for r in df.itertuples(index=False)}

def read_simple(filename, col):
    df = pd.read_csv(os.path.join(data_dir, filename))
    df.rename(columns={col: "val"}, inplace=True)
    return {(r.ct, r.n, r.h, r.td): r.val for r in df.itertuples(index=False)}

# -----------------------------
# Load data
# -----------------------------
a = read_param("a.csv")
b = read_param("b.csv")
D = read_param("D.csv")
d_ref = read_simple("d_ref.csv", "d_ref")

cts   = sorted({k[1] for k in a})
nodes = sorted({k[2] for k in a})
hours = sorted({k[3] for k in a})
tds   = sorted({k[4] for k in a})

# Single slice (as in your script)
n  = "GERMANY"
h  = 12
td = 10

# -----------------------------
# PLOTTING TOGGLES
# -----------------------------
PLOT_ONLY_ELECTRICITY = True   # set to False to plot all consumers

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(8, 6))

for ct in cts:
    if PLOT_ONLY_ELECTRICITY and ct != "ELECTRICITY":
        continue
    # Segments must be complete
    segs = sorted(
        k for (k,ct_i,n_i,h_i,td_i) in a
        if (ct_i,n_i,h_i,td_i) == (ct,n,h,td)
    )

    if not segs:
        continue

    # Reference demand
    d0 = d_ref[(ct,n,h,td)]

    # Sanity check: total PWL span must reach 1.1 * d_ref
    Dsum = sum(D[(k,ct,n,h,td)] for k in segs)
    if not np.isclose(Dsum / d0, 1.1, rtol=1e-6):
        raise ValueError(
            f"{ct}: ΣD/d_ref = {Dsum/d0:.6f} (expected 1.1)"
        )

    x_vals = []
    y_vals = []

    cum = 0.0
    for k in segs:
        ak = a[(k,ct,n,h,td)]
        bk = b[(k,ct,n,h,td)]
        Dk = D[(k,ct,n,h,td)]

        dloc = np.linspace(0, Dk, 120)
        dtot = cum + dloc
        ploc = ak - bk * dloc

        mask = dtot > 0
        dtot = dtot[mask]
        ploc = ploc[mask]

        # Absolute elasticity in %
        eps = 100.0 * (ploc / (bk * dtot))

        x_vals.append(dtot / d0)
        y_vals.append(eps)

        cum += Dk

    x = np.concatenate(x_vals)
    y = np.concatenate(y_vals)

    # Keep plotting window
    m = x >= 0.85

    plt.plot(
        x[m],
        y[m],
        linewidth=2,
        color=colors_end_use_type.get(ct, "black"),
        label="Multi-product SC EnergyScope" if PLOT_ONLY_ELECTRICITY else ct
    )

# -----------------------------
# Brown et al. (2025) reference
# -----------------------------
a_p = np.array([8000, 400, 200], float)
b_p = np.array([80, 40, 20], float)
D_p = np.array([95, 5, 10], float)
ref_d = 100.0

x_p, y_p = [], []
cum = 0.0

for ak, bk, Dk in zip(a_p, b_p, D_p):
    dloc = np.linspace(0, Dk, 200)
    dtot = cum + dloc
    ploc = ak - bk * dloc

    mask = dtot > 0
    eps = 100.0 * (ploc[mask] / (bk * dtot[mask]))

    x_p.append(dtot[mask] / ref_d)
    y_p.append(eps)

    cum += Dk

x_p = np.concatenate(x_p)
y_p = np.concatenate(y_p)

plt.plot(
    x_p[x_p >= 0.85],
    y_p[x_p >= 0.85],
    color="black",
    linewidth=2,
    linestyle="--",
    label="Brown et al. (2025)"
)

# -----------------------------
# Final formatting
# -----------------------------
plt.xlabel("Normalized Demand [-]")
plt.ylabel("Elasticity [%]")
plt.xlim(0.85, 1.1)
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    os.path.join(output_dir, "Elasticity.pdf"),
    dpi=300,
    bbox_inches="tight"
)
plt.close()
