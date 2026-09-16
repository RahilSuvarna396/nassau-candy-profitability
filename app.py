"""
Nassau Candy Distributor — Product Line Profitability & Margin Performance Dashboard
Run with: streamlit run app.py
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nassau Candy | Profitability Dashboard",
    page_icon="🍬",
    layout="wide",
)

NAVY = "#2B2560"
GOLD = "#B8923A"
GREEN = "#7A9B76"
RED = "#B85C5C"
BLUE = "#4C7A9E"
DIVISION_COLORS = {"Chocolate": NAVY, "Sugar": GOLD, "Other": RED}

FACTORY_MAP = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar - Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory",
}


@st.cache_data
def load_data():
    df = pd.read_csv("nassau_candy_cleaned.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Product Name"] = df["Product Name"].str.replace(
        "Wonka Bar -Scrumdiddlyumptious", "Wonka Bar - Scrumdiddlyumptious", regex=False
    )
    df["Factory"] = df["Product Name"].map(FACTORY_MAP)
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"] * 100
    df["Order Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df


df_all = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR — USER CONTROLS
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 🍬 Nassau Candy")
st.sidebar.markdown("**Profitability & Margin Dashboard**")
st.sidebar.divider()

min_date, max_date = df_all["Order Date"].min().date(), df_all["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

divisions = sorted(df_all["Division"].unique())
selected_divisions = st.sidebar.multiselect("Division filter", divisions, default=divisions)

margin_threshold = st.sidebar.slider(
    "Minimum gross margin (%) to include", min_value=0, max_value=100, value=0, step=5
)

product_search = st.sidebar.text_input("Product search", placeholder="e.g. Wonka, Gobstopper...")

st.sidebar.divider()
st.sidebar.caption(
    "Data: 10,194 order lines · Jan 2024 – Dec 2025 · 15 SKUs · 3 divisions"
)

# ---------------------------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------------------------
mask = (
    (df_all["Order Date"].dt.date >= start_date)
    & (df_all["Order Date"].dt.date <= end_date)
    & (df_all["Division"].isin(selected_divisions))
)
df = df_all[mask].copy()

product_margin = df.groupby("Product Name")["Gross Margin %"].transform(
    lambda s: (s * 0 + df.loc[s.index, "Gross Profit"].sum() / df.loc[s.index, "Sales"].sum() * 100)
)
# Product-level margin filter (based on aggregate product margin, not line-level)
prod_agg_margin = df.groupby("Product Name").apply(
    lambda g: g["Gross Profit"].sum() / g["Sales"].sum() * 100
)
allowed_products = prod_agg_margin[prod_agg_margin >= margin_threshold].index
df = df[df["Product Name"].isin(allowed_products)]

if product_search:
    df = df[df["Product Name"].str.contains(product_search, case=False, na=False)]

if df.empty:
    st.warning("No data matches the current filters. Adjust the filters in the sidebar.")
    st.stop()

total_sales = df["Sales"].sum()
total_profit = df["Gross Profit"].sum()
total_cost = df["Cost"].sum()
overall_margin = total_profit / total_sales * 100 if total_sales else 0

# ---------------------------------------------------------------------------
# HEADER + KPI STRIP
# ---------------------------------------------------------------------------
st.title("Product Line Profitability & Margin Performance")
st.caption("Nassau Candy Distributor — interactive analytics")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Gross Profit", f"${total_profit:,.0f}")
k3.metric("Overall Gross Margin", f"{overall_margin:.1f}%")
k4.metric("Units Sold", f"{df['Units'].sum():,.0f}")
k5.metric("Products in View", f"{df['Product Name'].nunique()} / {df_all['Product Name'].nunique()}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Product Profitability", "🏭 Division Performance", "🎯 Cost vs Margin Diagnostics", "📈 Profit Concentration"]
)

# ---------------------------------------------------------------------------
# TAB 1 — PRODUCT PROFITABILITY OVERVIEW
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Product-Level Profitability Leaderboard")

    product = df.groupby(["Division", "Product Name"], as_index=False).agg(
        Sales=("Sales", "sum"), Cost=("Cost", "sum"), Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
    )
    product["Gross Margin %"] = product["Gross_Profit"] / product["Sales"] * 100
    product["Profit per Unit"] = product["Gross_Profit"] / product["Units"]
    product["Revenue Contribution %"] = product["Sales"] / total_sales * 100
    product["Profit Contribution %"] = product["Gross_Profit"] / total_profit * 100
    product = product.sort_values("Gross_Profit", ascending=False)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = px.bar(
            product.sort_values("Gross_Profit"), x="Gross_Profit", y="Product Name", color="Division",
            orientation="h", color_discrete_map=DIVISION_COLORS,
            labels={"Gross_Profit": "Gross Profit ($)"}, title="Gross Profit by Product",
        )
        fig.update_layout(height=480, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.pie(
            product, values="Profit Contribution %", names="Product Name", title="Profit Contribution Share",
            hole=0.45,
        )
        fig2.update_layout(height=480, showlegend=False)
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Product Detail Table")
    show = product[[
        "Product Name", "Division", "Sales", "Cost", "Gross_Profit", "Units",
        "Gross Margin %", "Profit per Unit", "Revenue Contribution %", "Profit Contribution %",
    ]].rename(columns={"Gross_Profit": "Gross Profit"})
    st.dataframe(
        show.style.format({
            "Sales": "${:,.0f}", "Cost": "${:,.0f}", "Gross Profit": "${:,.0f}",
            "Units": "{:,.0f}", "Gross Margin %": "{:.1f}%", "Profit per Unit": "${:.2f}",
            "Revenue Contribution %": "{:.1f}%", "Profit Contribution %": "{:.1f}%",
        }).background_gradient(subset=["Gross Margin %"], cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True, height=420,
    )

# ---------------------------------------------------------------------------
# TAB 2 — DIVISION PERFORMANCE DASHBOARD
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Division Performance")

    division = df.groupby("Division", as_index=False).agg(
        Sales=("Sales", "sum"), Cost=("Cost", "sum"), Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
    )
    division["Gross Margin %"] = division["Gross_Profit"] / division["Sales"] * 100
    division["Revenue %"] = division["Sales"] / total_sales * 100
    division["Profit %"] = division["Gross_Profit"] / total_profit * 100
    division["Rev-Profit Gap"] = division["Profit %"] - division["Revenue %"]

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=division["Division"], y=division["Revenue %"], name="Revenue %", marker_color=BLUE)
        fig.add_bar(x=division["Division"], y=division["Profit %"], name="Profit %", marker_color=NAVY)
        fig.update_layout(barmode="group", title="Revenue vs. Profit Contribution by Division", height=420)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            division, x="Division", y="Gross Margin %", color="Division",
            color_discrete_map=DIVISION_COLORS, title="Average Gross Margin by Division",
        )
        fig.add_hline(y=overall_margin, line_dash="dash", line_color="gray",
                       annotation_text=f"Company avg {overall_margin:.1f}%")
        fig.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Margin Distribution by Division (order-line level)")
    fig = px.box(
        df, x="Division", y="Gross Margin %", color="Division", color_discrete_map=DIVISION_COLORS,
        points="outliers",
    )
    fig.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Division Summary Table")
    st.dataframe(
        division[["Division", "Sales", "Gross_Profit", "Gross Margin %", "Revenue %", "Profit %", "Rev-Profit Gap"]]
        .rename(columns={"Gross_Profit": "Gross Profit"})
        .style.format({
            "Sales": "${:,.0f}", "Gross Profit": "${:,.0f}", "Gross Margin %": "{:.1f}%",
            "Revenue %": "{:.1f}%", "Profit %": "{:.1f}%", "Rev-Profit Gap": "{:+.1f} pts",
        }),
        use_container_width=True,
    )

    st.markdown("#### Factory / Sourcing View")
    factory = df.groupby("Factory", as_index=False).agg(
        Sales=("Sales", "sum"), Gross_Profit=("Gross Profit", "sum")
    )
    factory["Gross Margin %"] = factory["Gross_Profit"] / factory["Sales"] * 100
    factory = factory.sort_values("Gross_Profit", ascending=False)
    fig = px.bar(factory, x="Factory", y="Gross Margin %", color="Gross Margin %",
                 color_continuous_scale="RdYlGn", range_color=[0, 80])
    fig.add_hline(y=overall_margin, line_dash="dash", line_color="gray")
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3 — COST VS MARGIN DIAGNOSTICS
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Cost Structure Diagnostics")

    product = df.groupby(["Division", "Product Name"], as_index=False).agg(
        Sales=("Sales", "sum"), Cost=("Cost", "sum"), Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
    )
    product["Gross Margin %"] = product["Gross_Profit"] / product["Sales"] * 100
    product["Cost Ratio %"] = product["Cost"] / product["Sales"] * 100
    avg_cost_ratio = total_cost / total_sales * 100

    fig = px.scatter(
        product, x="Sales", y="Cost Ratio %", color="Division", size="Gross_Profit",
        hover_name="Product Name", color_discrete_map=DIVISION_COLORS, log_x=True,
        size_max=45, title="Cost Ratio vs. Sales (bubble size = gross profit)",
    )
    fig.add_hline(y=avg_cost_ratio, line_dash="dash", line_color="gray",
                   annotation_text=f"Avg cost ratio {avg_cost_ratio:.1f}%")
    fig.update_layout(height=480)
    st.plotly_chart(fig, use_container_width=True)

    overall_margin_ratio = overall_margin
    product["Margin Risk"] = np.where(
        (product["Gross Margin %"] < overall_margin_ratio) & (product["Cost Ratio %"] > avg_cost_ratio),
        "🔴 Flagged", "🟢 OK",
    )
    flagged = product[product["Margin Risk"] == "🔴 Flagged"].sort_values("Cost Ratio %", ascending=False)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### Margin Risk Flags")
        st.caption("Flagged = below-average margin AND above-average cost ratio")
        st.dataframe(
            flagged[["Product Name", "Division", "Gross Margin %", "Cost Ratio %", "Gross_Profit"]]
            .rename(columns={"Gross_Profit": "Gross Profit"})
            .style.format({"Gross Margin %": "{:.1f}%", "Cost Ratio %": "{:.1f}%", "Gross Profit": "${:,.0f}"}),
            use_container_width=True, height=420,
        )
    with c2:
        st.markdown("#### Sourcing / Repricing Priority")
        st.caption("Highest cost-ratio products — best candidates for repricing or cost renegotiation")
        fig2 = px.bar(
            flagged.sort_values("Cost Ratio %"), x="Cost Ratio %", y="Product Name",
            orientation="h", color="Division", color_discrete_map=DIVISION_COLORS,
        )
        fig2.update_layout(height=420, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4 — PROFIT CONCENTRATION (PARETO) ANALYSIS
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Profit Concentration (Pareto) Analysis")

    product = df.groupby("Product Name", as_index=False).agg(
        Sales=("Sales", "sum"), Gross_Profit=("Gross Profit", "sum")
    )
    pareto_profit = product.sort_values("Gross_Profit", ascending=False).reset_index(drop=True)
    pareto_profit["Cum Profit %"] = pareto_profit["Gross_Profit"].cumsum() / total_profit * 100
    n80 = int((pareto_profit["Cum Profit %"] <= 80).sum() + 1)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=pareto_profit["Product Name"], y=pareto_profit["Gross_Profit"], name="Gross Profit", marker_color=NAVY)
        fig.add_trace(go.Scatter(
            x=pareto_profit["Product Name"], y=pareto_profit["Cum Profit %"], name="Cumulative %",
            yaxis="y2", mode="lines+markers", line_color=RED,
        ))
        fig.add_hline(y=80, line_dash="dash", line_color="gray", yref="y2")
        fig.update_layout(
            title="Product Pareto — Profit Concentration",
            yaxis=dict(title="Gross Profit ($)"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
            height=460, legend=dict(orientation="h", y=1.15),
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.metric("Products driving 80% of profit", f"{n80} of {len(pareto_profit)}",
                   f"{n80/len(pareto_profit)*100:.0f}% of catalog")
        state_sales = df.groupby("State/Province", as_index=False)["Sales"].sum().sort_values(
            "Sales", ascending=False
        ).reset_index(drop=True)
        state_sales["Cum %"] = state_sales["Sales"].cumsum() / total_sales * 100
        n_states_80 = int((state_sales["Cum %"] <= 80).sum() + 1)
        st.metric("States driving 80% of revenue", f"{n_states_80} of {df['State/Province'].nunique()}",
                   f"{n_states_80/df['State/Province'].nunique()*100:.0f}% of states")
        fig3 = px.bar(state_sales.head(15), x="State/Province", y="Sales", title="Top 15 States by Sales")
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, use_container_width=True)

    st.info(
        f"**Dependency insight:** {n80} product(s) generate 80% of total gross profit, "
        f"versus {n_states_80} states needed to reach 80% of revenue — profit is more concentrated "
        f"by product than revenue is by geography, meaning product-mix risk outweighs geographic risk."
    )

st.divider()
st.caption("Nassau Candy Distributor · Product Line Profitability & Margin Performance Analysis · Built with Streamlit")
