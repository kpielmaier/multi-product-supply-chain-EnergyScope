import os
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# GLOBAL STYLE — MATCHES OTHER FIGURES
# ============================================================
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 24,
})

# ============================================================
# SETTINGS
# ============================================================
BASE = "DataNormalPrice"

SCENARIOS = {
    "a) zero emissions": "elast_5pct_eps_0.00",
    "b) unconstrained emissions": "elast_5pct_eps_NONE",
}

RENEWABLES = {"RES_WIND", "RES_SOLAR", "RES_HYDRO", "RES_GEO"}

ALL_RESOURCES = {
    "ELECTRICITY","LFO","GAS","WOOD","WET_BIOMASS","COAL","URANIUM",
    "WASTE","H2","AMMONIA","RES_WIND","RES_SOLAR","RES_HYDRO","RES_GEO"
}

NON_RENEWABLES = ALL_RESOURCES - RENEWABLES

# ============================================================
# PROCESS SCENARIOS
# ============================================================
def compute_shares(path):
    df = pd.read_csv(path)
    totals = df.groupby("st")["val"].sum()

    renewable_supply = sum(totals.get(r, 0) for r in RENEWABLES)
    nonrenewable_supply = totals.sum() - renewable_supply
    return renewable_supply, nonrenewable_supply


# Collect data
results = {}
for label, folder in SCENARIOS.items():
    file_path = os.path.join(BASE, folder, "s_vals.csv")
    r, nr = compute_shares(file_path)
    results[label] = (r, nr)


# ============================================================
# PLOT — Two Pie Charts Positioned Manually
# ============================================================
fig = plt.figure(figsize=(14, 6))

# Position axes manually: [left, bottom, width, height]
ax1 = fig.add_axes([0.15, 0.20, 0.38, 0.70])   # left pie
ax2 = fig.add_axes([0.47, 0.20, 0.38, 0.70])   # right pie

labels = ["Renewable Supply", "Non-renewable Supply"]
colors = ["#66bb6a", "#d32f2f"]

axes = [ax1, ax2]

for ax, (scenario, (ren, non)) in zip(axes, results.items()):

    ax.pie(
        [ren, non],
        labels=None,
        colors=colors,
        startangle=90,
        autopct="%.1f%%",
        pctdistance=0.65,
        textprops={"fontsize": 24, "color": "white", "weight": "bold"},
    )

    ax.text(
        0.5, 0, scenario,
        ha="center", va="center",
        fontsize=24,
        transform=ax.transAxes
    )

# Shared legend centered under both pies
fig.legend(
    labels,
    loc="center left",
    fontsize=24,
    ncol=1,
    frameon=False,
    bbox_to_anchor=(0.8, 0.5)
)

# ============================================================
# SAVE
# ============================================================
out_path = os.path.join(BASE, "SupplyPie.pdf")
plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close()

print("Saved plot to:", out_path)
