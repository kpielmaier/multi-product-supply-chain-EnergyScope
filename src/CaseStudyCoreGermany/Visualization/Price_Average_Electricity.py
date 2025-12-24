import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from Colors import colors_end_use_type

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"DataNormalPrice\demand_fixed_eps_0.00")
figures_dir = os.path.join(project_root, "Results", "Figures", "Price")
os.makedirs(figures_dir, exist_ok=True)

price = pd.read_csv(os.path.join(data_dir, "price.csv"))
price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3

node_ref = price["n"].unique()[0]
end_uses_types = pd.read_csv(os.path.join(data_dir, "end_uses_types.csv"))["END_USES_TYPES"].tolist()

# Keep only electricity end-uses
end_uses_types = [e for e in end_uses_types if "ELECTRICITY" in e.upper()]

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

    plt.plot(
        price_avg["h"],
        price_avg["price_€_per_MWh"],
        marker="o",
        linewidth=2,
        color=colors_end_use_type.get(eut, "gray"),
        label=eut
    )

    ymax = max(ymax, price_avg["price_€_per_MWh"].max())

plt.title(f"Average Hourly Price by End-Use (Node {node_ref}, Averaged Over Typical Days)", fontsize=13)
plt.xlabel("Hour")
plt.ylabel("Average Price [€/MWh]")
plt.ticklabel_format(style='plain', axis='y')
plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))

plt.ylim(0, ymax * 1.05)
plt.grid(True)
plt.legend(title="End-use Type", loc="best", fontsize=9)
plt.tight_layout()

save_path = os.path.join(figures_dir, "Price_Average.png")
plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close()
