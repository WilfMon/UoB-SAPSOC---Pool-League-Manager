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