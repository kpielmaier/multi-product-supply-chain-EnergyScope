import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from Colors import colors_elasticity

# =====================================================
# Global Style (MATCHES Pareto plots)
# =====================================================
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,               # <<< MATCH Pareto plot font
})

# Legend names (same formatting as Pareto graphs)
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# =====================================================
# Paths
# =====================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Match the directory naming of your Pareto script
data_root = os.path.join(project_root, "DataNormalPrice")
save_dir  = os.path.join(project_root, "ResultsNormalPrice", "Figures", "Price")

os.makedirs(save_dir, exist_ok=True)

# Zero-emission folders
cases = {
    "demand_fixed": "demand_fixed_eps_0.00",
    "elast_2_5pct": "elast_2_5pct_eps_0.00",
    "elast_5pct":   "elast_5pct_eps_0.00",
    "elast_10pct":  "elast_10pct_eps_0.00",
}

# =====================================================
# Plot setup
# =====================================================
plt.figure(figsize=(10, 6))
ymax = 0

# =====================================================
# Process elasticity cases
# =====================================================
for tag, folder in cases.items():

    data_dir = os.path.join(data_root, folder)
    price_path = os.path.join(data_dir, "price.csv")

    if not os.path.exists(price_path):
        print(f"[WARNING] Missing price.csv for {tag}: {price_path}")
        continue

    df = pd.read_csv(price_path)
    df["price_€_per_MWh"] = df["price_M€_per_GWh"] * 1000

    # Detect node
    node_ref = df["n"].unique()[0]

    # Electricity-only
    df_elec = df[(df["p"] == "ELECTRICITY") & (df["n"] == node_ref)].copy()
    if df_elec.empty:
        continue

    # Weighted hourly average
    df_elec["weighted"] = df_elec["price_€_per_MWh"] * df_elec["mult"]
    price_avg = (
        df_elec.groupby("h")
        .apply(lambda g: g["weighted"].sum() / g["mult"].sum(), include_groups=False)
        .reset_index(name="price_€_per_MWh")
    )

    # Plot
    plt.plot(
        price_avg["h"],
        price_avg["price_€_per_MWh"],
        linewidth=2,
        marker="o",
        label=legend_names.get(tag, tag),          # <<< SAME legend style
        color=colors_elasticity.get(tag, "gray")   # <<< SAME color map
    )

    ymax = max(ymax, price_avg["price_€_per_MWh"].max())

# =====================================================
# Formatting
# =====================================================
plt.xlabel("Hour")
plt.ylabel("Average Electricity Price [€/MWh]")

plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))
plt.ylim(0, ymax * 1.05)

plt.grid(True)
plt.legend(fontsize=16)        # <<< MATCH Pareto style
plt.tight_layout()

# =====================================================
# Save to updated directory
# =====================================================
save_path = os.path.join(save_dir, "Price_Average_ZeroEmissions.pdf")
plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close()

print("Saved plot to:")
print(" ", save_path)
