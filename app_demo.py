
import streamlit as st
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime

from stock_finlab import stock

st.set_page_config(page_title="Stock chart (FinLab demo)", layout="wide")

st.sidebar.header('Parameter setting')
stock_code = st.sidebar.text_input('Stock code (e.g., 2330, 2317)')
month = st.sidebar.number_input('From month...', value=max(1, datetime.now().month - 3),
                                step=1, max_value=12, min_value=1)

@st.cache_data(show_spinner=False, ttl=3600)
def get_stock_data(stock_code: str, month: int):
    return stock(stock_code, month).get_all_data()

st.title('Stock chart (FinLab demo)')
st.caption('Only fields available from FinLab will be shown.')

if stock_code and month:
    data = get_stock_data(stock_code, int(month))
    if data is None or data.empty:
        st.warning("No data returned. Try another stock code or month range.")
        st.stop()

    # Derive available metrics based on columns actually present
    candidates = ["成交量", "外資", "投信", "自營商"]
    available = [c for c in candidates if c in data.columns]

    # Fallback to volume only if none of the three-majors exist
    if "成交量" not in available:
        available.insert(0, "成交量")

    # Build selectors AFTER we know available columns
    Bubble_info = st.sidebar.selectbox('Bubble_info', options=available, index=0, key="bubble_info")
    Bubble_size = st.sidebar.number_input('Bubble_size', step=1, value=10)
    sub_info = st.sidebar.selectbox('Sub_info', options=available, index=min(1, len(available)-1), key="sub_info")

    st.dataframe(data, use_container_width=True)
    st.success('Load data success!')

    # Trace 1: price line + size/color by chosen metric
    if Bubble_info != "成交量":
        marker_kwargs = dict(
            size=data[Bubble_info].abs(),
            sizeref=max(1e-9, data[Bubble_info].abs().mean()) / Bubble_size,
        )
        color_col = f"{Bubble_info}買賣顏色"
        if color_col in data.columns:
            marker_kwargs["color"] = data[color_col]

        trace1 = go.Scatter(
            x=data["日期"],
            y=data["收盤價"],
            mode="lines+markers",
            marker=marker_kwargs,
            line=dict(dash="dot"),
            hovertemplate="<b>日期 %{x}</b><br>收盤價 %{y}<br>" + f"{Bubble_info}: %{marker.size}<br>",
            name="收盤價",
        )
    else:
        trace1 = go.Scatter(
            x=data["日期"],
            y=data["收盤價"],
            mode="lines+markers",
            marker=dict(
                size=data["成交量"].abs(),
                sizeref=max(1e-9, data["成交量"].abs().mean()) / Bubble_size,
            ),
            line=dict(dash="dot"),
            hovertemplate="<b>日期 %{x}</b><br>收盤價 %{y}",
            name="收盤價",
        )

    # Trace 2: sub bar with safe color
    sub_color_col = f"{sub_info}買賣顏色"
    bar_kwargs = dict(x=data["日期"], y=data[sub_info], name=sub_info)
    if sub_color_col in data.columns:
        bar_kwargs["marker_color"] = data[sub_color_col]

    trace2 = go.Bar(**bar_kwargs)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(trace1, row=1, col=1)
    fig.add_trace(trace2, row=2, col=1)
    fig.update_layout(title=f"{stock_code}_chart", template="plotly_dark", height=700)

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("請先輸入股票代碼與起始月份。")
