"""
AI Data Center Sustainability & Energy Intelligence — dashboard.

Run with: streamlit run dashboard/app.py
Reads only from data/processed/ — regenerate those via
notebooks/clean_data_centers.ipynb if they're missing or stale.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = "../data/processed"

st.set_page_config(page_title="AI Data Center Sustainability & Energy Intelligence", layout="wide")

EPOCH_NAME_MAP = {
    "South Korea": "Korea (Republic of)",
    "Philippines": "Philippines (the)",
    "United Kingdom": "United Kingdom of Great Britain and Northern Ireland",
    "United States": "United States of America",
}


@st.cache_data
def load_data():
    dc = pd.read_csv(f"{DATA_DIR}/data_centers_clean.csv")
    gpu = pd.read_csv(f"{DATA_DIR}/gpu_clusters_clean.csv")
    timelines = pd.read_csv(f"{DATA_DIR}/data_center_timelines_clean.csv", parse_dates=["date"])
    sustainability = pd.read_csv(f"{DATA_DIR}/owid_country_sustainability_clean.csv")
    prices = pd.read_csv(f"{DATA_DIR}/electricity_price_clean.csv")
    co2 = pd.read_csv(f"{DATA_DIR}/owid_co2_clean.csv")

    gpu["country_epoch"] = gpu["country"].replace(EPOCH_NAME_MAP)

    country = (
        gpu.groupby("country")
        .agg(clusters=("name", "count"), total_power_mw=("power_capacity_mw", "sum"))
        .reset_index()
        .merge(sustainability[["country_epoch", "iso_code", "renewables_share_elec", "carbon_intensity_elec"]],
               left_on="country", right_on="country_epoch", how="left")
        .merge(prices[["country_epoch", "price_usd_per_kwh"]], on="country_epoch", how="left")
        .merge(co2[["country_epoch", "co2", "co2_per_capita"]], on="country_epoch", how="left")
        .drop(columns=["country_epoch"])
    )
    return dc, gpu, timelines, country


dc, gpu, timelines, country = load_data()
country_active = country[country["clusters"] >= 3].copy()

st.title("AI Data Center Sustainability & Energy Intelligence")
st.caption(
    "As AI adoption accelerates, what factors make a country an ideal location for "
    "efficient and sustainable AI data centers? Combines Epoch AI infrastructure data "
    "with OWID electricity/emissions data and a compiled electricity-price snapshot."
)

tab_overview, tab_map, tab_energy, tab_infra, tab_compare = st.tabs(
    ["🌍 Overview", "🗺️ Interactive Map", "⚡ Energy Analysis", "📈 AI Infrastructure", "🔍 Country Comparison"]
)

# ----------------------------------------------------------------------------
with tab_overview:
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI Infrastructure Sites", f"{len(gpu):,}", help="Rows in gpu_clusters_clean.csv (broad survey)")
    col2.metric("Total Power Capacity", f"{gpu['power_capacity_mw'].sum():,.0f} MW")
    col3.metric("Countries Covered", f"{gpu['country'].nunique()}")
    col4.metric("Avg. Renewable Share", f"{country_active['renewables_share_elec'].mean():.1f}%",
                help="Mean across countries with 3+ GPU clusters")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.markdown("**Top 10 countries by GPU cluster count**")
        top10 = country.sort_values("clusters", ascending=False).head(10)
        fig = px.bar(top10, x="clusters", y="country", orientation="h",
                     labels={"clusters": "GPU Clusters", "country": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("**Top 10 owners by curated data center count**")
        top_owners = dc["owner_name"].value_counts().head(10).reset_index()
        top_owners.columns = ["owner", "count"]
        fig = px.bar(top_owners, x="count", y="owner", orientation="h",
                     labels={"count": "Data Centers", "owner": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Note: `data_centers_clean.csv` (74 rows) is Epoch AI's curated set of the "
        "largest/most notable sites, heavily US-weighted. `gpu_clusters_clean.csv` "
        "(482 rows) is a broader global survey — used for most KPIs above."
    )

# ----------------------------------------------------------------------------
with tab_map:
    st.subheader("Interactive Map")
    f1, f2 = st.columns(2)
    with f1:
        owner_options = sorted(gpu["owner"].dropna().unique())
        selected_owners = st.multiselect("Filter by operator", owner_options)
    with f2:
        country_options = sorted(gpu["country"].dropna().unique())
        selected_countries = st.multiselect("Filter by country", country_options)

    filtered = gpu.copy()
    if selected_owners:
        filtered = filtered[filtered["owner"].isin(selected_owners)]
    if selected_countries:
        filtered = filtered[filtered["country"].isin(selected_countries)]

    st.markdown("**GPU cluster concentration by country**")
    # Linear color scale would make every country except the US/China (119, 188)
    # visually indistinguishable from zero — log-color them instead, same fix
    # used for this chart in 02_EDA.ipynb.
    choropleth_source = country[country["iso_code"].notna()].copy()
    choropleth_source["log_clusters"] = np.log10(choropleth_source["clusters"])
    tick_vals = [0, 1, 2, 3]
    tick_text = ["1", "10", "100", "1000"]
    fig = px.choropleth(choropleth_source, locations="iso_code", color="log_clusters",
                         color_continuous_scale="YlOrRd", hover_name="country",
                         hover_data={"clusters": True, "log_clusters": False, "iso_code": False})
    fig.update_geos(showcountries=True, countrycolor="lightgray", landcolor="whitesmoke")
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0),
                       coloraxis_colorbar=dict(title="GPU Clusters", tickvals=tick_vals, ticktext=tick_text))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**Individual site locations** ({len(filtered.dropna(subset=['latitude', 'longitude']))} shown)")
    geo = filtered.dropna(subset=["latitude", "longitude"]).copy()
    # scatter_geo's size can't take NaN (60 of 459 sites have no reported power) —
    # give those a small floor so they still show up as small dots, not crash.
    geo["size_mw"] = geo["power_capacity_mw"].fillna(0).clip(lower=0.5)
    fig2 = px.scatter_geo(geo, lat="latitude", lon="longitude", size="size_mw",
                           hover_name="name", hover_data={"owner": True, "country": True, "power_capacity_mw": True,
                                                           "size_mw": False, "latitude": False, "longitude": False},
                           color="country" if selected_countries else None, opacity=0.7)
    fig2.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, use_container_width=True)

# ----------------------------------------------------------------------------
with tab_energy:
    st.subheader("Energy Analysis")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Electricity price by country (lowest 15 among active AI hosts)**")
        cheapest = country_active.dropna(subset=["price_usd_per_kwh"]).sort_values("price_usd_per_kwh").head(15)
        fig = px.bar(cheapest, x="price_usd_per_kwh", y="country", orientation="h",
                     labels={"price_usd_per_kwh": "USD/kWh", "country": ""})
        fig.update_layout(yaxis={"categoryorder": "total descending"}, height=450)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Renewable energy share by country**")
        renew = country_active.dropna(subset=["renewables_share_elec"]).sort_values("renewables_share_elec", ascending=False)
        fig = px.bar(renew, x="renewables_share_elec", y="country", orientation="h",
                     labels={"renewables_share_elec": "Renewable %", "country": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Estimated emissions — total CO2 (bubble size) vs. carbon intensity of electricity**")
    emissions = country_active.dropna(subset=["co2", "carbon_intensity_elec"])
    fig = px.scatter(emissions, x="renewables_share_elec", y="carbon_intensity_elec", size="co2",
                      color="co2_per_capita", hover_name="country", size_max=50,
                      color_continuous_scale="Reds",
                      labels={"renewables_share_elec": "Renewable Share (%)",
                              "carbon_intensity_elec": "Carbon Intensity (gCO2/kWh)",
                              "co2_per_capita": "CO2 per capita (t)"})
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size = total national CO2 emissions (million tonnes/year, from OWID) — a country-level "
               "figure, not attributable to AI infrastructure specifically.")

# ----------------------------------------------------------------------------
with tab_infra:
    st.subheader("AI Infrastructure")

    st.markdown("**Capacity trend — cumulative power build-out over time (top 5 sites)**")
    top5_names = dc.sort_values("current_power_mw", ascending=False).head(5)["name"]
    top5_timeline = timelines[timelines["data_center"].isin(top5_names)]
    fig = px.line(top5_timeline.sort_values("date"), x="date", y="power_mw", color="data_center", markers=True,
                  labels={"power_mw": "Power (MW)", "date": "Date", "data_center": "Site"})
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Provider comparison — footprint by total power capacity**")
    owner_power = gpu.dropna(subset=["owner"]).groupby("owner")["power_capacity_mw"].sum().sort_values(ascending=False).head(15).reset_index()
    fig = px.treemap(owner_power, path=["owner"], values="power_capacity_mw",
                      labels={"power_capacity_mw": "MW"})
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**Sustainability ranking — cost + renewable + carbon, z-scored composite ({len(country_active)} countries)**")
    cs = country_active.dropna(subset=["price_usd_per_kwh", "renewables_share_elec", "carbon_intensity_elec"]).copy()
    z = lambda s: (s - s.mean()) / s.std()
    cs["score"] = (-z(cs["price_usd_per_kwh"]) + z(cs["renewables_share_elec"]) - z(cs["carbon_intensity_elec"])) / 3
    cs = cs.sort_values("score", ascending=False)
    fig = px.bar(cs, x="score", y="country", orientation="h", color="score",
                 color_continuous_scale="RdYlGn", labels={"score": "Balance Score", "country": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=650, coloraxis_showscale=False,
                       margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
with tab_compare:
    st.subheader("Country Comparison")
    default = [c for c in ["Germany", "France", "Netherlands"] if c in country_active["country"].values]
    if len(default) < 2:
        default = country_active.sort_values("clusters", ascending=False)["country"].head(3).tolist()
    picked = st.multiselect("Compare countries", sorted(country_active["country"].unique()), default=default)

    if len(picked) >= 2:
        comp = country_active[country_active["country"].isin(picked)].set_index("country")
        metrics = ["clusters", "total_power_mw", "renewables_share_elec", "carbon_intensity_elec", "price_usd_per_kwh", "co2_per_capita"]
        labels = {"clusters": "GPU Clusters", "total_power_mw": "Total Power (MW)",
                  "renewables_share_elec": "Renewable Share (%)", "carbon_intensity_elec": "Carbon Intensity (gCO2/kWh)",
                  "price_usd_per_kwh": "Electricity Price (USD/kWh)", "co2_per_capita": "CO2 per capita (t)"}
        st.dataframe(comp[metrics].rename(columns=labels).round(2), use_container_width=True)

        norm = comp[metrics].copy()
        for m in metrics:
            span = norm[m].max() - norm[m].min()
            norm[m] = 50 if span == 0 else (norm[m] - norm[m].min()) / span * 100
        norm = norm.rename(columns=labels).reset_index().melt(id_vars="country", var_name="metric", value_name="normalized")
        fig = px.line_polar(norm, r="normalized", theta="metric", color="country", line_close=True)
        fig.update_layout(height=500, polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Radar values are min-max normalized across the selected countries only (0-100), "
                   "for shape comparison — not real units. See the table above for actual values.")
    else:
        st.info("Pick at least 2 countries to compare.")
