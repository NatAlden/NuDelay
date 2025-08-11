# Add a vertical trigger trunk (red) from T660 to J240s and a purple dashed power bus from Power Block to J240s.
# This is a full runnable cell that reconstructs the diagram (v11) with the requested additions.
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

def add_section(ax, xy, wh, label, fc, ec="#999999", lw=1.25, label_size=17, zorder=0):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder)
    ax.add_patch(rect)
    ax.text(x + w/2, y + 0.35, label, va="bottom", ha="center",
            fontsize=label_size, fontweight="bold", zorder=zorder+1)
    return rect

def add_box(ax, xy, wh, text, fc="#FFFFFF", ec="#333333", lw=1.4, fontsize=14, ha="center", zorder=5):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, va="center", ha=ha, fontsize=fontsize, fontweight="bold", zorder=zorder+1)
    rect.get_x = lambda: x
    rect.get_y = lambda: y
    rect.get_width = lambda: w
    rect.get_height = lambda: h
    return rect

def add_arrow(ax, xy_from, xy_to, text=None, color="#333333", lw=1.6, ls="-", zorder=6):
    arr = FancyArrowPatch(xy_from, xy_to, arrowstyle="-|>", mutation_scale=12,
                          linewidth=lw, linestyle=ls, color=color, zorder=zorder)
    ax.add_patch(arr)
    if text:
        mid = ((xy_from[0]+xy_to[0])/2, (xy_from[1]+xy_to[1])/2)
        ax.text(mid[0], mid[1]+0.25, text, fontsize=13, fontweight="bold", ha="center", va="bottom", color=color, zorder=zorder+1)

def elbow(ax, points, color="#333333", lw=1.6, ls="-", arrow_at_end=True, zorder=6):
    for i in range(len(points)-1):
        x0, y0 = points[i]
        x1, y1 = points[i+1]
        if i < len(points)-2 or not arrow_at_end:
            ax.add_line(Line2D([x0, x1], [y0, y1], color=color, linewidth=lw, linestyle=ls, zorder=zorder))
        else:
            add_arrow(ax, (x0, y0), (x1, y1), color=color, lw=lw, ls=ls, zorder=zorder)

def bus_to_targets(ax, start_xy, trunk_x, targets, color="#2ca02c", lw=1.6, ls="-", zorder=6):
    x0, y0 = start_xy
    ax.add_line(Line2D([x0, trunk_x], [y0, y0], color=color, linewidth=lw, linestyle=ls, zorder=zorder))
    ys = [y for (_, y) in targets]
    y_top, y_bot = max(ys), min(ys)
    ax.add_line(Line2D([trunk_x, trunk_x], [y_bot, y_top], color=color, linewidth=lw, linestyle=ls, zorder=zorder))
    for xt, yt in targets:
        ax.add_patch(Circle((trunk_x, yt), 0.06, color=color, zorder=zorder+1))
        add_arrow(ax, (trunk_x, yt), (xt, yt), color=color, lw=lw, ls=ls, zorder=zorder+1)

# Canvas
fig_w, fig_h = 38, 14
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(0, 38)
ax.set_ylim(0, 14)
ax.axis("off")

# Sections
ext  = add_section(ax, (0.8, 8.4), (8.6, 5.3), "EXTERNAL", fc="#E8F0FE", zorder=0)

# EXTERNAL boxes
ps     = add_box(ax, (1.2, 12.3), (3.4, 1.1), "12 V PSU")
fg     = add_box(ax, (5.2, 12.3), (3.6, 1.1), "Function\nGenerator")
server = add_box(ax, (1.2, 10.5), (3.4, 1.1), "Control\nServer")
net    = add_box(ax, (5.2, 10.5), (3.6, 1.1), "Network /\nSwitch")

# PATT layout
patt_left   = 10.0
patt_top_y  = 0.8
patt_height = 12.6
left_margin  = 0.6
right_margin = 0.6

# Left column x
col_x = patt_left + left_margin
col_w = 3.3

# Global gaps
box_w     = 2.1
gap       = 0.8
col_to_j_gap = 1.3

# Chain x's
x_j     = col_x + col_w + col_to_j_gap
x_fixed = x_j + box_w + gap
x_prog  = x_fixed + box_w + gap
x_hpf   = x_prog + box_w + gap

# PATT section
patt_width = (x_hpf + box_w + right_margin) - patt_left
patt = add_section(ax, (patt_left, patt_top_y), (patt_width, patt_height), "PATT CHASSIS", fc="#EAF7EA", zorder=0)

# Left-column sub-blocks
pb_box        = add_box(ax, (col_x, 11.9), (col_w, 1.0), "Power Block\n(12 V dist + 5 V)")
bbb_box       = add_box(ax, (col_x, 10.2), (col_w, 1.0), "BeagleBone\n(Control Scripts)")
rs_box        = add_box(ax, (col_x, 8.6),  (col_w, 1.0), "RS-232 Board\n(BBB ↔ T660)")
t660_box      = add_box(ax, (col_x, 6.9),  (col_w, 1.0), "T660-1\nDelay/Pulse Gen")
atten_ctrl_box= add_box(ax, (col_x, 5.2),  (col_w, 1.0), "Attenuation\nControl")

# Channel rows
rows = [
    {"y": 10.4, "ch": "ch3"},
    {"y": 8.2,  "ch": "ch2"},
    {"y": 6.0,  "ch": "ch1"},
    {"y": 3.8,  "ch": "ch0"},
]

# Per-channel chain
j, fixa, proga, hpf = {}, {}, {}, {}
for r in rows:
    y = r["y"]
    ch = r["ch"]
    j[ch]    = add_box(ax, (x_j,    y), (box_w, 1.0), f"J240-1\nPulser {ch}")
    fixa[ch] = add_box(ax, (x_fixed,y), (box_w, 1.0), f"Fixed Atten\n3 dB {ch}")
    proga[ch]= add_box(ax, (x_prog, y), (box_w, 1.0), f"Programmable\nAttenuator {ch}")
    hpf[ch]  = add_box(ax, (x_hpf,  y), (box_w, 1.0), f"High-Pass\nFilter {ch}")

# Right-side sections
sig_gap  = 1.44
recv_gap = 0.64
sig_left = patt_left + patt_width + sig_gap - 1.2
sig  = add_section(ax, (sig_left, 3.1), (5.4, 8.7), "SIGNAL CHAIN", fc="#EDE7F6", zorder=0)
recv_left = sig_left + 5.4 + recv_gap - 0.4
recv = add_section(ax, (recv_left, 3.1), (4.8, 8.7), "RECEIVER", fc="#FFF3CD", zorder=0)

# IGLU / FLOWER
x_iglu_left = sig_left + 0.6
x_flow = recv_left + 0.6
iglu, flow = {}, {}
for r in rows:
    y = r["y"]
    ch = r["ch"]
    iglu[ch] = add_box(ax, (x_iglu_left, y), (3.2, 1.0), f"IGLU-DRAB\n({ch})")
    flow[ch] = add_box(ax, (x_flow, y), (3.8, 1.0), f"FLOWER ({ch})")

# Connections
# Ethernet
elbow(ax, [(server.get_x()+server.get_width(), server.get_y()+0.55),
           (net.get_x()-0.3, server.get_y()+0.55),
           (net.get_x()-0.3, net.get_y()+0.55),
           (net.get_x(), net.get_y()+0.55)], color="#1f77b4")
elbow(ax, [(net.get_x()+net.get_width(), net.get_y()+0.55),
           (patt_left-0.6, net.get_y()+0.55),
           (patt_left-0.6, bbb_box.get_y()+0.5),
           (bbb_box.get_x(), bbb_box.get_y()+0.5)], color="#1f77b4")

# RS-232 BBB->RS232->T660
elbow(ax, [(bbb_box.get_x()+bbb_box.get_width()/2, bbb_box.get_y()),
           (bbb_box.get_x()+bbb_box.get_width()/2, rs_box.get_y()+rs_box.get_height()),
           (rs_box.get_x()+rs_box.get_width()/2, rs_box.get_y()+rs_box.get_height()),
           (rs_box.get_x()+rs_box.get_width()/2, rs_box.get_y()),
           (t660_box.get_x()+t660_box.get_width()/2, t660_box.get_y()+t660_box.get_height())], color="#2ca02c")

# External trigger FG->T660
# We keep this short link into the T660 (can be adjusted as needed)
elbow(ax, [(fg.get_x()+fg.get_width(), fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.2, fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.2, t660_box.get_y()+t660_box.get_height()/2),
           (t660_box.get_x(), t660_box.get_y()+t660_box.get_height()/2)], color="#d62728")

# Power: PSU->Power Block (existing)
elbow(ax, [(ps.get_x()+ps.get_width(), ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-4.5, ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-4.5, pb_box.get_y()+0.5),
           (pb_box.get_x(), pb_box.get_y()+0.5)], color="#9467bd", ls="--")

# Power trunk (boards) left of PATT edge (existing)
trunk_x_boards = patt_left + 0.3
elbow(ax, [(pb_box.get_x()+pb_box.get_width()/2, pb_box.get_y()),
           (pb_box.get_x()+pb_box.get_width()/2, pb_box.get_y()-0.2),
           (trunk_x_boards, pb_box.get_y()-0.2),
           (trunk_x_boards, atten_ctrl_box.get_y()+atten_ctrl_box.get_height()+0.2)], color="#9467bd", ls="--", arrow_at_end=False)
for tgt in [bbb_box, rs_box, t660_box, atten_ctrl_box]:
    elbow(ax, [(trunk_x_boards, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height())], color="#9467bd", ls="--")

# ---------- NEW: Trigger vertical trunk from T660 to J240s ----------
trig_trunk_x = t660_box.get_x() + t660_box.get_width() + 0.5  # a bit to the right of T660
t660_mid_y = t660_box.get_y() + t660_box.get_height()/2
# short horizontal from T660 to trunk
elbow(ax, [(t660_box.get_x()+t660_box.get_width(), t660_mid_y),
           (trig_trunk_x,                        t660_mid_y)], color="#d62728")
# vertical trunk covering all channel y's
y_levels = [j[ch].get_y()+0.5 for ch in ["ch0","ch1","ch2","ch3"]]
ax.add_line(Line2D([trig_trunk_x, trig_trunk_x], [min(y_levels), max(y_levels)], color="#d62728", linewidth=1.8))
# branches from trunk to each J240
for ch in ["ch3","ch2","ch1","ch0"]:
    y = j[ch].get_y()+0.5
    add_arrow(ax, (trig_trunk_x, y), (j[ch].get_x(), y), color="#d62728")

# ---------- NEW: Power bus from Power Block to J240s ----------
# start at right side of Power Block, go right then down, then branch to each J240
pb_right = pb_box.get_x() + pb_box.get_width()
pb_mid_y = pb_box.get_y() + 0.5
power_trunk_j_x = x_j - 0.5  # run the vertical bus just left of the J240 column
# horizontal from PB to bus x, then vertical down across all J240 y's
elbow(ax, [(pb_right, pb_mid_y),
           (power_trunk_j_x, pb_mid_y)], color="#9467bd", ls="--")
ax.add_line(Line2D([power_trunk_j_x, power_trunk_j_x], [min(y_levels), max(y_levels)], color="#9467bd", linewidth=1.6, linestyle="--"))
# branch to each J240
for ch in ["ch3","ch2","ch1","ch0"]:
    y = j[ch].get_y()+0.5
    add_arrow(ax, (power_trunk_j_x, y), (j[ch].get_x(), y), color="#9467bd", lw=1.6, ls="--")

# Legend & Title
legend_elements = [
    Line2D([0], [0], color="#1f77b4", lw=2, label="Ethernet / Network"),
    Line2D([0], [0], color="#2ca02c", lw=2, label="Control (RS-232 / Board)"),
    Line2D([0], [0], color="#d62728", lw=2, label="Triggers"),
    Line2D([0], [0], color="#000000", lw=2, label="Analog Signal"),
    Line2D([0], [0], color="#9467bd", lw=2, linestyle="--", label="Power")
]
ax.legend(handles=legend_elements, loc="lower center", ncol=5, frameon=False, fontsize=14, bbox_to_anchor=(0.5, 0.01))

ax.text(19.0, 13.6, "PATT system block diagram", ha="center", va="center", fontsize=21, fontweight="bold")

png_path = "PATT_Block_Diagram_v12.png"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
