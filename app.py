
import streamlit as st
import plotly.graph_objects as go
import numpy as np
 
st.set_page_config(page_title="AI Civil Designer", page_icon="⛭", layout="wide")
 
# =========================================================
# PROFESSIONAL THEME (CSS)
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
 
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
 
    .main {
        background-color: #f7f8fa;
    }
 
    h1 {
        font-weight: 700;
        color: #1c2b3a;
        letter-spacing: -0.5px;
    }
 
    h2, h3 {
        font-weight: 600;
        color: #263544;
    }
 
    [data-testid="stSidebar"] {
        background-color: #1c2b3a;
    }
    [data-testid="stSidebar"] * {
        color: #e8ecf1 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label, 
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #a9b8c7 !important;
        font-size: 0.85rem;
        font-weight: 500;
    }
 
    /* Sidebar input fields: dark background instead of washed-out white */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="base-input"],
    [data-testid="stSidebar"] input[type="number"],
    [data-testid="stSidebar"] input {
        background-color: #24384b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3d5568 !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] span,
    [data-testid="stSidebar"] div[data-baseweb="select"] div {
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] button[title="Increment"],
    [data-testid="stSidebar"] button[title="Decrement"] {
        background-color: #2c435a !important;
        border: 1px solid #3d5568 !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] svg {
        fill: #cbd5e1 !important;
    }
 
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e6ea;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #1c2b3a;
        font-weight: 700;
    }
 
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        color: white;
    }
 
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #475569;
    }
 
    div[data-testid="stCaptionContainer"] {
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)
 
# =========================================================
# SOIL DATABASE
# =========================================================
# category: "weak" | "moderate" | "strong"  (typical safe bearing capacity behavior)
SOIL_DB = {
    "Soft Clay":                         {"category": "weak",     "expansive": False, "color": "#8b7355"},
    "Stiff Clay":                        {"category": "moderate", "expansive": False, "color": "#a0784f"},
    "Silty Clay":                        {"category": "weak",     "expansive": False, "color": "#9c8060"},
    "Sandy Clay":                        {"category": "moderate", "expansive": False, "color": "#b08a5a"},
    "Silt":                              {"category": "weak",     "expansive": False, "color": "#c2b280"},
    "Sandy Silt":                        {"category": "moderate", "expansive": False, "color": "#cbbb8c"},
    "Loose Sand":                        {"category": "moderate", "expansive": False, "color": "#e0c98a"},
    "Dense Sand":                        {"category": "strong",   "expansive": False, "color": "#e8d9a0"},
    "Gravel":                            {"category": "strong",   "expansive": False, "color": "#b5b0a5"},
    "Sandy Gravel":                      {"category": "strong",   "expansive": False, "color": "#c4beb0"},
    "Soft Rock":                         {"category": "strong",   "expansive": False, "color": "#8a8a8a"},
    "Hard Rock":                         {"category": "strong",   "expansive": False, "color": "#5c5c5c"},
    "Peat":                              {"category": "weak",     "expansive": False, "color": "#4a3c2a"},
    "Loam":                              {"category": "moderate", "expansive": False, "color": "#7a5c3e"},
    "Black Cotton Soil (Expansive Clay)":{"category": "weak",     "expansive": True,  "color": "#3d3a35"},
    "Laterite":                          {"category": "moderate", "expansive": False, "color": "#a8532f"},
    "Alluvial Soil":                     {"category": "weak",     "expansive": False, "color": "#b39b73"},
    "Loess":                             {"category": "weak",     "expansive": False, "color": "#d4c48a"},
}
 
STRUCT_COLOR = {
    "RC Frame": "#c9c4b8",
    "Shear Wall System": "#7c92a8",
    "Steel Frame": "#9a8168",
}
 
# Rough conceptual construction rates (PKR per sq ft of covered area), by structural system.
# These are order-of-magnitude planning figures, not tender-ready quotes.
RATE_PER_SQFT_PKR = {
    "RC Frame": 3200,
    "Shear Wall System": 3800,
    "Steel Frame": 4200,
}
 
FOUNDATION_EXTRA_PKR_PER_SQFT = {
    "Isolated Footing": 150,
    "Strip Footing": 200,
    "Raft Foundation": 350,
    "Pile Foundation": 700,
}
 
 
def estimate_cost_and_materials(footprint, floors, structural_system, foundation_type):
    covered_area_m2 = sum(dx * dy for (_, _, dx, dy) in footprint)
    covered_area_sqft = covered_area_m2 * 10.7639
    total_area_sqft = covered_area_sqft * floors
 
    rate = RATE_PER_SQFT_PKR[structural_system] + FOUNDATION_EXTRA_PKR_PER_SQFT[foundation_type]
    total_cost_pkr = total_area_sqft * rate
 
    concrete_m3 = covered_area_m2 * floors * 0.16          # rough: slabs+beams+columns per floor
    steel_tonnes = total_area_sqft * 0.0035                # rough: ~3.5 kg/sqft reinforcement
    cement_bags = concrete_m3 * 7                          # rough: ~7 bags/m3 of concrete
 
    return {
        "covered_area_sqft": covered_area_sqft,
        "total_area_sqft": total_area_sqft,
        "rate_per_sqft": rate,
        "total_cost_pkr": total_cost_pkr,
        "concrete_m3": concrete_m3,
        "steel_tonnes": steel_tonnes,
        "cement_bags": cement_bags,
    }
 
# =========================================================
# RECOMMENDATION LOGIC (rule-based)
# =========================================================
 
def recommend(soil_name, floors, purpose, seismic_zone, groundwater, length, width):
    soil = SOIL_DB[soil_name]
    category = soil["category"]
    expansive = soil["expansive"]
    warnings = []
    explanation = []
    high_load = floors >= 6 or purpose in ("hospital", "warehouse")
 
    if category == "strong":
        foundation = "Raft Foundation" if high_load else "Isolated Footing"
        depth = 1.6 if high_load else 1.2
        explanation.append(
            f"{soil_name} offers high bearing capacity, allowing a shallow foundation even for this building load."
        )
    elif category == "weak":
        if high_load:
            foundation = "Pile Foundation"
            depth = 10.0
            explanation.append(
                f"{soil_name} has low bearing capacity. With this load, piles transfer forces down to deeper, "
                "more competent soil layers instead of relying on the weak surface soil."
            )
        else:
            foundation = "Raft Foundation"
            depth = 2.2
            explanation.append(
                f"{soil_name} has low bearing capacity, so a raft spreads the building load over a larger area "
                "and reduces the risk of differential settlement."
            )
            warnings.append(f"{soil_name} may experience settlement over time; periodic monitoring is advised.")
        if expansive:
            depth = max(depth, 2.0)
            warnings.append(
                f"{soil_name} is expansive and can swell/shrink with seasonal moisture changes. The foundation "
                "should extend below the active zone, with moisture barriers around the perimeter."
            )
    else:  # moderate
        foundation = "Strip Footing" if floors <= 3 else "Raft Foundation"
        depth = 1.6
        explanation.append(
            f"{soil_name} provides moderate bearing capacity, suitable for a {foundation.lower()} at this building scale."
        )
 
    if groundwater == "High (< 2m)":
        warnings.append("High groundwater table detected; waterproofing and dewatering during construction will be needed.")
        if foundation != "Pile Foundation":
            depth = min(depth, 1.5)
        explanation.append("Foundation depth is kept conservative because the groundwater table is shallow.")
 
    if seismic_zone in ("High", "Severe") and floors >= 4:
        structural_system = "Shear Wall System"
        explanation.append("In a high seismic zone with a multi-story building, shear walls give better lateral stability than a frame alone.")
    elif floors >= 8:
        structural_system = "Steel Frame"
        explanation.append("For taller buildings, steel framing gives a good strength-to-weight ratio and faster construction.")
    else:
        structural_system = "RC Frame"
        explanation.append("For this height and load, a conventional RC frame is a practical, economical choice.")
 
    aspect_ratio = max(length, width) / max(min(length, width), 0.1)
    if aspect_ratio > 2.5:
        shapes = ["Rectangular"]
        warnings.append("Plot is quite elongated; avoid irregular shapes to limit torsional effects during earthquakes.")
    elif purpose in ("hospital",):
        shapes = ["H-shaped", "Courtyard", "U-shaped", "Cross-shaped", "Rectangular"]
        explanation.append("H-shaped, courtyard, and cross layouts give more perimeter wall for natural light and ventilation into every ward — valuable for a hospital.")
    elif purpose == "school":
        shapes = ["U-shaped", "Courtyard", "H-shaped", "L-shaped", "Rectangular"]
        explanation.append("U-shaped and courtyard layouts let classrooms open onto a shared yard, a common school planning pattern.")
    elif purpose == "office":
        shapes = ["Rectangular", "Square", "T-shaped", "L-shaped", "Cross-shaped"]
    else:
        shapes = ["Rectangular", "Square", "L-shaped", "T-shaped"]
 
    if seismic_zone in ("High", "Severe"):
        shapes = [s for s in shapes if s in ("Rectangular", "Square")] or ["Rectangular"]
        warnings.append("In high seismic zones, simple symmetric shapes (rectangular/square) perform better than irregular ones.")
 
    return {
        "foundation": foundation,
        "depth": depth,
        "structural_system": structural_system,
        "shapes": shapes,
        "warnings": warnings,
        "explanation": " ".join(explanation),
    }
 
 
# =========================================================
# FOOTPRINT HELPER
# =========================================================
 
def get_footprint(shape, length, width):
    if shape in ("Rectangular", "Square"):
        return [(0, 0, length, width)]
 
    if shape == "L-shaped":
        return [(0, 0, length, width * 0.55), (0, width * 0.55, length * 0.45, width * 0.45)]
 
    if shape == "U-shaped":
        arm_w = width * 0.3
        return [
            (0, 0, length, arm_w),
            (0, arm_w, arm_w, width - arm_w),
            (length - arm_w, arm_w, arm_w, width - arm_w),
        ]
 
    if shape == "T-shaped":
        bar_h = width * 0.32
        stem_w = length * 0.32
        return [
            (0, width - bar_h, length, bar_h),                              # top cross-bar
            (length/2 - stem_w/2, 0, stem_w, width - bar_h),                # stem
        ]
 
    if shape == "H-shaped":
        leg_w = length * 0.25
        bar_h = width * 0.24
        return [
            (0, 0, leg_w, width),                                          # left leg
            (length - leg_w, 0, leg_w, width),                             # right leg
            (leg_w, width/2 - bar_h/2, length - 2*leg_w, bar_h),           # connecting bar
        ]
 
    if shape == "Cross-shaped":
        bar_h = width * 0.32
        bar_w = length * 0.32
        return [
            (0, width/2 - bar_h/2, length, bar_h),                         # horizontal bar
            (length/2 - bar_w/2, 0, bar_w, width),                         # vertical bar
        ]
 
    if shape == "Courtyard":
        t = min(length, width) * 0.24  # wing thickness, open courtyard in the middle
        return [
            (0, 0, length, t),                                            # front wing
            (0, width - t, length, t),                                    # back wing
            (0, t, t, width - 2*t),                                       # left wing
            (length - t, t, t, width - 2*t),                              # right wing
        ]
 
    return [(0, 0, length, width)]
 
 
# =========================================================
# 3D ANIMATED MODEL
# =========================================================
 
def make_box_mesh(x0, y0, z0, dx, dy, dz, color, opacity=1.0):
    x = [x0, x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx]
    y = [y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy, y0]
    z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]
    # Correct box triangulation: 2 triangles per face, always along adjacent corners
    # (the previous index list connected diagonal corners on several faces, producing
    # a visible bowtie/hourglass fold across each face instead of a flat surface).
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]
    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity,
        flatshading=True, showscale=False,
        lighting=dict(ambient=0.65, diffuse=0.65, specular=0.15, roughness=0.7, fresnel=0.05),
        lightposition=dict(x=200, y=200, z=500),
    )
 
 
def make_flat_quad(pts, color, opacity=0.92):
    """A single flat rectangular panel from 4 ordered 3D corner points — used for windows."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return go.Mesh3d(x=xs, y=ys, z=zs, i=[0, 0], j=[1, 2], k=[2, 3],
                      color=color, opacity=opacity, flatshading=True, showscale=False, hoverinfo="skip")
 
 
def make_window_band(x0, y0, dx, dy, z0, dz, window_color="#3a4a5c"):
    """A row of window strips on the two long faces of a floor slab, for a more realistic facade."""
    eps = 0.03
    wz0, wz1 = z0 + dz * 0.28, z0 + dz * 0.78
    n_windows = max(2, int(dx // 3))
    seg = dx / n_windows
    traces = []
    for n in range(n_windows):
        wx0 = x0 + seg * n + seg * 0.15
        wx1 = x0 + seg * n + seg * 0.85
        traces.append(make_flat_quad([
            (wx0, y0 - eps, wz0), (wx1, y0 - eps, wz0), (wx1, y0 - eps, wz1), (wx0, y0 - eps, wz1)
        ], window_color))
        traces.append(make_flat_quad([
            (wx0, y0 + dy + eps, wz0), (wx1, y0 + dy + eps, wz0), (wx1, y0 + dy + eps, wz1), (wx0, y0 + dy + eps, wz1)
        ], window_color))
    return traces
 
 
def make_box_edges(x0, y0, z0, dx, dy, dz, line_color="#3a3a3a"):
    """Wireframe outline of a box so floors read as a structure, not a solid block."""
    corners = [
        (x0, y0, z0), (x0+dx, y0, z0), (x0+dx, y0+dy, z0), (x0, y0+dy, z0),
        (x0, y0, z0+dz), (x0+dx, y0, z0+dz), (x0+dx, y0+dy, z0+dz), (x0, y0+dy, z0+dz),
    ]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    xs, ys, zs = [], [], []
    for a, b in edges:
        xs += [corners[a][0], corners[b][0], None]
        ys += [corners[a][1], corners[b][1], None]
        zs += [corners[a][2], corners[b][2], None]
    return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                         line=dict(color=line_color, width=2), showlegend=False, hoverinfo="skip")
 
 
def ground_plane_traces(length, width, soil_color):
    pad = 0.15
    x = [-length*pad, length*(1+pad), length*(1+pad), -length*pad]
    y = [-width*pad, -width*pad, width*(1+pad), width*(1+pad)]
    g1 = go.Mesh3d(x=x, y=y, z=[0,0,0,0], i=[0], j=[1], k=[2], color=soil_color, opacity=0.55)
    g2 = go.Mesh3d(x=[x[0], x[2], x[3]], y=[y[0], y[2], y[3]], z=[0,0,0], i=[0], j=[1], k=[2], color=soil_color, opacity=0.55)
    return [g1, g2]
 
 
def soil_block_trace(footprint, depth, soil_color):
    """Translucent soil volume beneath grade, sized tightly to the footprint (+ small margin)
    so it reads as excavation around the foundation, not a giant surrounding wall."""
    xs = [x0 for (x0, y0, dx, dy) in footprint] + [x0 + dx for (x0, y0, dx, dy) in footprint]
    ys = [y0 for (x0, y0, dx, dy) in footprint] + [y0 + dy for (x0, y0, dx, dy) in footprint]
    margin = 2.0
    x_min, x_max = min(xs) - margin, max(xs) + margin
    y_min, y_max = min(ys) - margin, max(ys) + margin
    return make_box_mesh(x_min, y_min, -depth - 1.0, x_max - x_min, y_max - y_min, depth + 1.0,
                          soil_color, opacity=0.22)
 
 
def make_perimeter_beams(footprint, z0, z1, beam_w=0.35, color="#5b5751"):
    """Straight beams running along each rectangle's four edges between z0 and z1 —
    used both as foundation tie/grade beams and as floor-level ring beams."""
    traces = []
    for (x0, y0, dx, dy) in footprint:
        edges = [
            (x0, y0, x0 + dx, y0),          # bottom edge
            (x0, y0 + dy, x0 + dx, y0 + dy),  # top edge
            (x0, y0, x0, y0 + dy),          # left edge
            (x0 + dx, y0, x0 + dx, y0 + dy),  # right edge
        ]
        for (ax, ay, bx, by) in edges:
            if ay == by:
                traces.append(make_box_mesh(min(ax, bx), ay - beam_w/2, z0, abs(bx-ax), beam_w, z1-z0, color, 0.97))
            else:
                traces.append(make_box_mesh(ax - beam_w/2, min(ay, by), z0, beam_w, abs(by-ay), z1-z0, color, 0.97))
    return traces
 
 
FOUNDATION_BEAM_COLOR = "#b5451f"   # terracotta — distinct from gray floor beams
DRAINAGE_COLOR = "#1478d4"          # bright blue — sewer / drainage lines
TANK_COLOR = "#3d4a44"              # septic tank / soak pit
 
 
def make_label(x, y, z, text):
    return go.Scatter3d(
        x=[x], y=[y], z=[z], mode="text", text=[text], textposition="middle center",
        textfont=dict(size=12, color="#1c2b3a", family="Inter, sans-serif"),
        showlegend=False, hoverinfo="skip",
    )
 
 
def make_foundation_traces(footprint, foundation_type, depth, fnd_color="#767065"):
    """Build below-grade foundation geometry matching the recommended foundation type.
    The foundation-level beam is always a distinct terracotta color and labeled, so it
    never blends into the gray floor ring-beams stacked above it."""
    traces = []
    col_color = "#8f8a7e"
    label_x = footprint[0][0] + footprint[0][2] / 2
    label_y = footprint[0][1] + footprint[0][3] / 2
 
    if foundation_type == "Isolated Footing":
        pad_size = 1.4
        pad_h = max(0.45, depth * 0.3)
        for (x0, y0, dx, dy) in footprint:
            for (cx, cy) in [(x0, y0), (x0+dx, y0), (x0, y0+dy), (x0+dx, y0+dy)]:
                traces.append(make_box_mesh(cx-pad_size/2, cy-pad_size/2, -depth, pad_size, pad_size, pad_h, fnd_color, 0.97))
                traces.append(make_box_edges(cx-pad_size/2, cy-pad_size/2, -depth, pad_size, pad_size, pad_h))
                traces.append(make_box_mesh(cx-0.25, cy-0.25, -depth+pad_h, 0.5, 0.5, depth-pad_h, col_color, 0.97))
                traces.append(make_box_edges(cx-0.25, cy-0.25, -depth+pad_h, 0.5, 0.5, depth-pad_h))
        traces += make_perimeter_beams(footprint, -0.45, -0.05, beam_w=0.55, color=FOUNDATION_BEAM_COLOR)
        traces.append(make_label(label_x, label_y, 1.2, "Foundation tie beam"))
 
    elif foundation_type == "Strip Footing":
        strip_w, strip_h = 0.9, max(0.4, depth * 0.3)
        for (x0, y0, dx, dy) in footprint:
            edges = [
                (x0-0.3, y0-0.3, dx+0.6, strip_w),
                (x0-0.3, y0+dy-strip_w+0.3, dx+0.6, strip_w),
                (x0-0.3, y0-0.3, strip_w, dy+0.6),
                (x0+dx-strip_w+0.3, y0-0.3, strip_w, dy+0.6),
            ]
            for (ex, ey, edx, edy) in edges:
                traces.append(make_box_mesh(ex, ey, -depth, edx, edy, strip_h, fnd_color, 0.97))
            traces.append(make_box_edges(x0-0.3, y0-0.3, -depth, dx+0.6, dy+0.6, strip_h))
            beam_z0 = -depth + strip_h
            traces += make_perimeter_beams([(x0-0.3, y0-0.3, dx+0.6, dy+0.6)], beam_z0, beam_z0+0.35,
                                            beam_w=1.0, color=FOUNDATION_BEAM_COLOR)
        traces.append(make_label(label_x, label_y, 1.2, "Foundation beam (on strip footing)"))
 
    elif foundation_type == "Raft Foundation":
        raft_h = max(0.5, depth * 0.28)
        for (x0, y0, dx, dy) in footprint:
            traces.append(make_box_mesh(x0-0.5, y0-0.5, -depth, dx+1.0, dy+1.0, raft_h, fnd_color, 0.97))
            traces.append(make_box_edges(x0-0.5, y0-0.5, -depth, dx+1.0, dy+1.0, raft_h))
            beam_z0 = -depth + raft_h
            traces += make_perimeter_beams([(x0-0.5, y0-0.5, dx+1.0, dy+1.0)], beam_z0, beam_z0+0.4,
                                            beam_w=0.6, color=FOUNDATION_BEAM_COLOR)
        traces.append(make_label(label_x, label_y, 1.2, "Foundation edge beam (on raft)"))
 
    elif foundation_type == "Pile Foundation":
        cap_h = 1.2
        for (x0, y0, dx, dy) in footprint:
            traces.append(make_box_mesh(x0-0.3, y0-0.3, -cap_h, dx+0.6, dy+0.6, cap_h, fnd_color, 0.97))
            traces.append(make_box_edges(x0-0.3, y0-0.3, -cap_h, dx+0.6, dy+0.6, cap_h))
            nx = max(2, min(3, int(dx // 5)))
            ny = max(2, min(3, int(dy // 5)))
            xs = np.linspace(x0+0.6, x0+dx-0.6, nx)
            ys = np.linspace(y0+0.6, y0+dy-0.6, ny)
            for px in xs:
                for py in ys:
                    traces.append(make_box_mesh(px-0.25, py-0.25, -depth, 0.5, 0.5, depth-cap_h, "#5c5850", 0.97))
        traces += make_perimeter_beams(footprint, -0.45, -0.05, beam_w=0.55, color=FOUNDATION_BEAM_COLOR)
        traces.append(make_label(label_x, label_y, 1.2, "Foundation tie beam"))
 
    return traces
 
 
def make_drainage_traces(footprint, length, width):
    """Sewer connection from the building to a soak pit / septic tank at the plot edge.
    Includes a vertical riser pipe running up the building's exterior wall (so the drain
    visibly connects to the structure, not just appears floating near it), then the buried
    run out to a manhole and septic tank. Uses the full footprint bounding box (not just one
    rectangle), so it clears the building even for L/U-shaped layouts like a school.
    Schematic, not a hydraulic design."""
    traces = []
    xs = [p[0] for p in footprint] + [p[0] + p[2] for p in footprint]
    ys = [p[1] for p in footprint] + [p[1] + p[3] for p in footprint]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
 
    wall_x = x_min + (x_max - x_min) * 0.2
    riser_top = (wall_x, y_min, 2.3)
    outlet = (wall_x, y_min, -0.7)
    bend = (outlet[0], y_min - max(3.0, width * 0.25), -1.1)
    tank_size = 1.8
    tank_x, tank_y = bend[0] - tank_size/2, bend[1] - max(3.0, width * 0.2)
    tank_top = -1.4
 
    # riser: visible pipe running up the building's exterior wall, from just below the
    # ground line up past the first floor — this is what makes the drain read as "plumbed
    # into the building" rather than a disconnected line floating nearby.
    traces.append(go.Scatter3d(
        x=[riser_top[0], outlet[0]], y=[riser_top[1], outlet[1]], z=[riser_top[2], outlet[2]],
        mode="lines", line=dict(color=DRAINAGE_COLOR, width=11), showlegend=False, hoverinfo="skip",
    ))
    # small pipe collar where the riser meets the ground, for a finished look
    traces.append(make_box_mesh(outlet[0]-0.2, outlet[1]-0.2, -0.15, 0.4, 0.4, 0.3, "#123a5c", 0.95))
    traces.append(make_label(riser_top[0], riser_top[1] - 0.6, riser_top[2] + 0.5, "Drain pipe (from building)"))
 
    # segment 1: building outlet -> manhole bend, just outside the footprint
    traces.append(go.Scatter3d(
        x=[outlet[0], bend[0]], y=[outlet[1], bend[1]], z=[outlet[2], bend[2]],
        mode="lines", line=dict(color=DRAINAGE_COLOR, width=11), showlegend=False, hoverinfo="skip",
    ))
    traces.append(make_box_mesh(bend[0]-0.35, bend[1]-0.35, bend[2]-0.15, 0.7, 0.7, 0.3, "#123a5c", 0.95))
    traces.append(make_box_edges(bend[0]-0.35, bend[1]-0.35, bend[2]-0.15, 0.7, 0.7, 0.3))
 
    # segment 2: manhole -> septic tank / soak pit
    traces.append(go.Scatter3d(
        x=[bend[0], tank_x + tank_size/2], y=[bend[1], tank_y + tank_size/2], z=[bend[2], tank_top],
        mode="lines", line=dict(color=DRAINAGE_COLOR, width=11), showlegend=False, hoverinfo="skip",
    ))
    traces.append(make_box_mesh(tank_x, tank_y, tank_top - 1.6, tank_size, tank_size, 1.6, TANK_COLOR, 0.95))
    traces.append(make_box_edges(tank_x, tank_y, tank_top - 1.6, tank_size, tank_size, 1.6))
    traces.append(make_label(tank_x + tank_size/2, tank_y + tank_size/2, 0.9, "Septic tank / soak pit"))
    return traces
 
 
def compute_footprint_bbox(footprint):
    xs = [p[0] for p in footprint] + [p[0] + p[2] for p in footprint]
    ys = [p[1] for p in footprint] + [p[1] + p[3] for p in footprint]
    return min(xs), max(xs), min(ys), max(ys)
 
 
def make_building_stacks(footprint, floors, floor_height):
    """Internal soil-pipe stacks, run exposed on the building's exterior wall (as is common
    on real buildings) — one stack per wing (two for large wings), each with a short branch
    stub at every floor representing a bathroom/kitchen connection, running down to the same
    exterior outlet used by the outdoor drain run. Placing the stack on the outside of the
    wall (rather than inside the footprint) is what makes it actually visible instead of
    hidden behind the opaque building mass."""
    x_min, x_max, y_min, y_max = compute_footprint_bbox(footprint)
    wall_x = x_min + (x_max - x_min) * 0.2
    outlet = (wall_x, y_min, -0.7)
 
    # (x, y, branch_direction) — branch_direction is the y-step from the stack, back into
    # the building, so only the short T-fitting is visible and the rest reads as "inside"
    stack_points = []
    for (x0, y0, dx, dy) in footprint:
        stack_points.append((x0 + dx * 0.25, y0 - 0.35, 1))
        if dx > 9 or dy > 9:
            stack_points.append((x0 + dx * 0.75, y0 + dy + 0.35, -1))
 
    base_traces = []
    per_floor_traces = {lvl: [] for lvl in range(floors)}
    fitting_color = "#123a5c"  # dark blue, reads as part of the network rather than a generic black box
 
    for (sx, sy, branch_dir) in stack_points:
        base_traces.append(go.Scatter3d(
            x=[sx, outlet[0]], y=[sy, outlet[1]], z=[-0.4, outlet[2]],
            mode="lines", line=dict(color=DRAINAGE_COLOR, width=6), showlegend=False, hoverinfo="skip",
        ))
        for lvl in range(floors):
            z0 = lvl * floor_height
            z_branch = z0 + floor_height * 0.5
            branch_dy = branch_dir * 0.9
            per_floor_traces[lvl].append(go.Scatter3d(
                x=[sx, sx], y=[sy, sy], z=[z0, z0 + floor_height * 0.94],
                mode="lines", line=dict(color=DRAINAGE_COLOR, width=6), showlegend=False, hoverinfo="skip",
            ))
            per_floor_traces[lvl].append(go.Scatter3d(
                x=[sx, sx], y=[sy, sy + branch_dy], z=[z_branch, z_branch],
                mode="lines", line=dict(color=DRAINAGE_COLOR, width=5), showlegend=False, hoverinfo="skip",
            ))
            per_floor_traces[lvl].append(make_box_mesh(
                sx - 0.14, sy + branch_dy - 0.14, z_branch - 0.14, 0.28, 0.28, 0.28, fitting_color, 0.95
            ))
 
    if stack_points:
        base_traces.append(make_label(stack_points[0][0], stack_points[0][1] - 1.2, floor_height * 0.5, "Soil pipe stack (exterior)"))
    return base_traces, per_floor_traces
 
 
def build_3d_animated_figure(shape, length, width, floors, structural_system, soil_color, foundation_type, depth):
    floor_height = 3.0
    color = STRUCT_COLOR.get(structural_system, "#8c9aa8")
    beam_color = {"RC Frame": "#8a8577", "Shear Wall System": "#546e8a", "Steel Frame": "#75604a"}.get(structural_system, "#7a7a72")
    footprint = get_footprint(shape, length, width)
    ground = ground_plane_traces(length, width, soil_color)
    soil_block = soil_block_trace(footprint, depth, soil_color)
    foundation = make_foundation_traces(footprint, foundation_type, depth)
    drainage = make_drainage_traces(footprint, length, width)
    stacks_base, stacks_per_floor = make_building_stacks(footprint, floors, floor_height)
    base_layer = [soil_block] + foundation + ground + drainage + stacks_base
 
    frames = []
    for f in range(1, floors + 1):
        frame_data = list(base_layer)
        for lvl in range(f):
            z0 = lvl * floor_height
            opacity = 1.0 if lvl == f - 1 else 0.88
            for (x0, y0, dx, dy) in footprint:
                frame_data.append(make_box_mesh(x0, y0, z0, dx, dy, floor_height * 0.94, color, opacity))
                frame_data.append(make_box_edges(x0, y0, z0, dx, dy, floor_height * 0.94))
                frame_data += make_window_band(x0, y0, dx, dy, z0, floor_height * 0.94)
            # ring beam at the base of each floor, supporting the slab above
            frame_data += make_perimeter_beams(footprint, z0, z0 + 0.35, beam_w=0.4, color=beam_color)
            # internal plumbing stack segment + floor branch for this level
            frame_data += stacks_per_floor[lvl]
        # roof cap / parapet on the top floor for a finished look
        roof_z = f * floor_height
        for (x0, y0, dx, dy) in footprint:
            frame_data.append(make_box_mesh(x0-0.15, y0-0.15, roof_z, dx+0.3, dy+0.3, 0.35, "#565048", 0.97))
            frame_data.append(make_box_edges(x0-0.15, y0-0.15, roof_z, dx+0.3, dy+0.3, 0.35))
        frames.append(go.Frame(data=frame_data, name=str(f)))
 
    fig = go.Figure(data=frames[-1].data, frames=frames)
    fig.update_layout(
        scene=dict(
            xaxis_title="Length (m)", yaxis_title="Width (m)", zaxis_title="Height (m)",
            aspectmode="data",
            dragmode="orbit",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.3)),
            xaxis=dict(backgroundcolor="rgb(247,248,250)", gridcolor="rgb(225,228,232)"),
            yaxis=dict(backgroundcolor="rgb(247,248,250)", gridcolor="rgb(225,228,232)"),
            zaxis=dict(backgroundcolor="rgb(250,251,252)", gridcolor="rgb(225,228,232)"),
        ),
        font=dict(family="Inter, sans-serif", color="#334155", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        updatemenus=[dict(
            type="buttons", showactive=False, y=0.02, x=0.01, xanchor="left", yanchor="bottom",
            bgcolor="#ffffff", bordercolor="#cbd5e1", borderwidth=1,
            font=dict(size=11, color="#334155"),
            buttons=[
                dict(label="Build sequence", method="animate",
                     args=[None, {"frame": {"duration": 500, "redraw": True}, "fromcurrent": True, "transition": {"duration": 250}}]),
                dict(label="Reset", method="animate",
                     args=[[frames[0].name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]),
            ]
        )],
    )
    return fig
 
 
def build_town_3d_figure(total_length, total_width, houses_per_row, rows, house_floors, soil_color, structural_system):
    """Conceptual mixed-use town layout: houses/hospital/office set back on plots beside
    real road surfaces (not sitting on top of them), a few parked cars for scale, and a
    proper branching sewer network — each building's riser feeds a street sewer line for
    its row, every street line feeds one trunk main, and the trunk gets deeper as it runs
    toward a single outfall, the way a real gravity sewer is graded. Planning-level sketch,
    not a hydraulic design (no pipe sizing/slope calculations)."""
    road_w_x = max(2.2, min(5.0, total_length / (houses_per_row * 2.5)))
    road_w_y = max(2.2, min(5.0, total_width / (rows * 2.5)))
    plot_w = max(3.0, (total_length - (houses_per_row - 1) * road_w_x) / houses_per_row)
    plot_d = max(3.0, (total_width - (rows - 1) * road_w_y) / rows)
    floor_h = 3.0
    total_plots = houses_per_row * rows
 
    BUILD_FLOORS = {"House": house_floors, "Hospital": max(3, house_floors + 1), "Office": max(4, house_floors + 2)}
    BUILD_COLOR = {"House": STRUCT_COLOR.get(structural_system, "#c9c4b8"), "Hospital": "#7c92a8", "Office": "#9a8168"}
    ROAD_COLOR = "#48474a"
    CAR_COLORS = ["#b23b3b", "#2b3b6b", "#c9c9c9", "#3f7d4c", "#4a4a52"]
 
    plot_types = ["House"] * total_plots
    if total_plots >= 4:
        plot_types[total_plots // 2] = "Hospital"
    if total_plots >= 6:
        plot_types[-1] = "Office"
 
    traces = []
    traces += ground_plane_traces(total_length, total_width, soil_color)  # bare earth base, not asphalt gray
    traces[-1].opacity = 0.6
    traces[-2].opacity = 0.6
 
    # --- explicit road surfaces, visually distinct from the yards, with a center lane stripe ---
    for r in range(rows - 1):
        road_y0 = r * (plot_d + road_w_y) + plot_d
        traces.append(make_box_mesh(-1.5, road_y0, 0.02, total_length + 3.0, road_w_y, 0.03, ROAD_COLOR, 0.97))
        traces.append(go.Scatter3d(x=[0, total_length], y=[road_y0 + road_w_y/2]*2, z=[0.05, 0.05],
                                    mode="lines", line=dict(color="#d8cf9a", width=3, dash="dash"),
                                    showlegend=False, hoverinfo="skip"))
    for c in range(houses_per_row - 1):
        road_x0 = c * (plot_w + road_w_x) + plot_w
        traces.append(make_box_mesh(road_x0, -1.5, 0.02, road_w_x, total_width + 3.0, 0.03, ROAD_COLOR, 0.97))
        traces.append(go.Scatter3d(x=[road_x0 + road_w_x/2]*2, y=[0, total_width], z=[0.05, 0.05],
                                    mode="lines", line=dict(color="#d8cf9a", width=3, dash="dash"),
                                    showlegend=False, hoverinfo="skip"))
 
    # --- parked cars for scale/realism: one on each internal road ---
    car_idx = 0
    for r in range(rows - 1):
        road_y0 = r * (plot_d + road_w_y) + plot_d
        cx = total_length * (0.3 if r % 2 == 0 else 0.65)
        cy = road_y0 + road_w_y * 0.72
        col = CAR_COLORS[car_idx % len(CAR_COLORS)]
        traces.append(make_box_mesh(cx, cy, 0.05, 3.6, 1.6, 1.3, col, 0.95))
        traces.append(make_box_edges(cx, cy, 0.05, 3.6, 1.6, 1.3))
        car_idx += 1
    for c in range(houses_per_row - 1):
        road_x0 = c * (plot_w + road_w_x) + plot_w
        cy = total_width * (0.35 if c % 2 == 0 else 0.7)
        cx = road_x0 + road_w_x * 0.72
        col = CAR_COLORS[car_idx % len(CAR_COLORS)]
        traces.append(make_box_mesh(cx, cy, 0.05, 1.6, 3.6, 1.3, col, 0.95))
        traces.append(make_box_edges(cx, cy, 0.05, 1.6, 3.6, 1.3))
        car_idx += 1
 
    # --- street lights: a few posts along every road, on the side opposite the parked cars ---
    def make_street_light(x, y, pole_h=5.0):
        return [
            make_box_mesh(x-0.09, y-0.09, 0, 0.18, 0.18, pole_h, "#3a3a3a", 0.97),
            make_box_mesh(x-0.3, y-0.3, pole_h, 0.6, 0.6, 0.25, "#f2d675", 0.9),
        ]
 
    light_fracs = [0.15, 0.5, 0.85]
    for r in range(rows - 1):
        road_y0 = r * (plot_d + road_w_y) + plot_d
        ly = road_y0 + road_w_y * 0.2
        for frac in light_fracs:
            traces += make_street_light(total_length * frac, ly)
    for c in range(houses_per_row - 1):
        road_x0 = c * (plot_w + road_w_x) + plot_w
        lx = road_x0 + road_w_x * 0.2
        for frac in light_fracs:
            traces += make_street_light(lx, total_width * frac)
 
    # --- buildings, set back on their plots beside the roads ---
    building_walls = []  # (row_index, wall_x, wall_y) — the wall facing this row's street sewer
    counts = {"House": 0, "Hospital": 0, "Office": 0}
    idx = 0
    for r in range(rows):
        for c in range(houses_per_row):
            btype = plot_types[idx]
            idx += 1
            counts[btype] += 1
            floors_here = BUILD_FLOORS[btype]
            color = BUILD_COLOR[btype]
            shrink = 0.68 if btype in ("Hospital", "Office") else 0.72
            b_w, b_d = plot_w * shrink, plot_d * shrink
 
            px = c * (plot_w + road_w_x)
            py = r * (plot_d + road_w_y)
            bx = px + (plot_w - b_w) / 2
            by = py + (plot_d - b_d) / 2
 
            # connect from whichever wall faces this row's street (south wall normally,
            # north wall for the last row, which shares the road before it)
            wall_y = by + b_d if r < rows - 1 else by
            building_walls.append((r, bx + b_w * 0.25, wall_y))
 
            traces.append(make_box_mesh(px, py, -0.05, plot_w, plot_d, 0.05, soil_color, 0.55))  # yard
            traces.append(make_box_mesh(bx, by, 0, b_w, b_d, floor_h * floors_here, color, 0.97))
            traces.append(make_box_edges(bx, by, 0, b_w, b_d, floor_h * floors_here))
            if b_w >= 3.0:
                for lvl in range(floors_here):
                    traces += make_window_band(bx, by, b_w, b_d, lvl * floor_h, floor_h * 0.94)
            roof_z = floor_h * floors_here
            traces.append(make_box_mesh(bx-0.1, by-0.1, roof_z, b_w+0.2, b_d+0.2, 0.25, "#565048", 0.97))
            traces.append(make_label(bx + b_w/2, by + b_d/2, floor_h * floors_here + 1.2, btype))
 
    # --- drainage network: house riser -> row street sewer -> trunk main -> outfall ---
    street_z, trunk_z = -1.0, -1.7
    if rows >= 2:
        street_y = [min(r, rows - 2) * (plot_d + road_w_y) + plot_d + road_w_y / 2 for r in range(rows)]
    else:
        street_y = [plot_d + road_w_y]  # virtual street line for a single-row layout
 
    trunk_x = total_length + 2.5
    unique_streets = sorted(set(street_y))
    for sy in unique_streets:
        traces.append(go.Scatter3d(x=[0, trunk_x], y=[sy, sy], z=[street_z, street_z],
                                    mode="lines", line=dict(color=DRAINAGE_COLOR, width=8), showlegend=False, hoverinfo="skip"))
        traces.append(go.Scatter3d(x=[trunk_x, trunk_x], y=[sy, sy], z=[street_z, trunk_z],
                                    mode="lines", line=dict(color=DRAINAGE_COLOR, width=8), showlegend=False, hoverinfo="skip"))
        traces.append(make_box_mesh(trunk_x-0.4, sy-0.4, trunk_z-0.15, 0.8, 0.8, 0.3, "#123a5c", 0.95))
 
    outfall = (trunk_x + 2.0, unique_streets[len(unique_streets)//2], trunk_z - 1.0)
    traces.append(go.Scatter3d(x=[trunk_x]*2, y=[min(unique_streets), max(unique_streets)], z=[trunk_z, trunk_z],
                                mode="lines", line=dict(color=DRAINAGE_COLOR, width=13), showlegend=False, hoverinfo="skip"))
    traces.append(go.Scatter3d(x=[trunk_x, outfall[0]], y=[outfall[1], outfall[1]], z=[trunk_z, outfall[2]],
                                mode="lines", line=dict(color=DRAINAGE_COLOR, width=13), showlegend=False, hoverinfo="skip"))
    traces.append(make_box_mesh(outfall[0]-0.8, outfall[1]-0.8, outfall[2]-0.8, 1.6, 1.6, 1.0, TANK_COLOR, 0.95))
    traces.append(make_label(outfall[0], outfall[1], outfall[2]+1.2, "Outfall / main sewer connection"))
    traces.append(make_label(trunk_x, sum(unique_streets)/len(unique_streets), floor_h*max(BUILD_FLOORS.values())+3, "Trunk main (deepens toward outfall)"))
 
    for (r, wx, wy) in building_walls:
        sy = street_y[r]
        traces.append(go.Scatter3d(x=[wx, wx], y=[wy, wy], z=[1.6, -0.5],
                                    mode="lines", line=dict(color=DRAINAGE_COLOR, width=9), showlegend=False, hoverinfo="skip"))
        traces.append(make_box_mesh(wx-0.18, wy-0.18, -0.65, 0.36, 0.36, 0.25, "#123a5c", 0.95))
        traces.append(go.Scatter3d(x=[wx, wx], y=[wy, sy], z=[-0.5, street_z],
                                    mode="lines", line=dict(color=DRAINAGE_COLOR, width=6), showlegend=False, hoverinfo="skip"))
 
    fig = go.Figure(data=traces)
    fig.update_layout(
        scene=dict(
            xaxis_title="Length (m)", yaxis_title="Width (m)", zaxis_title="Height (m)",
            aspectmode="data", dragmode="orbit",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.1)),
            xaxis=dict(backgroundcolor="rgb(247,248,250)", gridcolor="rgb(225,228,232)"),
            yaxis=dict(backgroundcolor="rgb(247,248,250)", gridcolor="rgb(225,228,232)"),
            zaxis=dict(backgroundcolor="rgb(250,251,252)", gridcolor="rgb(225,228,232)"),
        ),
        font=dict(family="Inter, sans-serif", color="#334155", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        height=650,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig, counts
 
def foundation_profile_shapes(x_center, x_span, depth, foundation_type, ground_y=0):
    """Return list of plotly shape dicts drawing the foundation below ground line (2D side view)."""
    shapes = []
    if foundation_type == "Isolated Footing" or foundation_type == "Strip Footing":
        pad_w = x_span if foundation_type == "Strip Footing" else min(2.5, x_span)
        shapes.append(dict(type="rect", x0=x_center-pad_w/2, x1=x_center+pad_w/2,
                            y0=ground_y-depth, y1=ground_y-depth+0.5,
                            fillcolor="#7d7d7d", line=dict(color="#333", width=1)))
        shapes.append(dict(type="rect", x0=x_center-pad_w/6, x1=x_center+pad_w/6,
                            y0=ground_y-depth+0.5, y1=ground_y,
                            fillcolor="#9a9a9a", line=dict(color="#333", width=1)))
    elif foundation_type == "Raft Foundation":
        shapes.append(dict(type="rect", x0=x_center-x_span/2, x1=x_center+x_span/2,
                            y0=ground_y-depth, y1=ground_y-depth+0.6,
                            fillcolor="#7d7d7d", line=dict(color="#333", width=1)))
    elif foundation_type == "Pile Foundation":
        shapes.append(dict(type="rect", x0=x_center-1.5, x1=x_center+1.5,
                            y0=ground_y-1.5, y1=ground_y,
                            fillcolor="#7d7d7d", line=dict(color="#333", width=1)))
        for off in (-1.0, 0, 1.0):
            shapes.append(dict(type="rect", x0=x_center+off-0.15, x1=x_center+off+0.15,
                                y0=ground_y-depth, y1=ground_y-1.5,
                                fillcolor="#5a5a5a", line=dict(color="#333", width=1)))
    return shapes
 
 
def build_plan_view(shape, length, width, soil_name):
    footprint = get_footprint(shape, length, width)
    soil_color = SOIL_DB[soil_name]["color"]
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-length*0.15, x1=length*1.15, y0=-width*0.15, y1=width*1.15,
                  fillcolor=soil_color, opacity=0.25, line=dict(width=0))
    for (x0, y0, dx, dy) in footprint:
        fig.add_shape(type="rect", x0=x0, x1=x0+dx, y0=y0, y1=y0+dy,
                      fillcolor="#c9c2b3", line=dict(color="#333", width=2))
    fig.add_annotation(x=length/2, y=-width*0.22, text=f"Length = {length:.1f} m", showarrow=False)
    fig.add_annotation(x=-length*0.22, y=width/2, text=f"Width = {width:.1f} m", showarrow=False, textangle=-90)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Plan View (Top)", height=420, margin=dict(l=10, r=10, t=40, b=10),
                       plot_bgcolor="white")
    return fig
 
 
def build_elevation_view(length, floors, foundation_type, depth, soil_name, groundwater):
    soil_color = SOIL_DB[soil_name]["color"]
    floor_h = 3.0
    total_h = floors * floor_h
    fig = go.Figure()
 
    fig.add_shape(type="rect", x0=0, x1=length, y0=-depth-1, y1=0,
                  fillcolor=soil_color, opacity=0.5, line=dict(width=0))
    fig.add_shape(type="rect", x0=0, x1=length, y0=0, y1=total_h,
                  fillcolor="#d8d3c3", line=dict(color="#333", width=2))
    for f in range(1, floors):
        fig.add_shape(type="line", x0=0, x1=length, y0=f*floor_h, y1=f*floor_h, line=dict(color="#666", width=1))
    for s in foundation_profile_shapes(length/2, length*0.9, depth, foundation_type):
        fig.add_shape(**s)
    if groundwater == "High (< 2m)":
        fig.add_shape(type="line", x0=0, x1=length, y0=-1.5, y1=-1.5, line=dict(color="#2b6cb0", width=2, dash="dash"))
        fig.add_annotation(x=length*0.9, y=-1.5, text="Groundwater level", showarrow=False, font=dict(color="#2b6cb0", size=10))
    fig.add_shape(type="line", x0=-length*0.05, x1=length*1.05, y0=0, y1=0, line=dict(color="black", width=2))
    fig.add_annotation(x=length/2, y=total_h+1, text=f"{floors} floors ≈ {total_h:.1f} m", showarrow=False)
    fig.add_annotation(x=length/2, y=-depth-1.3, text=f"Foundation depth = {depth:.1f} m ({foundation_type})", showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Elevation View (Front)", height=480, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="white")
    return fig
 
 
def build_section_view(width, floors, foundation_type, depth, soil_name, groundwater):
    soil_color = SOIL_DB[soil_name]["color"]
    floor_h = 3.0
    total_h = floors * floor_h
    fig = go.Figure()
 
    fig.add_shape(type="rect", x0=0, x1=width, y0=-depth-1, y1=0,
                  fillcolor=soil_color, opacity=0.5, line=dict(width=0))
    fig.add_shape(type="rect", x0=0.3, x1=width-0.3, y0=0, y1=total_h,
                  fillcolor="#eee8da", line=dict(color="#333", width=2))
    for f in range(1, floors):
        fig.add_shape(type="line", x0=0.3, x1=width-0.3, y0=f*floor_h, y1=f*floor_h, line=dict(color="#888", width=1, dash="dot"))
    for s in foundation_profile_shapes(width/2, width*0.85, depth, foundation_type):
        fig.add_shape(**s)
    if groundwater == "High (< 2m)":
        fig.add_shape(type="line", x0=0, x1=width, y0=-1.5, y1=-1.5, line=dict(color="#2b6cb0", width=2, dash="dash"))
    fig.add_shape(type="line", x0=-width*0.05, x1=width*1.05, y0=0, y1=0, line=dict(color="black", width=2))
    fig.add_annotation(x=width/2, y=-depth-1.3, text=f"{soil_name} — {foundation_type} @ {depth:.1f} m", showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Section View (Cut through building)", height=480, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="white")
    return fig
 
 
# =========================================================
# UI
# =========================================================
 
st.markdown("""
<style>
    .hero {
        background: linear-gradient(120deg, #1c2b3a 0%, #2b4257 100%);
        border-radius: 14px;
        padding: 42px 40px;
        margin-bottom: 28px;
        color: #ffffff;
    }
    .hero-eyebrow {
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #8fb4d9;
        margin-bottom: 6px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0 0 10px 0;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 1.02rem;
        color: #cbd8e5;
        max-width: 720px;
        line-height: 1.5;
    }
    .feature-card {
        background: #ffffff;
        border: 1px solid #e2e6ea;
        border-radius: 10px;
        padding: 18px 20px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .feature-card .icon {
        font-size: 1.3rem;
        margin-bottom: 6px;
    }
    .feature-card .title {
        font-weight: 600;
        color: #1c2b3a;
        margin-bottom: 4px;
        font-size: 0.95rem;
    }
    .feature-card .desc {
        color: #64748b;
        font-size: 0.85rem;
        line-height: 1.4;
    }
</style>
 
<div class="hero">
    <div class="hero-eyebrow">CIVIL ENGINEERING · CONCEPTUAL DESIGN TOOL</div>
    <div class="hero-title">AI Civil Designer</div>
    <div class="hero-sub">
        Enter your site conditions and get an instant, engineering-informed starting point:
        foundation type, structural system, building shape, and a full 3D model with
        plan, elevation, and section views — all before you sit down with a licensed engineer.
    </div>
</div>
""", unsafe_allow_html=True)
 
fc1, fc2, fc3 = st.columns(3)
with fc1:
    st.markdown("""
    <div class="feature-card">
        <div class="icon">🧭</div>
        <div class="title">Site-aware recommendations</div>
        <div class="desc">18 soil profiles, seismic zone, groundwater level, and building purpose all shape the output.</div>
    </div>
    """, unsafe_allow_html=True)
with fc2:
    st.markdown("""
    <div class="feature-card">
        <div class="icon">🏗️</div>
        <div class="title">Animated 3D model</div>
        <div class="desc">A rotatable model that builds floor by floor, with the foundation visible below grade.</div>
    </div>
    """, unsafe_allow_html=True)
with fc3:
    st.markdown("""
    <div class="feature-card">
        <div class="icon">📐</div>
        <div class="title">Engineering drawings</div>
        <div class="desc">Plan, elevation, and section views generated automatically from your inputs.</div>
    </div>
    """, unsafe_allow_html=True)
 
st.write("")
 
with st.sidebar:
    st.header("Site & Building Inputs")
    soil_name = st.selectbox("Soil type", list(SOIL_DB.keys()))
    length = st.number_input("Plot length (m)", min_value=3.0, value=20.0, step=1.0)
    width = st.number_input("Plot width (m)", min_value=3.0, value=12.0, step=1.0)
    floors = st.slider("Number of floors", 1, 15, 3)
    purpose = st.selectbox("Building purpose", ["house", "school", "hospital", "office", "warehouse", "town / housing society"])
    if purpose == "town / housing society":
        houses_per_row = st.slider("Houses per row", 2, 12, 4)
        town_rows = st.slider("Number of rows", 1, 8, 3)
        house_floors = st.slider("Floors per house", 1, 3, 2)
    seismic_zone = st.selectbox("Earthquake zone", ["Low", "Moderate", "High", "Severe"])
    groundwater = st.selectbox("Groundwater level", ["High (< 2m)", "Moderate (2-5m)", "Low (> 5m)"])
    run = st.button("Get Recommendation", type="primary", use_container_width=True)
 
if run and purpose == "town / housing society":
    soil_color = SOIL_DB[soil_name]["color"]
    st.subheader("Town Layout & Drainage Network")
    st.caption(
        "Conceptual planning sketch: house plots on a road grid with a schematic sewer network "
        "(main trunk line + house connections + outfall). This is a layout concept, not a hydraulic "
        "design — actual pipe sizing, slopes, and manhole spacing must follow local drainage codes."
    )
    # rough structural system guess for the town's houses, from soil + seismic zone
    town_result = recommend(soil_name, house_floors, "house", seismic_zone, groundwater, length, width)
    fig_town, type_counts = build_town_3d_figure(length, width, houses_per_row, town_rows, house_floors, soil_color, town_result["structural_system"])
    st.plotly_chart(
        fig_town, use_container_width=True,
        config={"displayModeBar": True, "displaylogo": False, "scrollZoom": True},
    )
    st.caption("Drag to rotate/tilt, scroll to zoom. Teal lines are the sewer network; the dark box at the edge is the outfall.")
 
    total_buildings = houses_per_row * town_rows
    tc1, tc2, tc3, tc4 = st.columns(4)
    tc1.metric("Houses", type_counts["House"])
    tc2.metric("Hospitals", type_counts["Hospital"])
    tc3.metric("Offices", type_counts["Office"])
    tc4.metric("Total Buildings", total_buildings)
 
    rc1, rc2 = st.columns(2)
    rc1.metric("Foundation (typical)", town_result["foundation"])
    rc2.metric("Structural System (typical)", town_result["structural_system"])
 
    footprint_for_cost = [(0, 0, (length / houses_per_row) * 0.65, (width / town_rows) * 0.65)]
    est = estimate_cost_and_materials(footprint_for_cost, house_floors, town_result["structural_system"], town_result["foundation"])
    st.subheader("Estimated Cost (per house / total)")
    tc4b, tc5, tc6 = st.columns(3)
    tc4b.metric("Cost per House", f"PKR {est['total_cost_pkr']:,.0f}")
    tc5.metric("Total Town Cost (approx.)", f"PKR {est['total_cost_pkr']*total_buildings:,.0f}")
    tc6.metric("Rate Used", f"PKR {est['rate_per_sqft']:,.0f} / sq ft")
    st.caption("Total town cost is a rough scaling from a single house's rate — hospital and office blocks in the "
               "layout will cost meaningfully more per sq ft than shown here due to their larger floor counts.")
 
    st.divider()
    st.caption(
        "⚠️ Disclaimer: This is a conceptual town layout only. Actual subdivision, road widths, plot "
        "sizes, and drainage design must comply with local development authority bylaws and must be "
        "designed and approved by a licensed civil engineer / town planner."
    )
 
elif run:
    result = recommend(soil_name, floors, purpose, seismic_zone, groundwater, length, width)
    soil_color = SOIL_DB[soil_name]["color"]
 
    col1, col2, col3 = st.columns(3)
    col1.metric("Foundation Type", result["foundation"])
    col2.metric("Est. Depth (m)", f"{result['depth']:.1f}")
    col3.metric("Structural System", result["structural_system"])
 
    st.subheader("Recommended Building Shapes")
    st.write(", ".join(result["shapes"]))
 
    st.subheader("Explanation")
    st.write(result["explanation"])
 
    if result["warnings"]:
        st.subheader("⚠️ Warnings")
        for w in result["warnings"]:
            st.warning(w)
 
    st.subheader("Estimated Cost & Materials")
    st.caption("Rough, order-of-magnitude planning figures based on covered area — not a substitute for a detailed BOQ.")
    footprint_for_cost = get_footprint(result["shapes"][0], length, width)
    est = estimate_cost_and_materials(footprint_for_cost, floors, result["structural_system"], result["foundation"])
 
    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("Covered Area", f"{est['covered_area_sqft']:,.0f} sq ft")
    ec2.metric("Total Built-up Area", f"{est['total_area_sqft']:,.0f} sq ft")
    ec3.metric("Rate Used", f"PKR {est['rate_per_sqft']:,.0f} / sq ft")
 
    ec4, ec5, ec6 = st.columns(3)
    ec4.metric("Estimated Cost", f"PKR {est['total_cost_pkr']:,.0f}")
    ec5.metric("Concrete (approx.)", f"{est['concrete_m3']:.1f} m³")
    ec6.metric("Steel (approx.)", f"{est['steel_tonnes']:.2f} tonnes")
 
    st.caption(f"Cement (approx.): {est['cement_bags']:.0f} bags · Rate includes structural system + foundation type premium, "
               "but excludes finishing quality, site access, region, and market fluctuation.")
 
    st.subheader("Conceptual 3D Model")
    chosen_shape = st.selectbox("Preview shape", result["shapes"], key="shape_preview")
    fig3d = build_3d_animated_figure(
        chosen_shape, length, width, floors, result["structural_system"],
        soil_color, result["foundation"], result["depth"]
    )
    st.plotly_chart(
        fig3d,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["resetCameraDefault3d", "hoverClosest3d", "tableRotation"],
            "scrollZoom": True,
        },
    )
    st.caption(
        "Drag with your cursor to rotate and tilt the model, scroll to zoom, and use **Build sequence** "
        "(bottom-left) to animate construction floor by floor. The soil beneath grade is shown translucent "
        "so the foundation is visible underneath the building."
    )
 
    st.subheader("Orthographic Views")
    tab1, tab2, tab3 = st.tabs(["Plan View", "Elevation View", "Section View"])
    with tab1:
        st.plotly_chart(build_plan_view(chosen_shape, length, width, soil_name), use_container_width=True)
    with tab2:
        st.plotly_chart(build_elevation_view(length, floors, result["foundation"], result["depth"], soil_name, groundwater), use_container_width=True)
    with tab3:
        st.plotly_chart(build_section_view(width, floors, result["foundation"], result["depth"], soil_name, groundwater), use_container_width=True)
 
    st.divider()
    st.caption(
        "⚠️ Disclaimer: This tool provides conceptual, preliminary suggestions only. "
        "Final building design must consider local building codes, architectural requirements, "
        "wind/seismic analysis, budget, and owner requirements, and must be verified and stamped "
        "by a licensed structural/civil engineer before construction."
    )
else:
    st.markdown("""
    <div style="background:#ffffff; border:1px dashed #cbd5e1; border-radius:10px;
                padding:26px 24px; text-align:center; color:#475569;">
        <div style="font-size:1.4rem; margin-bottom:6px;">👈</div>
        <div style="font-weight:600; color:#1c2b3a; margin-bottom:4px;">Enter your site details in the sidebar</div>
        <div style="font-size:0.9rem;">Click <b>Get Recommendation</b> to generate the foundation type, structural
        system, animated 3D model, and plan/elevation/section drawings.</div>
    </div>
    """, unsafe_allow_html=True)
 
 
