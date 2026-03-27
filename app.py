import streamlit as st
import plotly.express as px
import pandas as pd
import json
import os
import uuid
from datetime import datetime

SIMULATIONS_FILE = "simulations.json"

# ─── Data helpers ────────────────────────────────────────────────────────────

def load_simulations():
    if os.path.exists(SIMULATIONS_FILE):
        with open(SIMULATIONS_FILE, "r") as f:
            return json.load(f)
    return []


def save_simulations(simulations):
    with open(SIMULATIONS_FILE, "w") as f:
        json.dump(simulations, f, indent=2)


# ─── Chart rendering ─────────────────────────────────────────────────────────

def render_chart(chart_type, df, x_col, y_cols, title):
    try:
        if not y_cols:
            return None
        if chart_type == "Pie":
            fig = px.pie(df, names=x_col, values=y_cols[0], title=title)
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_cols, title=title, barmode="group")
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_cols, title=title, markers=True)
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_cols, title=title)
        elif chart_type == "Area":
            fig = px.area(df, x=x_col, y=y_cols, title=title)
        else:
            fig = px.bar(df, x=x_col, y=y_cols, title=title, barmode="group")

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=80, b=40, l=40, r=40),
        )
        return fig
    except Exception as e:
        st.error(f"Chart error: {e}")
        return None


# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Chart Simulation Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .platform-title {
        font-size: 2.2rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .platform-sub {
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="platform-title">📊 Chart Simulation Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="platform-sub">Interactive chart simulations for classroom learning</p>', unsafe_allow_html=True)

# ─── Sidebar role selector ────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Select Role")
    role = st.radio(
        "role",
        ["👨‍🏫 Faculty", "👨‍🎓 Student"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if "Faculty" in role:
        st.info("As **Faculty** you can create and manage chart simulations for your students.")
    else:
        st.info("As **Student** you can pick a simulation, enter values and see your chart come to life.")

simulations = load_simulations()

# ══════════════════════════════════════════════════════════════════════════════
#  FACULTY MODE
# ══════════════════════════════════════════════════════════════════════════════

if "Faculty" in role:
    tab_create, tab_manage = st.tabs(["➕ Create Simulation", "📋 Manage Simulations"])

    # ── CREATE ────────────────────────────────────────────────────────────────
    with tab_create:
        st.subheader("Create a New Simulation")

        c1, c2 = st.columns(2)
        with c1:
            sim_name = st.text_input("Simulation Name", placeholder="e.g., Monthly Sales Analysis")
        with c2:
            chart_type = st.selectbox(
                "Chart Type",
                ["Bar", "Line", "Scatter", "Area", "Pie"],
                help="Pie charts use only the first Y-axis column.",
            )

        st.markdown("---")

        c3, c4 = st.columns(2)
        with c3:
            num_cols = st.number_input(
                "Number of Columns",
                min_value=2,
                max_value=10,
                value=3,
                help="First column = X-axis labels. Remaining = Y-axis data series.",
            )
        with c4:
            num_rows = st.number_input("Number of Data Points (Rows)", min_value=2, max_value=20, value=5)

        st.caption("💡 **First column** is always the X-axis (category labels). Other columns are data series.")

        st.markdown("---")
        st.subheader("Configure Each Column")

        columns_config = []
        valid = True

        for i in range(int(num_cols)):
            label = "Column 1 — X-Axis (Categories)" if i == 0 else f"Column {i+1} — Y-Axis Series {i}"
            with st.expander(label, expanded=True):
                col_name = st.text_input(
                    "Column Name",
                    key=f"col_name_{i}",
                    placeholder="Month" if i == 0 else f"Series {i}",
                )

                is_x = i == 0
                allow_student = False
                default_values = []

                # Grid helper: split values across 5-wide columns
                def value_grid(key_prefix, num, is_text=False, x_vals=None):
                    vals = []
                    row_cols = st.columns(min(int(num), 5))
                    for j in range(int(num)):
                        lbl = x_vals[j] if (x_vals and x_vals[j]) else f"Row {j+1}"
                        with row_cols[j % 5]:
                            if is_text:
                                v = st.text_input(f"#{j+1}", key=f"{key_prefix}_{j}", placeholder=f"Label {j+1}")
                            else:
                                v = st.number_input(lbl, key=f"{key_prefix}_{j}", value=0.0, format="%.2f")
                            vals.append(v)
                    return vals

                if is_x:
                    st.markdown("**X-axis category labels:**")
                    default_values = value_grid(f"x_{i}", num_rows, is_text=True)
                else:
                    # Peek at x values for row labels
                    x_vals_preview = [
                        st.session_state.get(f"x_0_{j}", "") for j in range(int(num_rows))
                    ]
                    fill_opt = st.radio(
                        "Who provides the values?",
                        ["Faculty pre-fills values", "Students will enter values"],
                        key=f"fill_opt_{i}",
                        horizontal=True,
                    )
                    allow_student = fill_opt == "Students will enter values"

                    if allow_student:
                        st.success("Students will fill in this column during the simulation.")
                        default_values = [None] * int(num_rows)
                    else:
                        st.markdown("**Default values (pre-filled for students):**")
                        default_values = value_grid(f"y_{i}", num_rows, is_text=False, x_vals=x_vals_preview)

                columns_config.append(
                    {
                        "name": col_name,
                        "is_x_axis": is_x,
                        "allow_student_input": allow_student,
                        "default_values": default_values,
                    }
                )

        st.markdown("---")

        if st.button("💾 Save Simulation", type="primary", use_container_width=True):
            # Validate
            if not sim_name.strip():
                st.error("Please enter a simulation name.")
            elif any(not c["name"].strip() for c in columns_config):
                st.error("Please fill in all column names.")
            elif any(
                not str(v).strip()
                for v in columns_config[0]["default_values"]
                if v is not None
            ) or len([v for v in columns_config[0]["default_values"] if v]) < int(num_rows):
                st.error("Please fill in all X-axis category labels.")
            elif any(s["name"] == sim_name.strip() for s in simulations):
                st.error(f"A simulation named '{sim_name.strip()}' already exists. Choose a different name.")
            else:
                new_sim = {
                    "id": str(uuid.uuid4()),
                    "name": sim_name.strip(),
                    "chart_type": chart_type,
                    "num_rows": int(num_rows),
                    "columns": columns_config,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                simulations.append(new_sim)
                save_simulations(simulations)
                st.success(f"✅ Simulation **'{sim_name.strip()}'** saved successfully!")
                st.balloons()

    # ── MANAGE ────────────────────────────────────────────────────────────────
    with tab_manage:
        st.subheader("Your Simulations")

        if not simulations:
            st.info("No simulations yet. Create one in the **Create Simulation** tab.")
        else:
            for sim in simulations:
                col_names = [c["name"] for c in sim["columns"]]
                student_cols = [c["name"] for c in sim["columns"] if c.get("allow_student_input")]
                preset_cols = [
                    c["name"]
                    for c in sim["columns"]
                    if not c.get("allow_student_input") and not c["is_x_axis"]
                ]

                with st.expander(
                    f"📊 {sim['name']}  |  {sim['chart_type']} Chart  |  Created: {sim.get('created_at', 'N/A')}"
                ):
                    ca, cb = st.columns([3, 1])
                    with ca:
                        st.markdown(f"**Columns:** {', '.join(col_names)}")
                        st.markdown(f"**Data Points:** {sim['num_rows']}")
                        if preset_cols:
                            st.markdown(f"**Faculty pre-filled:** {', '.join(preset_cols)}")
                        if student_cols:
                            st.markdown(f"**Student input required:** {', '.join(student_cols)}")

                        # Preview chart with preset data
                        x_col = sim["columns"][0]
                        preview_data = {x_col["name"]: x_col["default_values"]}
                        has_preview = False
                        y_col_names = []
                        for col in sim["columns"]:
                            if col["is_x_axis"]:
                                continue
                            if not col["allow_student_input"] and col["default_values"]:
                                preview_data[col["name"]] = col["default_values"]
                                y_col_names.append(col["name"])
                                has_preview = True

                        if has_preview:
                            try:
                                df = pd.DataFrame(preview_data)
                                for yc in y_col_names:
                                    df[yc] = pd.to_numeric(df[yc], errors="coerce").fillna(0)
                                fig = render_chart(
                                    sim["chart_type"], df, x_col["name"], y_col_names, sim["name"] + " (preview)"
                                )
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                            except Exception:
                                pass

                    with cb:
                        if st.button("🗑️ Delete", key=f"del_{sim['id']}", type="secondary"):
                            simulations = [s for s in simulations if s["id"] != sim["id"]]
                            save_simulations(simulations)
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT MODE
# ══════════════════════════════════════════════════════════════════════════════

else:
    st.subheader("👨‍🎓 Student Simulation View")

    if not simulations:
        st.warning("No simulations are available yet. Please ask your faculty to create one.")
    else:
        sim_names = [s["name"] for s in simulations]
        selected_name = st.selectbox("Select a Simulation", sim_names)
        sim = next(s for s in simulations if s["name"] == selected_name)

        st.markdown(f"### 📊 {sim['name']}")
        st.caption(f"Chart type: **{sim['chart_type']}** | Data points: **{sim['num_rows']}**")

        x_col = sim["columns"][0]
        x_values = x_col["default_values"]

        # Build data dict — start with X axis
        data = {x_col["name"]: x_values}

        has_student_inputs = any(
            c["allow_student_input"] for c in sim["columns"] if not c["is_x_axis"]
        )

        if has_student_inputs:
            st.markdown("---")
            st.subheader("📝 Enter Your Values")
            st.caption("Fill in the fields below — the chart updates automatically as you type.")

        y_col_names = []
        for col in sim["columns"]:
            if col["is_x_axis"]:
                continue

            y_col_names.append(col["name"])

            if col["allow_student_input"]:
                st.markdown(f"**{col['name']}**")
                vals = []
                input_cols = st.columns(min(sim["num_rows"], 5))
                for j in range(sim["num_rows"]):
                    lbl = str(x_values[j]) if x_values[j] else f"Row {j+1}"
                    with input_cols[j % 5]:
                        v = st.number_input(
                            lbl,
                            key=f"student_{sim['id']}_{col['name']}_{j}",
                            value=0.0,
                            format="%.2f",
                        )
                        vals.append(v)
                data[col["name"]] = vals
            else:
                data[col["name"]] = col["default_values"]

        # ── Render chart ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📈 Your Chart")

        try:
            df = pd.DataFrame(data)
            for yc in y_col_names:
                df[yc] = pd.to_numeric(df[yc], errors="coerce").fillna(0)

            # For Pie, only first Y column
            plot_y = y_col_names[:1] if sim["chart_type"] == "Pie" else y_col_names
            fig = render_chart(sim["chart_type"], df, x_col["name"], plot_y, sim["name"])

            if fig:
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋 View Data Table"):
                st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Could not render chart: {e}")
