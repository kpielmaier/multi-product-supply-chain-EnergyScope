import os
import json
import matplotlib.pyplot as plt
from Colors import colors_elasticity   # <<< IMPORT YOUR COLOR MAP

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

script_dir = os.path.dirname(os.path.abspath(__file__))

# === HIGH AND LOW PRICE DIRECTORIES ===
pareto_high = os.path.join(script_dir, "..", "ResultsHighPrice", "Figures", "Pareto")
pareto_low  = os.path.join(script_dir, "..", "ResultsLowPrice",  "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# CLEAN LEGEND LABELS
# ============================================================
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# ============================================================
# Load JSON helper
# ============================================================
def load_pareto_jsons(folder):
    out = {}
    for tag, fname in elasticity_files.items():
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            with open(path, "r") as fh:
                out[tag] = json.load(fh)
        else:
            print(f"[WARNING] Missing: {path}")
    return out

fronts_high = load_pareto_jsons(pareto_high)
fronts_low  = load_pareto_jsons(pareto_low)

# Gray override ONLY for low-price fixed-demand curve
low_price_fixed_color = "gray"

# ============================================================
# PLOT
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

# -------------------------
# HIGH PRICE (solid + circle)
# -------------------------
for tag, pts in fronts_high.items():
    gwp  = [p["TotalGWP"]  for p in pts]
    cost = [p["TotalCost"] for p in pts]

    color = colors_elasticity.get(tag, "#000000")  # from Colors.py
    label = f"{legend_names.get(tag, tag)} (High)"

    ax.plot(
        gwp, cost,
        marker="o",
        linestyle="-",
        linewidth=2,
        color=color,
        label=label
    )

# -------------------------
# LOW PRICE (dashed + cross)
# -------------------------
for tag, pts in fronts_low.items():
    gwp  = [p["TotalGWP"]  for p in pts]
    cost = [p["TotalCost"] for p in pts]

    # Gray only for fixed demand (Low)
    if tag == "demand_fixed":
        color = low_price_fixed_color
    else:
        color = colors_elasticity[tag]  # SAME COLORS as High-price case

    label = f"{legend_names.get(tag, tag)} (Low)"

    ax.plot(
        gwp, cost,
        marker="x",
        linestyle="--",
        linewidth=2,
        color=color,
        label=label
    )

# ============================================================
# AESTHETICS
# ============================================================
ax.set_xlabel("Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Total Cost [M€/year]")
ax.grid(True)
ax.legend(fontsize=14)

plt.tight_layout()

# Save output in both scenario folders
save_high = os.path.join(pareto_high, "TotalCost_vs_GWP_Combined.pdf")
save_low  = os.path.join(pareto_low,  "TotalCost_vs_GWP_Combined.pdf")

plt.savefig(save_high, dpi=250, bbox_inches="tight")
plt.savefig(save_low,  dpi=250, bbox_inches="tight")
plt.close()

print("Saved TotalCost–GWP combined figure to:")
print("  ", save_high)
print("  ", save_low)
