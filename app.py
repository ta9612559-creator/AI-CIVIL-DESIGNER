import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="AI Civil Designer", layout="wide")

# -----------------------------
# 3D BOX / SHAPE HELPERS
# -----------------------------

def make_box_mesh(x0, y0, z0, dx, dy, dz, color, opacity=1.0):
    """Return a go.Mesh3d cuboid starting at (x0,y0,z0) with size (dx,dy,dz)."""
    x = [x0, x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx]
    y = [y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy, y0]
    z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]

    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 0, 3]
    j = [1, 3, 5, 7, 1, 4, 2, 5, 3, 6, 4, 7]
    k = [2, 2, 6, 6, 4, 5, 5, 6, 6, 7, 7, 4]

    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=opacity, flatshading=True,
        showscale=False
    )


def get_footprint(shape, length, width):
    """Return list of (x0, y0, dx, dy) rectangles approximating the footprint."""
    if shape == "Rectangular" or shape == "Square":
        return [(0, 0, length, width)]

    if shape == "L-shaped":
        return [
            (0, 0, length, width * 0.55),
            (0, width * 0.55, length * 0.45, width * 0.45),
        ]

    if shape == "U-shaped":
        arm_w = width * 0.3
        return [
            (0, 0, length, arm_w),
            (0, arm_w, arm_w, width - arm_w),
            (length - arm_w, arm_w, arm_w, width - arm_w),
        ]

    return [(0, 0, length, width)]


def build_3d_figure(shape, length, width, floors, structural_system):
    floor_height = 3.0
    color_map = {
        "RC Frame": "#8c9aa8",
        "Shear Wall System": "#4a7fb5",
        "Steel Frame": "#d98f3b",
    }
    color = color_map.get(structural_system, "#8c9aa8")

    footprint = get_footprint(shape, length, width)
    meshes = []

    for f in range(floors):
        z0 = f * floor_height
        opacity = 0.95 if f == floors - 1 else 0.75
        for (x0, y0, dx, dy) in footprint:
            meshes.append(make_box_mesh(x0, y0, z0, dx, dy, floor_height * 0.92, color, opacity))

    # simple ground plane for context
    ground = go.Mesh3d(
        x=[-length*0.3, length*1.3, length*1.3, -length*0.3],
        y=[-width*0.3, -width*0.3, width*1.3, width*1.3],
        z=[0, 0, 0, 0],
        i=[0], j=[1], k=[2],
        color="#e8e4d8", opacity=0.5
    )
    ground2 = go.Mesh3d(
        x=[-length*0.3, length*1.3, -length*0.3],
        y=[-width*0.3, width*1.3, width*1.3],
        z=[0, 0, 0],
        i=[0], j=[1], k=[2],
        color="#e8e4d8", opacity=0.5
    )

    fig = go.Figure(data=[ground, ground2] + meshes)
    fig.update_layout(
        scene=dict(
            xaxis_title="Length (m)",
            yaxis_title="Width (m)",
            zaxis_title="Height (m)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=550,
    )
    return fig


# -----------------------------
# RECOMMENDATION LOGIC (rule-based)
# -----------------------------

def recommend(soil_type, bearing_capacity, floors, purpose, seismic_zone,
              groundwater, length, width):
    warnings = []
    explanation_parts = []

    # --- Foundation type ---
    high_load = floors >= 6 or purpose in ("hospital", "warehouse")
    weak_soil = soil_type in ("clay", "silt")

    if soil_type == "rock":
        foundation = "Isolated Footing"
        depth = 1.0
        explanation_parts.append(
            "Rock has very high bearing capacity, so shallow isolated footings are usually sufficient."
        )
    elif weak_soil and high_load:
        foundation = "Pile Foundation"
        depth = 8.0
        explanation_parts.append(
            f"{soil_type.capitalize()} soil combined with a heavier structure means loads should be "
            "transferred to deeper, stronger strata using piles rather than relying on the surface soil."
        )
    elif weak_soil:
        foundation = "Raft Foundation"
        depth = 2.0
        explanation_parts.append(
            f"On {soil_type} soil, a raft foundation spreads the building load over a larger area, "
            "which helps limit differential settlement compared to isolated footings."
        )
        warnings.append(f"{soil_type.capitalize()} soil may experience settlement over time; monitor for cracks.")
    elif soil_type == "sand":
        foundation = "Strip Footing" if floors <= 3 else "Raft Foundation"
        depth = 1.5
        explanation_parts.append(
            "Sandy soil generally drains well and has moderate bearing capacity, suiting strip or raft footings "
            "depending on building height."
        )
    else:  # gravel or unspecified
        foundation = "Isolated Footing"
        depth = 1.2
        explanation_parts.append(
            "This soil type generally offers reasonable bearing capacity for isolated footings at moderate depth."
        )

    if bearing_capacity is not None and bearing_capacity < 100 and foundation == "Isolated Footing":
        foundation = "Raft Foundation"
        explanation_parts.append(
            "The reported bearing capacity is quite low, so spreading the load with a raft is safer than "
            "isolated footings."
        )

    # --- Groundwater adjustment ---
    if groundwater == "High (< 2m)":
        warnings.append("High groundwater table detected. Waterproofing and dewatering during construction will be needed.")
        depth = min(depth, 1.5)
        explanation_parts.append(
            "Since the groundwater table is shallow, the foundation depth is kept conservative to reduce "
            "water-related construction issues."
        )

    # --- Structural system ---
    if seismic_zone in ("High", "Severe") and floors >= 4:
        structural_system = "Shear Wall System"
        explanation_parts.append(
            "In a high seismic zone with a multi-story building, shear walls provide better lateral stability "
            "than a frame alone."
        )
    elif floors >= 8:
        structural_system = "Steel Frame"
        explanation_parts.append(
            "For taller buildings, steel framing offers a good strength-to-weight ratio and faster construction."
        )
    else:
        structural_system = "RC Frame"
        explanation_parts.append(
            "For this height and load, a conventional RC frame is a practical and economical choice."
        )

    # --- Building shape suggestions ---
    aspect_ratio = max(length, width) / max(min(length, width), 0.1)
    if aspect_ratio > 2.5:
        shapes = ["Rectangular"]
        warnings.append("Plot is quite elongated; avoid highly irregular shapes to reduce torsional effects in earthquakes.")
    elif purpose in ("school", "hospital"):
        shapes = ["U-shaped", "L-shaped", "Rectangular"]
    else:
        shapes = ["Rectangular", "Square", "L-shaped"]

    if seismic_zone in ("High", "Severe"):
        shapes = [s for s in shapes if s in ("Rectangular", "Square")] or ["Rectangular"]
        warnings.append("In high seismic zones, simple symmetric shapes (rectangular/square) perform better than irregular ones.")

    result = {
        "foundation": foundation,
        "depth": depth,
        "structural_system": structural_system,
        "shapes": shapes,
        "warnings": warnings,
        "explanation": " ".join(explanation_parts),
    }
    return result


# -----------------------------
# UI
# -----------------------------

st.title("🏗️ AI Civil Designer")
st.caption("Conceptual foundation & layout recommendations based on site conditions")

with st.sidebar:
    st.header("Site & Building Inputs")
    soil_type = st.selectbox("Soil type", ["clay", "sand", "silt", "gravel", "rock"])
    bearing_capacity = st.number_input("Bearing capacity (kPa) — optional, 0 = unknown", min_value=0, value=0, step=10)
    length = st.number_input("Plot length (m)", min_value=3.0, value=20.0, step=1.0)
    width = st.number_input("Plot width (m)", min_value=3.0, value=12.0, step=1.0)
    floors = st.slider("Number of floors", 1, 15, 3)
    purpose = st.selectbox("Building purpose", ["house", "school", "hospital", "office", "warehouse"])
    seismic_zone = st.selectbox("Earthquake zone", ["Low", "Moderate", "High", "Severe"])
    groundwater = st.selectbox("Groundwater level", ["High (< 2m)", "Moderate (2-5m)", "Low (> 5m)"])
    run = st.button("Get Recommendation", type="primary", use_container_width=True)

if run:
    bc = bearing_capacity if bearing_capacity > 0 else None
    result = recommend(soil_type, bc, floors, purpose, seismic_zone, groundwater, length, width)

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

    st.subheader("Conceptual 3D Visualization")
    chosen_shape = st.selectbox("Preview shape", result["shapes"], key="shape_preview")
    fig = build_3d_figure(chosen_shape, length, width, floors, result["structural_system"])
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.caption(
        "⚠️ Disclaimer: This tool provides conceptual, preliminary suggestions only. "
        "Final building design must consider local building codes, architectural requirements, "
        "wind/seismic analysis, budget, and owner requirements, and must be verified and stamped "
        "by a licensed structural/civil engineer before construction."
    )
else:
    st.info("Fill in the site details in the sidebar and click **Get Recommendation** to see suggestions and a 3D preview.")
