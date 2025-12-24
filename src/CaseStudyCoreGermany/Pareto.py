import os
import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))
dat_file = os.path.join(script_dir, "CaseStudy.dat")
case_script = os.path.join(script_dir, "CaseStudy.py")
data_dir = os.path.join(script_dir, "Data")
output_dir  = os.path.join(script_dir, "Results", "Figures", "Pareto")
os.makedirs(output_dir, exist_ok=True)

def set_epsilon(eps_value, enable=True):
    with open(dat_file, "r") as f:
        lines = f.readlines()

    with open(dat_file, "w") as f:
        for line in lines:
            if line.strip().startswith("param use_epsilon"):
                f.write(f"param use_epsilon := {1 if enable else 0};\n")
            elif line.strip().startswith("param epsilon_value"):
                f.write(f"param epsilon_value := {eps_value};\n")
            else:
                f.write(line)

def set_elasticity(eps):
    # Important: epsilon must be disabled before changing elasticity
    set_epsilon(1e12, enable=False)

    with open(dat_file, "r") as f:
        lines = f.readlines()

    with open(dat_file, "w") as f:
        for line in lines:
            if line.strip().startswith("param elasticity"):
                if eps == "HARD":
                    f.write("param elasticity := -0.02;\n")
                else:
                    f.write(f"param elasticity := {eps};\n")
            elif line.strip().startswith("param fix_demand"):
                f.write("param fix_demand := 1;\n" if eps == "HARD" else "param fix_demand := 0;\n")
            else:
                f.write(line)

# def run_model():
#     subprocess.run(["python", case_script], check=True)

def run_model_with_folder(folder_name):
    folder_path = os.path.join(data_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    subprocess.run(["python", case_script, folder_path], check=True)
    return folder_path

# def get_results():
#     fname = os.path.join(data_dir, "last_run.json")
#     if not os.path.exists(fname):
#         raise RuntimeError("Results not found — model infeasible or crashed.")
#     with open(fname, "r") as f:
#         return json.load(f)

def get_results(folder):
    fname = os.path.join(folder, "last_run.json")
    if not os.path.exists(fname):
        raise RuntimeError("Results not found — model infeasible or crashed.")
    with open(fname, "r") as f:
        return json.load(f)

elasticities = {
    -0.10: "elast_10pct",
    -0.05: "elast_5pct",
    -0.025: "elast_2_5pct",
    "HARD": "demand_fixed"
}

N_POINTS = 5
all_fronts = {}

for eps, eps_tag in elasticities.items():
    print(f"\n=== ELASTICITY {eps_tag} ===")
    all_fronts[eps_tag] = []

    set_elasticity(eps)

    # Anchor 1
    print("Running anchor: max social welfare (high emissions)")
    set_epsilon(1e12, enable=False)
    folder = f"{eps_tag}_eps_NONE"
    folder_path = run_model_with_folder(folder)
    anchor_maxSW = get_results(folder_path)
    gwp_high = anchor_maxSW["TotalGWP"]

    anchor_maxSW["epsilon"] = None
    anchor_maxSW["elasticity_tag"] = eps_tag
    all_fronts[eps_tag].append(anchor_maxSW)

    # Anchor 2
    print("Running anchor: min emissions (low social welfare)")
    set_epsilon(0.0, enable=True)
    folder = f"{eps_tag}_eps_{0.0:.2f}"
    folder_path = run_model_with_folder(folder)
    anchor_minGWP = get_results(folder_path)
    gwp_low = anchor_minGWP["TotalGWP"]

    anchor_minGWP["epsilon"] = 0.0
    anchor_minGWP["elasticity_tag"] = eps_tag
    all_fronts[eps_tag].append(anchor_minGWP)


    epsilons = np.linspace(gwp_low, gwp_high, N_POINTS)[1:-1]

    for e in epsilons:
        print(f"  ε = {e:.1f}")
        set_epsilon(float(e), enable=True)
        folder = f"{eps_tag}_eps_{e:.2f}"
        folder_path = run_model_with_folder(folder)
        try:
            r = get_results(folder_path)
        except:
            print(f"    Infeasible for ε = {e:.1f}")
            continue
        r["epsilon"] = float(e)
        r["elasticity_tag"] = eps_tag
        all_fronts[eps_tag].append(r)

    all_fronts[eps_tag] = sorted(all_fronts[eps_tag], key=lambda p: p["TotalGWP"])

    with open(os.path.join(output_dir, f"pareto_SW_vs_GWP_{eps_tag}.json"), "w") as f:
        json.dump(all_fronts[eps_tag], f, indent=4)
