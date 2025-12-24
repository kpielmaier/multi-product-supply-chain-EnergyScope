import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Matplotlib configuration
# ---------------------------------------------------------

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

LW = 2

# ---------------------------------------------------------
# Given parameters
# ---------------------------------------------------------

a_p = np.array([8000, 400, 200], float)
b_p = np.array([80, 40, 20], float)
D_p = np.array([95, 5, 10], float)

n_seg = len(a_p)

# ---------------------------------------------------------
# Build stacked PWL inverse demand
# ---------------------------------------------------------

x_offset = 0.0
x_all, y_all = [], []

for k in range(n_seg):
    a = a_p[k]
    b = b_p[k]
    dseg = D_p[k]

    d_local = np.linspace(0, dseg, 300)
    p_local = a - b * d_local

    # Segment curve
    x_all.append(x_offset + d_local)
    y_all.append(p_local)

    # Vertical jump to next segment
    if k < n_seg - 1:
        x_vert = np.array([x_offset + dseg, x_offset + dseg])
        y_vert = np.array([p_local[-1], a_p[k + 1]])

        x_all.append(x_vert)
        y_all.append(y_vert)

    x_offset += dseg

x = np.concatenate(x_all)
y = np.concatenate(y_all)

# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 6))

ax.plot(x, y, lw=LW, color="tab:blue")

# Segment boundaries
x_bounds = np.concatenate(([0.0], np.cumsum(D_p)))
for xb in x_bounds:
    ax.axvline(xb, color="black", lw=LW)

# ---------------------------------------------------------
# Symbolic x-axis: d_seg labels
# ---------------------------------------------------------

x_centers = [
    0.5 * (x_bounds[k] + x_bounds[k + 1])
    for k in range(n_seg)
]

ax.set_xticks(x_centers)
ax.set_xticklabels(
    [rf"$d_{{\mathrm{{seg}}, {k+1}}}$" for k in range(n_seg)]
)

# ---------------------------------------------------------
# Symbolic y-axis: a_k labels
# ---------------------------------------------------------

ax.set_yticks(a_p)
ax.set_yticklabels(
    [rf"$a_{k+1}$" for k in range(n_seg)]
)

# ---------------------------------------------------------
# Formatting
# ---------------------------------------------------------

ax.set_xlabel("Demand")
ax.set_ylabel("Price / marginal utility")
ax.grid(True)

ax.set_xlim(0, x_bounds[-1] * 1.02)
ax.set_ylim(0, a_p.max() * 1.05)

plt.tight_layout()
plt.show()
