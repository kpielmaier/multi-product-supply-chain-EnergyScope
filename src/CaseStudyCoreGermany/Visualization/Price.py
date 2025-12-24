import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from Colors import colors_end_use_type

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"DataNormalPrice\elast_5pct_eps_0.00")
figures_dir = os.path.join(project_root, "Results", "Figures", "Price")
os.makedirs(figures_dir, exist_ok=True)

price = pd.read_csv(os.path.join(data_dir, "price.csv"))
price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3

node_ref = price["n"].unique()[0]
end_uses_types = pd.read_csv(os.path.join(data_dir, "end_uses_types.csv"))["END_USES_TYPES"].tolist()

# -------------------------------------------------------------
# OPTIONAL FILTER: EXCLUDE HEAT_LOW_T_DECEN IF DESIRED

# Uncomment the following line to remove HEAT_LOW_T_DECEN:
end_uses_types = [e for e in end_uses_types if e != "HEAT_LOW_T_DECEN"]
# -------------------------------------------------------------

for td in sorted(price["td"].unique()):
    plt.figure(figsize=(10, 6))
    for eut in end_uses_types:
        df_eut_td = price[(price["p"] == eut) & (price["n"] == node_ref) & (price["td"] == td)]
        if not df_eut_td.empty:
            plt.plot(
                df_eut_td["h"],
                df_eut_td["price_€_per_MWh"],
                marker="o",
                linewidth=2,
                color=colors_end_use_type.get(eut, "gray"),
                label=eut
            )

    plt.title(f"Price Comparison Across End-Uses (Node {node_ref}, Typical Day {td})", fontsize=13)
    plt.xlabel("Hour")
    plt.ylabel("Price [€/MWh]")
    plt.ticklabel_format(style='plain', axis='y')
    plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))

    price_filtered = price[(price["n"] == node_ref) & (price["td"] == td) & (price["p"].isin(end_uses_types))]
    ymax = price_filtered["price_€_per_MWh"].max()
    plt.ylim(0, ymax * 1.05)
    plt.grid(True)
    plt.legend(title="End-use Type", loc="best", fontsize=9)
    plt.tight_layout()

    save_path = os.path.join(figures_dir, f"Price_TD{td}.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    