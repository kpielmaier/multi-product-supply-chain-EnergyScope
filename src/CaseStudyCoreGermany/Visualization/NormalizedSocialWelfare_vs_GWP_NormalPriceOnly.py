import os
import json
import matplotlib.pyplot as plt

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# ============================================================
# DIRECTORIES
# ============================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
pareto_normal = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# COLORS (from Colors.py)
# ============================================================
colors_elasticity = {
    "demand_fixed": "#000000",
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}

# ============================================================
# CLEAN LEGEND LABELS  (matching the price plot script)
# ============================================================
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# ============================================================
# LOAD JSON FILES
# ============================================================
def load_pareto_jsons(folder):
    result = {}
    for tag, fname in elasticity_files.items():
        path = os.path.join(folder, fname)
        if not os.path.exists(path):
            print(f"[WARNING] Missing: {path}")
            continue
        with open(path, "r") as fh:
            result[tag] = json.load(fh)
    return result

fronts_normal = load_pareto_jsons(pareto_normal)

# ============================================================
# NORMALIZATION HELPERS
# ============================================================
def get_unconstrained_sw(points):
    """Return the maximum SW in this elasticity case."""
    return max(p["SocialWelfare"] for p in points)

def normalize_sw(points):
    sw0 = get_unconstrained_sw(points)
    return [p["SocialWelfare"] / sw0 for p in points], sw0

# ============================================================
# PLOT: NORMAL PRICE ONLY
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

for eps_tag, pts in fronts_normal.items():

    color = colors_elasticity.get(eps_tag, "#000000")
    label = legend_names.get(eps_tag, eps_tag)

    sw_norm, sw0 = normalize_sw(pts)
    gwp = [p["TotalGWP"] for p in pts]

    ax.plot(
        gwp, sw_norm,
        marker='o',
        linestyle='-',
        color=color,
        label=label
    )

# ============================================================
# AESTHETICS
# ============================================================
ax.set_xlabel("Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Normalized Social Welfare [-]")
ax.grid(True)
ax.legend(fontsize=16)

plt.tight_layout()

# ============================================================
# SAVE FIGURE
# ============================================================
save_path = os.path.join(pareto_normal, "NormalizedSW_vs_GWP_NormalPriceOnly.pdf")
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=250)
plt.close()

print("Saved Normal Price only plot to:")
print(" ", save_path)
