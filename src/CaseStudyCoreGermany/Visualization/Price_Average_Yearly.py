import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"Data")

price = pd.read_csv(os.path.join(data_dir, "price.csv"))

price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3

price["weight"] = price["mult"] * price["t_op"]

annual_avg = (
    price
    .groupby("p")
    .apply(lambda g: (g["price_€_per_MWh"] * g["weight"]).sum() / g["weight"].sum())
    .reset_index(name="annual_average_price_€/MWh")
)

print(annual_avg)
