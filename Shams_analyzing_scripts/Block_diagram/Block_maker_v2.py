# Regenerate diagram v10:
# - Tighten horizontal spacing by ~20% (gaps, inter-section spacing)
# - Keep the halved left-column→J240 gap from v9 unless otherwise noted
# - Ensure PATT section is drawn FIRST so left-column sub-blocks (Power Block, BBB, RS-232, T660, Attenuation Control) are visible
# - Preserve clean margins; no overlaps; HPFs remain inside PATT; power trunk left of PATT boundary

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.lines import Line2D


def add_section(ax, xy, wh, label, fc, ec="#999999", lw=1.25, label_size=16, zorder=0):  # label_size+1
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder)
    ax.add_patch(rect)
    ax.text(x + w/2, y + 0.35, label, va="bottom", ha="center",
            fontsize=label_size, fontweight="bold", zorder=zorder+1)
    return rect

def add_box(ax, xy, wh, text, fc="#FFFFFF", ec="#333333", lw=1.4, fontsize=12, ha="center", zorder=5):  # fontsize+1
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
        ax.text(mid[0], mid[1]+0.25, text, fontsize=11, fontweight="bold", ha="center", va="bottom", color=color, zorder=zorder+1)  # fontsize+1



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

# Tighten global horizontal gaps by ~20%
box_w     = 2.1
gap       = 0.8     # 20% smaller than 1.0
col_to_j_gap = 1.3  # keep the halved separation from v9

# Compute chain x's
x_j     = col_x + col_w + col_to_j_gap
x_fixed = x_j + box_w + gap
x_prog  = x_fixed + box_w + gap
x_hpf   = x_prog + box_w + gap

# Compute PATT width before drawing (so it sits behind boxes)
patt_width = (x_hpf + box_w + right_margin) - patt_left
patt = add_section(ax, (patt_left, patt_top_y), (patt_width, patt_height), "PATT CHASSIS", fc="#EAF7EA", zorder=0)

# Left-column sub-blocks (explicitly drawn after PATT so they are visible)
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

# Draw per-channel chain
j, fixa, proga, hpf = {}, {}, {}, {}
for r in rows:
    y = r["y"]
    ch = r["ch"]
    j[ch]    = add_box(ax, (x_j,    y), (box_w, 1.0), f"J240-1\nPulser {ch}")
    fixa[ch] = add_box(ax, (x_fixed,y), (box_w, 1.0), f"Fixed Atten\n3 dB {ch}")
    proga[ch]= add_box(ax, (x_prog, y), (box_w, 1.0), f"Programmable\nAttenuator {ch}")
    hpf[ch]  = add_box(ax, (x_hpf,  y), (box_w, 1.0), f"High-Pass\nFilter {ch}")

# Right-side sections with 20% tighter spacing
sig_gap  = 1.44  # 1.8 * 0.8
recv_gap = 0.64  # 0.8 * 0.8
sig_left = patt_left + patt_width + sig_gap -1.2
sig  = add_section(ax, (sig_left, 3.1), (5.4, 8.7), "SIGNAL CHAIN", fc="#EDE7F6", zorder=0)
recv_left = sig_left + 5.4 + recv_gap -0.4
recv = add_section(ax, (recv_left, 3.1), (4.8, 8.7), "RECEIVER", fc="#FFF3CD", zorder=0)

# IGLU and FLOWER blocks
x_iglu_left = sig_left + 0.6
x_flow = recv_left + 0.6
iglu, flow = {}, {}
for r in rows:
    y = r["y"]
    ch = r["ch"]
    iglu[ch] = add_box(ax, (x_iglu_left, y), (3.2, 1.0), f"IGLU-DRAB\n({ch})")
    flow[ch] = add_box(ax, (x_flow, y), (3.8, 1.0), f"FLOWER ({ch})")

# Connections
# Ethernet server->switch->BBB
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
elbow(ax, [(fg.get_x()+fg.get_width(), fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.2, fg.get_y()+0.55),
           (ext.get_x()+ext.get_width()-0.2, t660_box.get_y()+t660_box.get_height()/2),
           (t660_box.get_x(), t660_box.get_y()+t660_box.get_height()/2)], color="#d62728")

# Power PSU->Power Block
elbow(ax, [(ps.get_x()+ps.get_width(), ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-4.5, ps.get_y()+0.55),
           (ext.get_x()+ext.get_width()-4.5, pb_box.get_y()+0.5),
           (pb_box.get_x(), pb_box.get_y()+0.5)], color="#9467bd", ls="--")

# Power trunk left of PATT edge
trunk_x = patt_left + 0.3
elbow(ax, [(pb_box.get_x()+pb_box.get_width()/2, pb_box.get_y()),
           (pb_box.get_x()+pb_box.get_width()/2, pb_box.get_y()-0.2),
           (trunk_x, pb_box.get_y()-0.2),
           (trunk_x, atten_ctrl_box.get_y()+atten_ctrl_box.get_height()+0.2)], color="#9467bd", ls="--", arrow_at_end=False)
for tgt in [bbb_box, rs_box, t660_box, atten_ctrl_box]:
    elbow(ax, [(trunk_x, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height()+0.2),
               (tgt.get_x()+tgt.get_width()/2, tgt.get_y()+tgt.get_height())], color="#9467bd", ls="--")

# T660 -> J240 triggers
for ch in ["ch3","ch2","ch1","ch0"]:
    y_mid = j[ch].get_y()+0.5
    elbow(ax, [(t660_box.get_x()+t660_box.get_width(), y_mid),
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

# Atten control bus -> programmable attenuators
ctrl_trunk_x = x_prog - 0.5
targets_ctrl = [(x_prog, proga[ch].get_y()+0.5) for ch in ["ch3","ch2","ch1","ch0"]]
bus_to_targets(ax, start_xy=(atten_ctrl_box.get_x()+atten_ctrl_box.get_width(), atten_ctrl_box.get_y()+0.5),
               trunk_x=ctrl_trunk_x, targets=targets_ctrl, color="#2ca02c", lw=1.6, ls="-")

# Legend & Title
legend_elements = [
    Line2D([0], [0], color="#1f77b4", lw=2, label="Ethernet / Network"),
    Line2D([0], [0], color="#2ca02c", lw=2, label="Control (RS-232 / Board)"),
    Line2D([0], [0], color="#d62728", lw=2, label="Triggers"),
    Line2D([0], [0], color="#000000", lw=2, label="Analog Signal"),
    Line2D([0], [0], color="#9467bd", lw=2, linestyle="--", label="Power")
]
ax.legend(handles=legend_elements, loc="lower center", ncol=5, frameon=False, fontsize=12, bbox_to_anchor=(0.5, 0.01))

ax.text(19.0, 13.6, "PATT system block diagram", ha="center", va="center", fontsize=18)

png_path = "PATT_Block_Diagram_v12.png"

plt.savefig(png_path, dpi=300, bbox_inches="tight")

