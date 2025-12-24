import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from Colors import colors_end_use_type

# -------------------------------------------------------------
# Paths
# -------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"DataLowPrice\demand_fixed_eps_NONE")
figures_dir = os.path.join(project_root, "Results", "Figures", "Price")
os.makedirs(figures_dir, exist_ok=True)

# -------------------------------------------------------------
# Load data
# -------------------------------------------------------------
price = pd.read_csv(os.path.join(data_dir, "price.csv"))
price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3
EPS = 1e-6
price["price_€_per_MWh"] = price["price_€_per_MWh"].mask(price["price_€_per_MWh"].abs() < EPS, 0)


node_ref = price["n"].unique()[0]

# Load end-use list
end_uses_types = pd.read_csv(os.path.join(data_dir, "end_uses_types.csv"))["END_USES_TYPES"].tolist()

# -------------------------------------------------------------
# ELECTRICITY FILTER (change condition if needed)
# keep only end-uses containing "ELEC"
# -------------------------------------------------------------
electricity_euts = [e for e in end_uses_types if "ELEC" in e.upper()]

if not electricity_euts:
    raise ValueError("No electricity end-use found. Please adjust the filter condition.")

end_uses_types = electricity_euts
print("Electricity end-uses used:", end_uses_types)

# -------------------------------------------------------------
# 1. Average hourly electricity price across typical days
# -------------------------------------------------------------
plt.figure(figsize=(10, 6))
ymax = 0

for eut in end_uses_types:
    df_eut = price[(price["p"] == eut) & (price["n"] == node_ref)].copy()
    if df_eut.empty:
        continue

    df_eut["weighted_price"] = df_eut["price_€_per_MWh"] * df_eut["mult"]

    price_avg = (
        df_eut.groupby("h")
        .apply(lambda g: g["weighted_price"].sum() / g["mult"].sum(), include_groups=False)
        .reset_index(name="price_€_per_MWh")
    )
    price_avg["price_€_per_MWh"] = price_avg["price_€_per_MWh"].mask(price_avg["price_€_per_MWh"].abs() < EPS, 0)

    plt.plot(
        price_avg["h"],
        price_avg["price_€_per_MWh"],
        marker="o",
        linewidth=2,
        color=colors_end_use_type.get(eut, "gray"),
        label=eut
    )

    ymax = max(ymax, price_avg["price_€_per_MWh"].max())

plt.title(f"Average Hourly Electricity Price (Node {node_ref})", fontsize=13)
plt.xlabel("Hour")
plt.ylabel("Average Price [€/MWh]")
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))

plt.ylim(0, ymax * 1.05)
plt.grid(True)
plt.legend(title="Electricity End-Use", fontsize=9)
plt.tight_layout()

save_path = os.path.join(figures_dir, "Price_Average_Electricity.png")
plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close()

print("Saved:", save_path)


# -------------------------------------------------------------
# 2. Price per Typical Day (TD) for Electricity
# -------------------------------------------------------------
for td in sorted(price["td"].unique()):
    plt.figure(figsize=(10, 6))

    for eut in end_uses_types:
        df_eut_td = price[
            (price["p"] == eut) &
            (price["n"] == node_ref) &
            (price["td"] == td)
        ].copy()

        df_eut_td["price_€_per_MWh"] = df_eut_td["price_€_per_MWh"].mask(df_eut_td["price_€_per_MWh"].abs() < EPS, 0)

        if not df_eut_td.empty:
            plt.plot(
                df_eut_td["h"],
                df_eut_td["price_€_per_MWh"],
                marker="o",
                linewidth=2,
                color=colors_end_use_type.get(eut, "gray"),
                label=eut
            )

    plt.title(f"Electricity Price (Node {node_ref}, Typical Day {td})", fontsize=13)
    plt.xlabel("Hour")
    plt.ylabel("Price [€/MWh]")
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))

    price_filtered = price[
        (price["n"] == node_ref) &
        (price["td"] == td) &
        (price["p"].isin(end_uses_types))
    ]
    ymax = price_filtered["price_€_per_MWh"].max()
    if ymax == 0 or pd.isna(ymax):
        ymax = 1  # fallback to 1 €/MWh
    plt.ylim(0, ymax * 1.05)

    plt.grid(True)
    plt.legend(title="Electricity End-Use", fontsize=9)
    plt.tight_layout()

    save_path = os.path.join(figures_dir, f"Price_Electricity_TD{td}.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved:", save_path)
