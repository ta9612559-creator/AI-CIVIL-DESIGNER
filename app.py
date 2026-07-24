
import streamlit as st
import plotly.graph_objects as go
import numpy as np
 
st.set_page_config(page_title="AI Civil Designer", layout="wide")
 
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
    "RC Frame": "#8c9aa8",
    "Shear Wall System": "#4a7fb5",
    "Steel Frame": "#d98f3b",
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
    elif purpose in ("school", "hospital"):
        shapes = ["U-shaped", "L-shaped", "Rectangular"]
    else:
        shapes = ["Rectangular", "Square", "L-shaped"]
 
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
    return [(0, 0, length, width)]
 
 
# =========================================================
# 3D ANIMATED MODEL
# =========================================================
 
def make_box_mesh(x0, y0, z0, dx, dy, dz, color, opacity=1.0):
    x = [x0, x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx]
    y = [y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy, y0]
    z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 0, 3]
    j = [1, 3, 5, 7, 1, 4, 2, 5, 3, 6, 4, 7]
    k = [2, 2, 6, 6, 4, 5, 5, 6, 6, 7, 7, 4]
    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity,
        flatshading=True, showscale=False,
        lighting=dict(ambient=0.55, diffuse=0.85, specular=0.4, roughness=0.4, fresnel=0.2),
        lightposition=dict(x=200, y=200, z=400),
    )
 
 
def ground_plane_traces(length, width, soil_color):
    pad = 0.4
    x = [-length*pad, length*(1+pad), length*(1+pad), -length*pad]
    y = [-width*pad, -width*pad, width*(1+pad), width*(1+pad)]
    g1 = go.Mesh3d(x=x, y=y, z=[0,0,0,0], i=[0], j=[1], k=[2], color=soil_color, opacity=0.9)
    g2 = go.Mesh3d(x=[x[0], x[2], x[3]], y=[y[0], y[2], y[3]], z=[0,0,0], i=[0], j=[1], k=[2], color=soil_color, opacity=0.9)
    return [g1, g2]
 
 
def build_3d_animated_figure(shape, length, width, floors, structural_system, soil_color):
    floor_height = 3.0
    color = STRUCT_COLOR.get(structural_system, "#8c9aa8")
    footprint = get_footprint(shape, length, width)
    ground = ground_plane_traces(length, width, soil_color)
 
    frames = []
    max_traces = len(ground) + floors * len(footprint)
 
    for f in range(1, floors + 1):
        frame_data = list(ground)
        for lvl in range(f):
            z0 = lvl * floor_height
            opacity = 0.97 if lvl == f - 1 else 0.8
            for (x0, y0, dx, dy) in footprint:
                frame_data.append(make_box_mesh(x0, y0, z0, dx, dy, floor_height * 0.92, color, opacity))
        frames.append(go.Frame(data=frame_data, name=str(f)))
 
    fig = go.Figure(data=frames[-1].data, frames=frames)
    fig.update_layout(
        scene=dict(
            xaxis_title="Length (m)", yaxis_title="Width (m)", zaxis_title="Height (m)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.1)),
            xaxis=dict(backgroundcolor="rgb(235,240,245)"),
            yaxis=dict(backgroundcolor="rgb(235,240,245)"),
            zaxis=dict(backgroundcolor="rgb(245,248,250)"),
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=600,
        paper_bgcolor="rgba(0,0,0,0)",
        updatemenus=[dict(
            type="buttons", showactive=False, y=0, x=0, xanchor="left", yanchor="bottom",
            buttons=[
                dict(label="▶ Build Animation", method="animate",
                     args=[None, {"frame": {"duration": 450, "redraw": True}, "fromcurrent": True, "transition": {"duration": 200}}]),
                dict(label="⟲ Reset", method="animate",
                     args=[[frames[0].name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]),
            ]
        )],
    )
    return fig
 
 
# =========================================================
# 2D ORTHOGRAPHIC VIEWS (Plan / Elevation / Section)
# =========================================================
 
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
 
st.title("🏗️ AI Civil Designer")
st.caption("Conceptual foundation & layout recommendations based on site conditions")
 
with st.sidebar:
    st.header("Site & Building Inputs")
    soil_name = st.selectbox("Soil type", list(SOIL_DB.keys()))
    length = st.number_input("Plot length (m)", min_value=3.0, value=20.0, step=1.0)
    width = st.number_input("Plot width (m)", min_value=3.0, value=12.0, step=1.0)
    floors = st.slider("Number of floors", 1, 15, 3)
    purpose = st.selectbox("Building purpose", ["house", "school", "hospital", "office", "warehouse"])
    seismic_zone = st.selectbox("Earthquake zone", ["Low", "Moderate", "High", "Severe"])
    groundwater = st.selectbox("Groundwater level", ["High (< 2m)", "Moderate (2-5m)", "Low (> 5m)"])
    run = st.button("Get Recommendation", type="primary", use_container_width=True)
 
if run:
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
 
    st.subheader("Conceptual 3D Model")
    chosen_shape = st.selectbox("Preview shape", result["shapes"], key="shape_preview")
    fig3d = build_3d_animated_figure(chosen_shape, length, width, floors, result["structural_system"], soil_color)
    st.plotly_chart(fig3d, use_container_width=True)
    st.caption("Click **▶ Build Animation** (bottom-left of the chart) to watch the building rise floor by floor. Drag to rotate, scroll to zoom.")
 
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
    st.info("Fill in the site details in the sidebar and click **Get Recommendation** to see suggestions, the animated 3D model, and plan/elevation/section views.")
