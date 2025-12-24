import os
import json
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

# === HIGH / LOW / NORMAL PRICE DIRECTORIES ===
pareto_high   = os.path.join(script_dir, "..", "ResultsHighPrice",   "Figures", "Pareto")
pareto_low    = os.path.join(script_dir, "..", "ResultsLowPrice",    "Figures", "Pareto")
pareto_normal = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# === Load JSONs ===
def load_pareto_jsons(folder):
    result = {}
    for tag, f in elasticity_files.items():
        path = os.path.join(folder, f)
        if not os.path.exists(path):
            print(f"[WARNING] Missing: {path}")
            continue
        with open(path, "r") as fh:
            result[tag] = json.load(fh)
    return result

fronts_high   = load_pareto_jsons(pareto_high)
fronts_low    = load_pareto_jsons(pareto_low)
fronts_normal = load_pareto_jsons(pareto_normal)

# === Color map for elasticities ===
elasticity_colors = {}
available_colors = plt.cm.tab10.colors  # stable fixed palette

i = 0
for key in elasticity_files:
    if key != "demand_fixed":
        elasticity_colors[key] = available_colors[i]
        i += 1

# Special colors for demand_fixed
color_high_fixed   = "black"
color_low_fixed    = "gray"
color_normal_fixed = "lightgray"

# === Combined plot: High + Low + Normal ===
fig, ax = plt.subplots(figsize=(10, 6))

# ----- HIGH PRICE (solid, circles) -----
for eps_tag, pts in fronts_high.items():
    gwp  = [p["TotalGWP"] for p in pts]
    cost = [p["TotalCost"] for p in pts]

    color = elasticity_colors.get(eps_tag, "black")
    if eps_tag == "demand_fixed":
        color = color_high_fixed

    ax.plot(
        gwp, cost,
        marker='o',
        linestyle='-',
        color=color,
        label=f"{eps_tag} (High)"
    )

# ----- LOW PRICE (dashed, crosses) -----
for eps_tag, pts in fronts_low.items():
    gwp  = [p["TotalGWP"] for p in pts]
    cost = [p["TotalCost"] for p in pts]

    color = elasticity_colors.get(eps_tag, "black")
    if eps_tag == "demand_fixed":
        color = color_low_fixed

    ax.plot(
        gwp, cost,
        marker='x',
        linestyle='--',
        color=color,
        label=f"{eps_tag} (Low)"
    )

# ----- NORMAL PRICE (dotted, triangles) -----
for eps_tag, pts in fronts_normal.items():
    gwp  = [p["TotalGWP"] for p in pts]
    cost = [p["TotalCost"] for p in pts]

    color = elasticity_colors.get(eps_tag, "black")
    if eps_tag == "demand_fixed":
        color = color_normal_fixed

    ax.plot(
        gwp, cost,
        marker='^',
        linestyle=':',
        color=color,
        label=f"{eps_tag} (Normal)"
    )

# === Aesthetics ===
ax.set_title("Total Cost vs GWP — High, Low, and Normal Price Scenarios")
ax.set_xlabel("Total GWP [ktCO₂/year]")
ax.set_ylabel("Total Cost [M€/year]")
ax.grid(True)
ax.legend()

# === Save combined figure to all 3 folders ===
save_high   = os.path.join(pareto_high,   "TotalCost_vs_GWP_Combined_WithNormal.png")
save_low    = os.path.join(pareto_low,    "TotalCost_vs_GWP_Combined_WithNormal.png")
save_normal = os.path.join(pareto_normal, "TotalCost_vs_GWP_Combined_WithNormal.png")

for path in [save_high, save_low, save_normal]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=250)

plt.close()

print("Saved combined figure to:")
print(" ", save_high)
print(" ", save_low)
print(" ", save_normal)
