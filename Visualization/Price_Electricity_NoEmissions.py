import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from Colors import colors_elasticity   # uses your elasticity color map

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# =====================================================
# Paths
# =====================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

base_dir = os.path.join(project_root, "DataNormalPrice")

# Zero-emission epsilon folder names for each elasticity
cases = {
    "demand_fixed": "demand_fixed_eps_0.00",
    "elast_2_5pct": "elast_2_5pct_eps_0.00",
    "elast_5pct":   "elast_5pct_eps_0.00",
    "elast_10pct":  "elast_10pct_eps_0.00",
}

# Legend names
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

figures_dir = os.path.join(project_root, "Results", "Figures", "Price")
os.makedirs(figures_dir, exist_ok=True)

# =====================================================
# Loop over typical days
# =====================================================

# Load a sample file to identify typical days and node
sample_case = list(cases.values())[0]
sample_price_path = os.path.join(base_dir, sample_case, "price.csv")
sample_price = pd.read_csv(sample_price_path)

typical_days = sorted(sample_price["td"].unique())
node_ref = sample_price["n"].unique()[0]

for td in typical_days:

    plt.figure(figsize=(10, 6))
    ymax = 0

    for label, folder in cases.items():

        data_dir = os.path.join(base_dir, folder)
        price_path = os.path.join(data_dir, "price.csv")

        if not os.path.exists(price_path):
            print(f"[WARNING] Missing price.csv for {label}: {price_path}")
            continue

        # Load price data
        price = pd.read_csv(price_path)
        price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3

        # Keep only electricity
        df_elec_td = price[
            (price["p"] == "ELECTRICITY") &
            (price["n"] == node_ref) &
            (price["td"] == td)
        ].copy()

        if df_elec_td.empty:
            continue

        EPS = 1e-6
        df_elec_td["price_€_per_MWh"] = df_elec_td["price_€_per_MWh"].mask(
            df_elec_td["price_€_per_MWh"].abs() < EPS, 0
        )

        # Plot
        plt.plot(
            df_elec_td["h"],
            df_elec_td["price_€_per_MWh"],
            linewidth=2,
            marker="o",
            label=legend_names.get(label, label),  # <<< clean legend
            color=colors_elasticity.get(label, "gray")
        )

        ymax = max(ymax, df_elec_td["price_€_per_MWh"].max())

    # Formatting
    plt.xlabel("Hour")
    plt.ylabel("Electricity Price [€/MWh]")

    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))
    plt.ylim(0, ymax * 1.05)

    plt.grid(True)
    plt.legend(fontsize=16)
    plt.tight_layout()

    # Save
    save_path = os.path.join(figures_dir, f"Price_Electricity_TD{td}_ZeroEmissions.pdf")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved:", save_path)
