#!/usr/bin/env bash
# A5 shaper-sim -- full reproducible pipeline (LTspice batch + Python analysis).
# Run from chips-board/shaper-cr200-cr210/sim/ :  bash scripts/run_all.sh
set -e
LT="C:/Users/darro/AppData/Local/Programs/ADI/LTspice/LTspice.exe"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

echo "[1/5] regenerate Cremat .subckt wrappers from the official model .asc files"
"$LT" -netlist "cremat-models/CR-200/CR-200-1us-R2.1.asc"
"$LT" -netlist "cremat-models/CR-210/CR-210-R0.asc"
python scripts/make_subckts.py

echo "[2/5] M1: CR-200-1us single-event response"
"$LT" -b -Run decks/m1_cr200.cir
python scripts/analyze_m1.py

echo "[3/5] M2: CR-200 -> CR-210 BLR pulse train"
"$LT" -b -Run decks/m2_blr.cir
python scripts/analyze_m2.py

echo "[4/5] behavioral cross-check (CR-RC^4)"
python scripts/behavioral_crosscheck.py

echo "[5/5] done. Plots in plots/, FOM JSON in data/."
