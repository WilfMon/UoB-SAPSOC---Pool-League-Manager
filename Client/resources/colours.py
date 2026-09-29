# Palette lifted from the SapSoc website's dark-mode CSS variables.
# Old constant names are kept so nothing importing from here breaks.

DARK       = "#080705"  # --paper       deep mahogany / dark wood base (app bg)
PANEL_COL  = "#14120f"  # --paper-dim   secondary dark ledger background (panels)
HEAD       = "#0A1A14"  # --felt-deep   deep night felt (cards / header bar)
LINE       = "#342A22"  # --ledger-line dividers, default button state
TEXT       = "#E8DFCE"  # --ink         warm parchment text
MUTED      = "#C1B39C"  # --ink-soft    soft muted ledger text
ACCENT     = "#D4A04B"  # --brass       titles / section labels
GREEN      = "#0f9763"  # --felt-v-light  win state / positive
RED        = "#DF493B"  # --loss-red    loss state / negative

# Extra site tokens, in case custom_widgets.py / confimation_window.py
# want finer control than the 8 names above give you.
FELT           = "#163C2E"
FELT_LIGHT     = "#225340"
WOOD           = "#4A2E1A"
WOOD_DARK      = "#24150A"
BRASS_LIGHT    = "#ebcd95"
CUE_WHITE      = "#1F1D1C"  # inverted-bg for cards sitting on cards

# match quality colors
QUALITY_COLORS = {
    0: "#153152",
    1: "#214E9A",
    2: "#428AC9",
    3: "#4D8FA9",
    4: "#41966B",
    5: "#A6B94D",
    6: "#C8A640",
    7: "#C6A8D4",
    8: "#673F8A",
    9: "#4B166A",
    10: "#39144C"
}