# Multi-Product Supply Chain Market Reformulation of EnergyScope

## Overview
This repository contains the implementation of a **coordinated market-clearing reformulation of the EnergyScope energy system model**, integrating a **spatio-temporal multi-product supply chain (SC) framework** to analyze stakeholder interaction, demand elasticity, and endogenous price formation in multi-sector energy systems.

Instead of assuming a central planner that minimizes total system cost under fixed demand, the model represents **producers, conversion technologies, storage units, and consumers as independent, profit-seeking stakeholders**. These stakeholders interact through supply and demand bids and are coordinated by an independent system operator that clears the market by maximizing social welfare.

The framework preserves the economic properties of competitive market equilibrium and enables explicit analysis of price formation in highly renewable, decarbonized energy systems.

---

## Key Features
- Reformulation of EnergyScope as a **coordinated market-clearing optimization**
- **Spatio-temporal multi-product supply chain** representation of energy systems
- Explicit modeling of **profit-seeking stakeholders**
- **Elastic consumer demand** using a piecewise-linear approximation of log–log demand curves
- **Endogenous price formation** via dual variables of nodal balance constraints
- Computationally efficient formulation suitable for long-term system planning
- Application to a **2050 German electricity and heating system case study**

---

## Methodology
The model builds on the multi-product supply chain framework for coordinated markets and integrates it into the EnergyScope modeling environment.

Key methodological components include:
- A market-clearing problem that maximizes **social welfare** rather than minimizing total system cost
- Stakeholder bids based on short-run marginal costs (supply side) and willingness to pay (demand side)
- A **spatio-temporal graph** that captures storage, intertemporal coupling, and typical-day representations
- Transition from a linear program to a **quadratic program** when elastic demand is enabled, while maintaining tractable solve times

When demand is fixed, the market formulation collapses to the standard EnergyScope central-planner solution. Stakeholder interaction and price-responsive behavior emerge only once demand elasticity is introduced.

---

## Demand Modeling
Consumer demand is modeled using several representations, including:
- Fixed (perfectly inelastic) demand
- Inelastic demand up to a value-of-lost-load (VOLL)
- Elastic demand via a **piecewise-linear approximation of a log–log demand curve**

The elastic formulation allows consumers to respond to price signals while preserving quadratic structure in the objective function. This enables endogenous price formation and realistic stakeholder behavior without sacrificing computational efficiency.

---

## Case Study
The framework is applied to a **single-node representation of Germany’s coupled electricity and heating system in 2050**.

The case study investigates:
- The impact of demand elasticity on investment and operational decisions
- Endogenous electricity price formation under varying emission constraints
- The role of flexible demand in reducing zero-price hours and limiting price spikes
- System behavior in scenarios with high shares of variable renewable energy

Results show that demand elasticity stabilizes prices and mitigates extreme price events in highly renewable systems.

---

## Technologies and Tools
- Optimization framework: Linear and quadratic programming
- Modeling language: AMPL
- Solver: Gurobi
- Energy system model: EnergyScope
- Data: Derived from PyPSA-Eur workflows adapted for EnergyScope

---

## Project Context
This repository accompanies the semester project:

**“Multi-Product Supply Chain Optimization for Energy Systems”**  
Zürich, December 2025

The full methodological description, mathematical formulation, and results are documented in the project report :contentReference[oaicite:0]{index=0}.

---

## Notes
- This repository is intended for **research, modeling, and academic demonstration purposes**
- Some data preprocessing and scenario generation scripts may be external to this repository
- The implementation focuses on clarity and methodological consistency rather than production deployment

---

## Citation
If you use or reference this work, please cite the accompanying project report.

---

## Author
Konstantin Pielmaier
