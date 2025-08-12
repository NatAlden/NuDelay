# Simplified block diagram (v13): no outer sections, only inner blocks.
# Layout: T660 (left) -> J240 Pulsers -> Programmable Attenuators -> High-Pass Filter (optional, translucent) -> IGLU-DRAB
# Lines: only Triggers (red) and Analog Signal (black)
# Title: "Simplified block diagram"

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

def add_box(ax, xy, wh, text, fc="#FFFFFF", ec="#333333", lw=1.4, fontsize=12, alpha=1.0):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, va="center", ha="center", fontsize=fontsize)
    return rect

def add_arrow(ax, xy_from, xy_to, color="#333333", lw=1.8, ls="-", ms=12):
    arr = FancyArrowPatch(xy_from, xy_to, arrowstyle="-|>", mutation_scale=ms,
                          linewidth=lw, linestyle=ls, color=color)
    ax.add_patch(arr)

def elbow(ax, points, color="#333333", lw=1.8, ls="-", arrow_at_end=True, ms=12):
    for i in range(len(points)-1):
        x0, y0 = points[i]
        x1, y1 = points[i+1]
        if i < len(points)-2 or not arrow_at_end:
            ax.add_line(Line2D([x0, x1], [y0, y1], color=color, linewidth=lw, linestyle=ls))
        else:
            add_arrow(ax, (x0, y0), (x1, y1), color=color, lw=lw, ls=ls, ms=ms)

# Canvas
fig, ax = plt.subplots(figsize=(24, 8))
ax.set_xlim(0, 24)
ax.set_ylim(0, 12)
ax.axis("off")

# Columns
x_t660 = 1.6
x_j240 = 6.0
x_prog = 10.0
x_hpf  = 14.0
x_iglu = 18.5

box_w = 2.6
box_h = 1.2
row_y = [9.5, 7.0, 4.5, 2.0]  # ch3..ch0

# T660
t660 = add_box(ax, (x_t660, 6.6), (box_w, 1.6), "T660-1\nDelay / Pulse Gen", fontsize=12)

# J240, Programmable Atten, HPF (optional), IGLU-DRAB per channel
j = {}
prog = {}
hpf = {}
iglu = {}

for i, y in enumerate(row_y):
    ch = f"ch{3-i}"
    j[ch]    = add_box(ax, (x_j240, y), (box_w, box_h), f"J240-1\nPulser {ch}")
    prog[ch] = add_box(ax, (x_prog, y), (box_w, box_h), f"Programmable\nAttenuator {ch}")
    # translucent high-pass with "(optional)"
    hpf[ch]  = add_box(ax, (x_hpf, y), (box_w, box_h), "High-Pass Filter\n(optional)", fc="#EDE7F6", alpha=0.35)
    iglu[ch] = add_box(ax, (x_iglu, y), (box_w+0.6, box_h), f"IGLU-DRAB\n({ch})")

# Trigger trunk from T660 to all J240s
trunk_x = x_t660 + box_w + 0.9
t660_mid_y = 6.6 + 0.8  # vertical center of T660
# short horizontal from T660 to trunk
elbow(ax, [(x_t660 + box_w, t660_mid_y),
           (trunk_x,        t660_mid_y)], color="#d62728", lw=2.0)
# vertical trunk spanning all rows
ax.add_line(Line2D([trunk_x, trunk_x], [min([y+box_h/2 for y in row_y]), max([y+box_h/2 for y in row_y])], color="#d62728", linewidth=2.0))
# branches to each J240
for y in row_y:
    ymid = y + box_h/2
    add_arrow(ax, (trunk_x, ymid), (x_j240, ymid), color="#d62728", lw=2.0)

# Analog chain J240 -> Prog Atten -> HPF -> IGLU
for y in row_y:
    ymid = y + box_h/2
    elbow(ax, [(x_j240 + box_w, ymid), (x_prog, ymid)], color="#000000", lw=2.0)
    elbow(ax, [(x_prog + box_w, ymid), (x_hpf, ymid)], color="#000000", lw=2.0)
    elbow(ax, [(x_hpf + box_w, ymid), (x_iglu, ymid)], color="#000000", lw=2.0)

# Legend and title
legend_elements = [
    Line2D([0], [0], color="#d62728", lw=2.2, label="Triggers"),
    Line2D([0], [0], color="#000000", lw=2.2, label="Analog Signal"),
]
ax.legend(handles=legend_elements, loc="lower center", ncol=2, frameon=False, fontsize=12, bbox_to_anchor=(0.5, 0.02))

ax.text(12, 11.1, "Simplified block diagram for the PATT", ha="center", va="center", fontsize=18)

png_path = "Simplified_Block_Diagram_v13.png"
plt.savefig(png_path, dpi=300, bbox_inches="tight")

