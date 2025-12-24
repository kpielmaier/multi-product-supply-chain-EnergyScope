import numpy as np
import matplotlib.pyplot as plt
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
output_dir = os.path.join(project_root, "Results", "Figures", "Demand")
os.makedirs(output_dir, exist_ok=True)

a_paper = np.array([8000, 400, 200], dtype=float)
b_paper = np.array([80, 40, 20], dtype=float)
D_paper = np.array([95, 5, 10], dtype=float)

ref_demand = 100
ref_price = 100

d_pts = [0.0]
p_pts = []
cum = 0.0
for ak, bk, Dk in zip(a_paper, b_paper, D_paper):
    d_local = np.linspace(0, Dk, 100)
    p_local = ak - bk * d_local
    if not p_pts:
        p_pts.append(p_local[0])
    d_pts.extend(list(cum + d_local[1:]))
    p_pts.extend(list(p_local[1:]))
    cum += Dk

cum_limits = np.cumsum(D_paper)
if ref_demand <= cum_limits[0]:
    seg_idx_d = 0
elif ref_demand <= cum_limits[1]:
    seg_idx_d = 1
else:
    seg_idx_d = 2

cum_before = 0 if seg_idx_d == 0 else cum_limits[seg_idx_d - 1]
d_local = ref_demand - cum_before
p_at_ref_d = a_paper[seg_idx_d] - b_paper[seg_idx_d] * d_local
elasticity_ref_d = -1 / b_paper[seg_idx_d] * (p_at_ref_d / ref_demand)

p_bounds = [a_paper[k] - b_paper[k] * D_paper[k] for k in range(len(a_paper))]
if ref_price >= p_bounds[0]:
    seg_idx_p = 0
elif ref_price >= p_bounds[1]:
    seg_idx_p = 1
else:
    seg_idx_p = 2

d_at_ref_p = (a_paper[seg_idx_p] - ref_price) / b_paper[seg_idx_p]
d_at_ref_p += 0 if seg_idx_p == 0 else cum_limits[seg_idx_p - 1]
elasticity_ref_p = -1 / b_paper[seg_idx_p] * (ref_price / d_at_ref_p)

plt.figure(figsize=(7, 5))
plt.plot(d_pts, p_pts, linewidth=2, color="tab:blue", label="Paper PWL Inverse Demand Curve")

plt.axvline(ref_demand, color="gray", linestyle="--", linewidth=1.2, label=f"Ref Demand = {ref_demand} MW")
plt.axhline(ref_price, color="red", linestyle=":", linewidth=1.5, label=f"Ref Price = {ref_price} €/MWh")

plt.text(
    0.2 * max(d_pts), 0.05 * max(p_pts),
    f"ε @ Ref Demand = {elasticity_ref_d:.3f}\nε @ Ref Price = {elasticity_ref_p:.3f}",
    color="black", fontsize=10, bbox=dict(facecolor='white', alpha=0.7)
)

plt.title("Paper PWL Inverse Demand Curve", fontsize=12)
plt.xlabel("Demand [MW]")
plt.ylabel("Price [€/MWh]")
plt.xlim(0, 150)
plt.ylim(0, 1500)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.tight_layout()

paper_save_path = os.path.join(output_dir, "Demand_PAPER.png")
plt.savefig(paper_save_path, dpi=300, bbox_inches="tight")
plt.close()
