import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# --------------------------------------------------------
# 1. Path to your .dat file
# --------------------------------------------------------
dat_path = r"C:\Users\pielm\Desktop\SemesterProject\1_AMPL\CaseStudyCoreGermany\CaseStudyTimeSeries.dat"

# --------------------------------------------------------
# 2. Output folder ("Figures" in current directory)
# --------------------------------------------------------
output_dir = os.path.join(os.getcwd(), "Figures")
os.makedirs(output_dir, exist_ok=True)

# --------------------------------------------------------
# 3. Read the file
# --------------------------------------------------------
with open(dat_path, "r") as f:
    text = f.read()

# --------------------------------------------------------
# 4. Find ALL technologies inside ["TECH",*,*] blocks
# --------------------------------------------------------
tech_list = re.findall(r'\["([^"]+)",\*,\*\]:', text)
tech_list = list(dict.fromkeys(tech_list))  # remove duplicates, keep order

print("Technologies found:", tech_list)

# --------------------------------------------------------
# 5. Function to extract ONE block for a technology
# --------------------------------------------------------
def extract_block(tech_name):
    pattern = rf'\["{tech_name}",\*,\*\]:(.*?)\n(?=\[|;)'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract block for {tech_name}")
    return match.group(1).strip()

# --------------------------------------------------------
# 6. Function to convert a block into a DataFrame
# --------------------------------------------------------
def block_to_df(block):
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    header_line = lines[0].replace(":=", " ").replace(":", " ")
    header_tokens = [tok for tok in header_line.split() if tok.isdigit()]
    col_numbers = list(map(int, header_tokens))

    row_numbers = []
    matrix = []

    for line in lines[1:]:
        parts = line.split()
        if not parts[0].isdigit():
            continue
        row_numbers.append(int(parts[0]))
        matrix.append([float(x) for x in parts[1:1 + len(col_numbers)]])

    df = pd.DataFrame(matrix, index=row_numbers, columns=col_numbers)
    df.index.name = "Hour"
    df.columns.name = "TypicalDay"
    return df

# --------------------------------------------------------
# 7. Loop over technologies and plot heatmaps
# --------------------------------------------------------
for tech in tech_list:

    print(f"\nProcessing {tech}...")

    block = extract_block(tech)
    df = block_to_df(block)

    # ---------------------------------------------------
    # Choose colormap: PV → RED heatmap, others → viridis
    # ---------------------------------------------------
    solar_cmap = "inferno"
    wind_cmap = "viridis"

    if tech.upper() == "PV":
        cmap_choice = solar_cmap
    elif "WIND_ONSHORE" in tech.upper():
        cmap_choice = wind_cmap
    else:
        cmap_choice = "viridis"

    plt.figure(figsize=(10, 6))
    plt.imshow(df.values, aspect='auto', cmap=cmap_choice, origin='lower')
    plt.colorbar(label=f"Capacity Factor {tech}")
    # plt.title(f"Capacity Factor {tech}")
    plt.xlabel("Typical Day")
    plt.ylabel("Hour")
    plt.xticks(ticks=np.arange(len(df.columns)), labels=df.columns)
    plt.yticks(ticks=np.arange(len(df.index)), labels=df.index)
    plt.tight_layout()

    heatmap_path = os.path.join(output_dir, f"{tech}_CF_Heatmap.pdf")
    plt.savefig(heatmap_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved heatmap → {heatmap_path}")

print("\nAll technologies processed successfully!")
