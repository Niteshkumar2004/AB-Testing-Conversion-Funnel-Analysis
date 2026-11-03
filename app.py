import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
from pathlib import Path
from math import sqrt

st.set_page_config(page_title="A/B Testing & Conversion Funnel",page_icon="🧪",layout="wide")
ROOT=Path(__file__).parent
st.markdown("""
<style>
.stApp{background:#F5F8FC}
[data-testid="stMetric"]{background:BLUE;padding:16px;border:1px solid #E5EAF1;border-radius:14px}
.hero{padding:24px 28px;background:linear-gradient(110deg,#102A43,#2563EB);border-radius:18px;color:white;margin-bottom:18px}
.hero h1{color:white;margin:0;font-size:2rem}.hero p{color:#DBEAFE;margin:8px 0 0}
</style>
<div class="hero"><h1>A/B Testing & Product Conversion Funnel</h1>
<p>Measure experiment impact, statistical confidence, and user journey drop-offs before launch.</p></div>
""",unsafe_allow_html=True)

@st.cache_data
def load(file):
    return pd.read_csv(file,parse_dates=["event_time"])
up=st.sidebar.file_uploader("Upload event log CSV (optional)",type=["csv"])
try: raw=load(up if up is not None else ROOT/"data/events.csv")
except Exception as e: st.error(f"Could not read file: {e}"); st.stop()

required={"user_id","group","event_name","event_time","revenue"}
missing=required-set(raw.columns)
if missing: st.error("Missing required columns: "+", ".join(sorted(missing))); st.stop()
raw["event_time"]=pd.to_datetime(raw.event_time,errors="coerce")
raw["revenue"]=pd.to_numeric(raw.revenue,errors="coerce").fillna(0)
raw=raw.dropna(subset=["user_id","group","event_name","event_time"])
raw=raw[raw.group.isin(["Control","Variant"])]
steps=["landing_page","add_to_cart","checkout","purchase"]
raw=raw[raw.event_name.isin(steps)]
if raw.empty: st.warning("No valid events found."); st.stop()

with st.sidebar:
    st.header("Experiment filters")
    groups=st.multiselect("Experiment groups",["Control","Variant"],default=["Control","Variant"])
    devices=sorted(raw.device.dropna().astype(str).unique()) if "device" in raw else []
    chosen_devices=st.multiselect("Devices",devices,default=devices) if devices else []
    alpha=st.selectbox("Significance level (alpha)",[0.01,0.05,0.10],index=1)
    st.caption("Demo data is synthetic. Replace it with a randomized experiment event log.")

data=raw[raw.group.isin(groups)].copy()
if chosen_devices and "device" in data: data=data[data.device.astype(str).isin(chosen_devices)]
if data.empty: st.warning("No events match filters."); st.stop()
if not {"Control","Variant"}.issubset(set(data.group.unique())):
    st.info("Select both Control and Variant groups to calculate the experiment comparison.")

# User-level funnel: each user counts once at each stage.
users=data.groupby(["user_id","group"],as_index=False).agg(
    landing=("event_name",lambda x:int(x.eq("landing_page").any())),
    cart=("event_name",lambda x:int(x.eq("add_to_cart").any())),
    checkout=("event_name",lambda x:int(x.eq("checkout").any())),
    purchase=("event_name",lambda x:int(x.eq("purchase").any())),
    revenue=("revenue","sum"))
users["order_value"]=np.where(users.purchase==1,users.revenue,0)

def funnel_table(g):
    stages=["landing","cart","checkout","purchase"]
    counts=[int(g[s].sum()) for s in stages]
    return pd.DataFrame({"Stage":["Landing Page","Add to Cart","Checkout","Purchase"],"Users":counts,
                         "Step conversion (%)":[100]+[counts[i]/counts[i-1]*100 if counts[i-1] else 0 for i in range(1,4)],
                         "Overall conversion (%)":[v/counts[0]*100 if counts[0] else 0 for v in counts]})
summary=users.groupby("group").agg(users=("user_id","nunique"),purchases=("purchase","sum"),revenue=("revenue","sum"))
summary["conversion_rate"]=summary.purchases/summary.users
summary["revenue_per_user"]=summary.revenue/summary.users
control=users[users.group=="Control"]; variant=users[users.group=="Variant"]
st.subheader("Experiment overview")
a,b,c,d=st.columns(4)
a.metric("Total users",f"{len(users):,}")
a2=float(summary.loc["Control","conversion_rate"]) if "Control" in summary.index else 0
b.metric("Control conversion",f"{a2:.2%}")
v2=float(summary.loc["Variant","conversion_rate"]) if "Variant" in summary.index else 0
c.metric("Variant conversion",f"{v2:.2%}",delta=f"{(v2-a2)*100:.2f} pp" if {"Control","Variant"}.issubset(summary.index) else None)
d.metric("Variant revenue / user",f"${summary.loc['Variant','revenue_per_user']:,.2f}" if "Variant" in summary.index else "—")

if {"Control","Variant"}.issubset(summary.index):
    st.divider(); st.subheader("Statistical significance")
    n1,n2=len(control),len(variant); x1=int(control.purchase.sum()); x2=int(variant.purchase.sum())
    p1=x1/n1 if n1 else 0; p2=x2/n2 if n2 else 0
    pooled=(x1+x2)/(n1+n2) if n1+n2 else 0
    se=sqrt(pooled*(1-pooled)*(1/n1+1/n2)) if n1 and n2 else 0
    z=(p2-p1)/se if se else 0
    p_chi=float(2*stats.norm.sf(abs(z))) if se else 1.0
    se_diff=sqrt(p1*(1-p1)/n1+p2*(1-p2)/n2) if n1 and n2 else 0
    ci_low=(p2-p1)-1.96*se_diff; ci_high=(p2-p1)+1.96*se_diff
    # Chi-square test on 2x2 conversion table
    table=np.array([[x1,n1-x1],[x2,n2-x2]])
    chi2,p_chi2,_,_=stats.chi2_contingency(table,correction=False)
    # Welch t-test for revenue per user (zeros included)
    t_stat,p_t=stats.ttest_ind(control.order_value,variant.order_value,equal_var=False,nan_policy="omit")
    lift=((p2-p1)/p1*100) if p1 else np.nan
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Absolute conversion lift",f"{(p2-p1)*100:+.2f} pp")
    c2.metric("Relative conversion lift",f"{lift:+.1f}%" if np.isfinite(lift) else "N/A")
    c3.metric("Chi-square p-value",f"{p_chi2:.4f}")
    c4.metric("Welch t-test p-value",f"{p_t:.4f}" if np.isfinite(p_t) else "N/A")
    st.write(f"**95% confidence interval for absolute conversion lift:** {ci_low*100:+.2f} to {ci_high*100:+.2f} percentage points.")
    sig=p_chi2<alpha
    positive=ci_low>0
    if sig and positive:
        st.success("Recommendation: Variant shows a statistically significant positive conversion lift. Consider a staged rollout after checking guardrail metrics.")
    elif sig and ci_high<0:
        st.error("Recommendation: Variant significantly reduces conversion. Do not launch without further investigation.")
    else:
        st.warning("Recommendation: Evidence is inconclusive at the selected significance level. Keep the control or collect more data; do not claim a win.")
    st.caption(f"Two-proportion chi-square test (uncorrected): χ²={chi2:.3f}, p={p_chi2:.5f}. Welch t-test compares revenue per randomized user, including zero-revenue users: t={t_stat:.3f}, p={p_t:.5f}.")
else:
    st.info("Select both experiment groups to see p-values, confidence intervals, and a launch recommendation.")

st.divider(); st.subheader("Conversion funnel")
funnel=[]
for group,g in users.groupby("group"):
    tab=funnel_table(g); tab["Group"]=group; funnel.append(tab)
funnel_df=pd.concat(funnel,ignore_index=True)
fig=px.funnel(funnel_df,x="Users",y="Stage",color="Group",color_discrete_map={"Control":"#2563EB","Variant":"#0F766E"})
fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig,use_container_width=True)
st.dataframe(funnel_df[["Group","Stage","Users","Step conversion (%)","Overall conversion (%)"]].style.format({"Step conversion (%)":"{:.1f}%","Overall conversion (%)":"{:.1f}%"}),use_container_width=True,hide_index=True)

st.divider(); st.subheader("Segment and guardrail breakdown")
if "device" in data:
    device_users=data.groupby(["user_id","group","device"],as_index=False).agg(purchase=("event_name",lambda x:int(x.eq("purchase").any())))
    by_device=device_users.groupby(["device","group"],as_index=False).agg(users=("user_id","nunique"),conversions=("purchase","sum"))
    by_device["conversion_rate"]=by_device.conversions/by_device.users
    fig=px.bar(by_device,x="device",y="conversion_rate",color="group",barmode="group",labels={"conversion_rate":"Conversion rate","device":"Device"},color_discrete_map={"Control":"#2563EB","Variant":"#0F766E"})
    st.plotly_chart(fig,use_container_width=True)
st.subheader("Experiment data")
st.dataframe(summary.reset_index().rename(columns={"index":"group"}).style.format({"conversion_rate":"{:.2%}","revenue":"${:,.2f}","revenue_per_user":"${:,.2f}"}),use_container_width=True,hide_index=True)
st.download_button("Download cleaned event data",data=data.to_csv(index=False).encode("utf-8"),file_name="cleaned_ab_test_events.csv",mime="text/csv")
st.caption("Assumptions: user-level random assignment, independent users, one primary conversion per user, fixed-horizon analysis. Check sample-ratio mismatch, novelty effects, multiple testing, guardrail metrics, and experiment duration before making a production decision.")
