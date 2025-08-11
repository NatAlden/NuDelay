# Generate revised diagram v7 per feedback:
# - Single SIGNAL CHAIN and single RECEIVER section
# - Increase spacing so no blocks overlap; HPFs inside PATT CHASSIS with margin
# - EXTERNAL items fully enclosed with more distance to boundaries
# - Power trunk (purple dashed) routed left of PATT CHASSIS edge (no overlap)
# - Remove dead space by tightening canvas while preserving clear spacing

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

def add_section(ax, xy, wh, label, fc, ec="#999999", lw=1.25, label_size=15):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(rect)
    ax.text(x + w/2, y + 0.35, label, va="bottom", ha="center",
            fontsize=label_size, fontweight="bold")
    rect.get_x = lambda: x
    rect.get_y = lambda: y
    rect.get_width = lambda: w
    rect.get_height = lambda: h
    return rect

def add_box(ax, xy, wh, text, fc="#FFFFFF", ec="#333333", lw=1.4, fontsize=11, ha="center"):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, va="center", ha=ha, fontsize=fontsize)
    rect.get_x = lambda: x
    rect.get_y = lambda: y
    rect.get_width = lambda: w
    rect.get_height = lambda: h
    return rect

def add_arrow(ax, xy_from, xy_to, text=None, color="#333333", lw=1.6, ls="-"):
    arr = FancyArrowPatch(xy_from, xy_to, arrowstyle="-|>", mutation_scale=12,
                          linewidth=lw, linestyle=ls, color=color)
    ax.add_patch(arr)
    if text:
        mid = ((xy_from[0]+xy_to[0])/2, (xy_from[1]+xy_to[1])/2)
        ax.text(mid[0], mid[1]+0.25, text, fontsize=10, ha="center", va="bottom", color=color)

def elbow(ax, points, color="#333333", lw=1.6, ls="-", arrow_at_end=True):
    for i in range(len(points)-1):
        x0, y0 = points[i]
        x1, y1 = points[i+1]
        if i < len(points)-2 or not arrow_at_end:
            ax.add_line(Line2D([x0, x1], [y0, y1], color=color, linewidth=lw, linestyle=ls))
        else:
            add_arrow(ax, (x0, y0), (x1, y1), color=color, lw=lw, ls=ls)

def bus_to_targets(ax, start_xy, trunk_x, targets, color="#2ca02c", lw=1.6, ls="-"):
    x0, y0 = start_xy
    ax.add_line(Line2D([x0, trunk_x], [y0, y0], color=color, linewidth=lw, linestyle=ls))
    ys = [y for (_, y) in targets]
    y_top, y_bot = max(ys), min(ys)
    ax.add_line(Line2D([trunk_x, trunk_x], [y_bot, y_top], color=color, linewidth=lw, linestyle=ls))
    for xt, yt in targets:
        ax.add_patch(Circle((trunk_x, yt), 0.06, color=color))
        add_arrow(ax, (trunk_x, yt), (xt, yt), color=color, lw=lw, ls=ls)

# Canvas (moderately wide to avoid dead space but keep clarity)
fig_w, fig_h = 36, 14
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(0, 36)
ax.set_ylim(0, 14)
ax.axis("off")

# Sections
ext  = add_section(ax, (0.8, 8.4), (8.6, 5.3), "EXTERNAL", fc="#E8F0FE")
patt = add_section(ax, (9.8, 0.8), (14.2, 12.6), "PATT CHASSIS", fc="#EAF7EA")
sig  = add_section(ax, (24.6, 3.1), (5.4, 8.4), "SIGNAL CHAIN", fc="#EDE7F6")
recv = add_section(ax, (30.4, 3.1), (4.8, 8.4), "RECEIVER", fc="#FFF3CD")

# External boxes (lowered and spaced with margin)
ps     = add_box(ax, (1.2, 12.4), (3.4, 1.1), "12 V PSU")
fg     = add_box(ax, (5.1, 12.4), (3.7, 1.1), "Function\nGenerator")
server = add_box(ax, (1.2, 10.5), (3.4, 1.1), "Control\nServer")
net    = add_box(ax, (5.1, 10.5), (3.7, 1.1), "Network /\nSwitch")

# PATT left column
col_x = 10.4
col_w = 3.3
power_block = add_box(ax, (col_x, 11.9), (col_w, 1.0), "Power Block\n(12 V dist + 5 V)")
bbb         = add_box(ax, (col_x, 10.2), (col_w, 1.0), "BeagleBone\n(Control Scripts)")
rs232       = add_box(ax, (col_x, 8.6),  (col_w, 1.0), "RS-232 Board\n(BBB ↔ T660)")
t660        = add_box(ax, (col_x, 6.9),  (col_w, 1.0), "T660-1\nDelay/Pulse Gen")
atten_ctrl  = add_box(ax, (col_x, 5.2),  (col_w, 1.0), "Attenuation\nControl")

# PATT per-channel chain (ensure HPFs remain inside PATT with margin)
x_j = 14.2
box_w = 2.1
gap = 1.0
x_fixed = x_j + box_w + gap
x_prog  = x_fixed + box_w + gap
x_hpf   = x_prog + box_w + gap
# Ensure HPF stays inside PATT with margin 0.6
right_margin = 0.6
if x_hpf + box_w > patt.get_x() + patt.get_width() - right_margin:
    shift_left = (x_hpf + box_w) - (patt.get_x() + patt.get_width() - right_margin)
    x_j -= shift_left
    x_fixed -= shift_left
    x_prog -= shift_left
    x_hpf -= shift_left

rows = [
    {"y": 10.4, "ch": "ch3"},
    {"y": 8.2,  "ch": "ch2"},
    {"y": 6.0,  "ch": "ch1"},
    {"y": 3.8,  "ch": "ch0"},
]

j = {}
fixa = {}
proga = {}
hpf = {}
iglu = {}
flow = {}

for r in rows:
    y = r["y"]
    ch = r["ch"]
    j[ch]    = add_box(ax, (x_j,    y), (box_w, 1.0), f"J240-1\nPulser {ch}")
    fixa[ch] = add_box(ax, (x_fixed,y), (box_w, 1.0), f"Fixed Atten\n3 dB {ch}")
    proga[ch]= add_box(ax, (x_prog, y), (box_w, 1.0), f"Programmable\nAttenuator {ch}")
    hpf[ch]  = add_box(ax, (x_hpf,  y), (box_w, 1.0), f"High-Pass\nFilter {ch}")

# Compute large gap between HPF and IGLU (two sub-block widths + gaps)
gap_between =  (box_w + gap-0.8)
x_iglu_left = x_hpf + box_w + gap_between

# Place IGLU inside SIGNAL CHAIN with left margin
iglu_margin = 0.6
if x_iglu_left < sig.get_x() + iglu_margin:
    x_iglu_left = sig.get_x() + iglu_margin

for r in rows:
    y = r["y"]
    ch = r["ch"]
    iglu[ch] = add_box(ax, (x_iglu_left, y), (3.2, 1.0), f"IGLU-DRAB\n({ch})")

# RECEIVER FLOWER boxes (single section)
x_flow = recv.get_x() + 0.6
for r in rows:
    y = r["y"]
    ch = r["ch"]
    flow[ch] = add_box(ax, (x_flow, y), (3.6, 1.0), f"FLOWER ({ch})")

# Connections
# Ethernet server->switch->BBB
elbow(ax, [(server.get_x()+server.get_width(), server.get_y()+0.55),
           (net.get_x()-0.3, server.get_y()+0.55),
           (net.get_x()-0.3, net.get_y()+0.55),
           (net.get_x(), net.get_y()+0.55)], color="#1f77b4")
elbow(ax, [(net.get_x()+net.get_width(), net.get_y()+0.55),
           (patt.get_x()-0.6, net.get_y()+0.55),
           (patt.get_x()-0.6, bbb.get_y()+0.5),
           (bbb.get_x(), bbb.get_y()+0.5)], color="#1f77b4")

# RS-232 BBB->RS232->T660
elbow(ax, [(bbb.get_x()+bbb.get_width()/2, bbb.get_y()),
           (bbb.get_x()+bbb.get_width()/2, rs232.get_y()+rs232.get_height()),
           (rs232.get_x()+rs232.get_width()/2, rs232.get_y()+rs232.get_height()),
           (rs232.get_x()+rs232.get_width()/2, rs232.get_y()),
           (t660.get_x()+t660.get_width()/2, t660.get_y()+t660.get_height())], color="#2ca02c")

# External trigger FG->T660
elbow(ax, [(fg.get_x()+fg.get_width(), fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.5, fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.5, t660.get_y()+t660.get_height()/2),
           (t660.get_x(), t660.get_y()+t660.get_height()/2)], color="#d62728")

# Power PSU->Power Block
elbow(ax, [(ps.get_x()+ps.get_width(), ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.6, ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.6, power_block.get_y()+0.5),
           (power_block.get_x(), power_block.get_y()+0.5)], color="#9467bd", ls="--")

# Power trunk routed left of PATT edge (no overlap)
trunk_x = patt.get_x() - 1.0  # left of PATT edge by 1 unit
elbow(ax, [(power_block.get_x()+power_block.get_width()/2, power_block.get_y()),
           (power_block.get_x()+power_block.get_width()/2, power_block.get_y()-0.6),
           (trunk_x, power_block.get_y()-0.6),
           (trunk_x, atten_ctrl.get_y()+atten_ctrl.get_height()+0.2)], color="#9467bd", ls="--", arrow_at_end=False)
for tgt in [bbb, rs232, t660, atten_ctrl]:
    elbow(ax, [(trunk_x, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height())], color="#9467bd", ls="--")

# T660 -> J240 triggers
for ch in ["ch3","ch2","ch1","ch0"]:
    y_mid = j[ch].get_y()+0.5
    elbow(ax, [(t660.get_x()+t660.get_width(), y_mid),
               (j[ch].get_x(), y_mid)], color="#d62728")

# Analog chain per channel
for ch in ["ch3","ch2","ch1","ch0"]:
    y = j[ch].get_y()+0.5
    elbow(ax, [(j[ch].get_x()+j[ch].get_width(), y),
               (fixa[ch].get_x(), y)], color="#000000")
    elbow(ax, [(fixa[ch].get_x()+fixa[ch].get_width(), y),
               (proga[ch].get_x(), y)], color="#000000")
    elbow(ax, [(proga[ch].get_x()+proga[ch].get_width(), y),
               (hpf[ch].get_x(), y)], color="#000000")
    elbow(ax, [(hpf[ch].get_x()+hpf[ch].get_width(), y),
               (iglu[ch].get_x(), y)], color="#000000")
    elbow(ax, [(iglu[ch].get_x()+iglu[ch].get_width(), y),
               (flow[ch].get_x(), y)], color="#000000")

# Control bus: Atten Control -> programmable attenuators
ctrl_trunk_x = proga["ch3"].get_x() - 0.55
targets_ctrl = [(proga[ch].get_x(), proga[ch].get_y()+0.5) for ch in ["ch3","ch2","ch1","ch0"]]
bus_to_targets(ax, start_xy=(atten_ctrl.get_x()+atten_ctrl.get_width(), atten_ctrl.get_y()+0.5),
               trunk_x=ctrl_trunk_x, targets=targets_ctrl, color="#2ca02c", lw=1.6, ls="-")

# Legend and title
legend_elements = [
    Line2D([0], [0], color="#1f77b4", lw=2, label="Ethernet / Network"),
    Line2D([0], [0], color="#2ca02c", lw=2, label="Control (RS-232 / Board)"),
    Line2D([0], [0], color="#d62728", lw=2, label="Triggers"),
    Line2D([0], [0], color="#000000", lw=2, label="Analog Signal"),
    Line2D([0], [0], color="#9467bd", lw=2, linestyle="--", label="Power")
]
ax.legend(handles=legend_elements, loc="lower center", ncol=5, frameon=False, fontsize=12, bbox_to_anchor=(0.5, 0.01))

ax.text(18.0, 13.6, "PATT system block diagram", ha="center", va="center", fontsize=18)

png_path = "PATT_Block_Diagram_v7.png"

plt.savefig(png_path, dpi=300, bbox_inches="tight")

