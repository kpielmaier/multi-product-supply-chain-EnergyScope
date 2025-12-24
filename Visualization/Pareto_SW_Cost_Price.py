import os
import json
import matplotlib.pyplot as plt
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# DIRECTORIES FOR HIGH + LOW PRICE SCENARIOS
# ============================================================
pareto_high = os.path.join(script_dir, "..", "ResultsHighPrice", "Figures", "Pareto")
pareto_low  = os.path.join(script_dir, "..", "ResultsLowPrice",  "Figures", "Pareto")

data_high = os.path.join(script_dir, "..", "DataHighPrice")
data_low  = os.path.join(script_dir, "..", "DataLowPrice")

elasticity_files = {
    "elast_10pct": "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct": "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# LOAD JSONs (same code as before)
# ============================================================
def load_jsons(pareto_dir):
    all_fronts = {}
    for eps_tag, filename in elasticity_files.items():
        fullpath = os.path.join(pareto_dir, filename)

        if not os.path.exists(fullpath):
            print(f"[WARNING] File not found: {fullpath}")
            continue

        with open(fullpath, "r") as f:
            all_fronts[eps_tag] = json.load(f)

    return all_fronts

# ============================================================
# CALCULATE AVERAGE PRICE
# ============================================================
def compute_avg_price(folder_path):
    price_file = os.path.join(folder_path, "price.csv")
    if not os.path.exists(price_file):
        return None
    
    df = pd.read_csv(price_file)
    df = df[df["p"] == "ELECTRICITY"]
    if df.empty:
        return None

    df["price_€_per_MWh"] = df["price_M€_per_GWh"] * 1e3
    df["weight"] = df["mult"] * df["t_op"]
    
    avg_price = (df["price_€_per_MWh"] * df["weight"]).sum() / df["weight"].sum()
    return float(avg_price)

# ============================================================
# FOLDER NAMING EXACTLY LIKE ORIGINAL SCRIPT
# ============================================================
def folder_from_point(pt):
    eps_tag = pt["elasticity_tag"]
    
    if pt["epsilon"] is None:
        eps_string = "NONE"
    else:
        eps_string = f"{pt['epsilon']:.2f}"
    
    return f"{eps_tag}_eps_{eps_string}"


# ============================================================
# FUNCTION TO GENERATE THE 3-PLOT FIGURE (High or Low)
# ============================================================
def make_full_pareto_figure(all_fronts, data_root, output_path, title_suffix):

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 6), sharex=True)

    # ===== LEFT PLOT: SW vs GWP =====
    for eps_tag, pts in all_fronts.items():
        if eps_tag == "demand_fixed":
            continue
        gwp = [p["TotalGWP"] for p in pts]
        sw  = [p["SocialWelfare"] for p in pts]
        ax1.plot(gwp, sw, marker='o', label=eps_tag)

    ax1.set_title(f"Social Welfare vs GWP ({title_suffix})")
    ax1.set_xlabel("Total GWP [ktCO₂/year]")
    ax1.set_ylabel("Social Welfare [M€/year]")
    ax1.grid(True)
    ax1.legend()

    # ===== MIDDLE PLOT: Total Cost vs GWP =====
    for eps_tag, pts in all_fronts.items():
        gwp  = [p["TotalGWP"] for p in pts]
        cost = [p["TotalCost"] for p in pts]
        ax2.plot(gwp, cost, marker='x', linestyle='--', label=eps_tag)

    ax2.set_title(f"Total Cost vs GWP ({title_suffix})")
    ax2.set_xlabel("Total GWP [ktCO₂/year]")
    ax2.set_ylabel("Total Cost [M€/year]")
    ax2.grid(True)
    ax2.legend()

    # ===== RIGHT PLOT: Average Price vs GWP =====
    for eps_tag, pts in all_fronts.items():
        gwp_list = []
        price_list = []
        
        for pt in pts:
            folder_name = folder_from_point(pt)
            folder_path = os.path.join(data_root, folder_name)
            
            avg_price = compute_avg_price(folder_path)
            if avg_price is None:
                continue
            
            gwp_list.append(pt["TotalGWP"])
            price_list.append(avg_price)

        ax3.plot(gwp_list, price_list, marker='s', linestyle='-', label=eps_tag)

    ax3.set_ylim(None, 57)
    ax3.set_title(f"Avg Annual Electricity Price vs GWP ({title_suffix})")
    ax3.set_xlabel("Total GWP [ktCO₂/year]")
    ax3.set_ylabel("Avg Electricity Price [€/MWh]")
    ax3.grid(True)
    ax3.legend()

    # Save figure
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=250)
    plt.close()

    print(f"Saved: {output_path}")


# ============================================================
# RUN FOR BOTH HIGH & LOW SCENARIOS
# ============================================================
fronts_high = load_jsons(pareto_high)
fronts_low  = load_jsons(pareto_low)

make_full_pareto_figure(
    fronts_high,
    data_high,
    os.path.join(pareto_high, "Pareto_SW_Cost_Price_High.png"),
    "High Price Scenario"
)

make_full_pareto_figure(
    fronts_low,
    data_low,
    os.path.join(pareto_low, "Pareto_SW_Cost_Price_Low.png"),
    "Low Price Scenario"
)
