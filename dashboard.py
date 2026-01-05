import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="나만의 매크로 대시보드", layout="wide")

st.title("📊 Global Macro & Market Dashboard")
st.markdown(f"기준 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.divider()

# 2. 데이터 가져오기 함수 (캐싱을 통해 속도 향상)
@st.cache_data(ttl=600)  # 10분마다 갱신
def get_market_data():
    # 티커 리스트 정의
    tickers = {
        'US 10Y Yield': '^TNX',       # 미국 10년물 국채금리
        'Dollar Index': 'DX-Y.NYB',   # 달러 인덱스
        'WTI Oil': 'CL=F',            # 서부 텍사스유
        'VIX (Fear)': '^VIX',         # 공포지수
        'KRW/USD': 'KRW=X',           # 원달러 환율
        'Semi Index': '^SOX',         # 필라델피아 반도체
    }
    
    data = {}
    for name, ticker in tickers.items():
        # 최근 2일치 데이터 가져오기 (전일 대비 등락 확인용)
        df = yf.download(ticker, period="5d", progress=False)
        if len(df) >= 2:
            current = df['Close'].iloc[-1].item()
            prev = df['Close'].iloc[-2].item()
            change = current - prev
            change_pct = (change / prev) * 100
            
            # 10년물 금리는 데이터가 40.0 등으로 와서 /10 보정 필요할 수 있음 (Yahoo Finance 특성)
            # 최근 Yahoo Finance ^TNX는 %단위 그대로 오는 경우가 많아 확인 필요하지만, 통상 4.0%면 4.0으로 표기됨.
            
            data[name] = {
                'current': current,
                'change': change,
                'change_pct': change_pct
            }
    return data

# 데이터 로딩 표시
with st.spinner('시장 데이터를 불러오는 중입니다...'):
    macro_data = get_market_data()

# 3. 화면 구성 (레이아웃)

# 섹션 1: 시장의 '중력' (금리, 달러, 유가)
st.subheader("1. Key Drivers (시장의 중력)")
col1, col2, col3 = st.columns(3)

with col1:
    d = macro_data.get('US 10Y Yield')
    if d:
        st.metric(
            label="🇺🇸 미국 10년물 금리",
            value=f"{d['current']:.2f}%",
            delta=f"{d['change']:.2f}%p",
            delta_color="inverse" # 금리 상승은 주식에 악재이므로 반대 색상(빨강) 표시
        )

with col2:
    d = macro_data.get('Dollar Index')
    if d:
        st.metric(
            label="💵 달러 인덱스",
            value=f"{d['current']:.2f}",
            delta=f"{d['change']:.2f}",
            delta_color="inverse"
        )

with col3:
    d = macro_data.get('WTI Oil')
    if d:
        st.metric(
            label="🛢️ WTI 유가",
            value=f"${d['current']:.2f}",
            delta=f"{d['change_pct']:.2f}%",
            delta_color="inverse"
        )

st.divider()

# 섹션 2: 한국 시장 민감 지표
st.subheader("2. Korea Market Sensitivity (한국 영향)")
col4, col5, col6 = st.columns(3)

with col4:
    d = macro_data.get('KRW/USD')
    if d:
        st.metric(
            label="🇰🇷 원/달러 환율",
            value=f"{d['current']:.2f} 원",
            delta=f"{d['change']:.2f} 원",
            delta_color="inverse" # 환율 상승은 외국인 이탈 우려
        )

with col5:
    d = macro_data.get('Semi Index')
    if d:
        st.metric(
            label="💾 필라델피아 반도체",
            value=f"{d['current']:.0f}",
            delta=f"{d['change_pct']:.2f}%",
            delta_color="normal" # 상승이 좋음
        )

with col6:
    d = macro_data.get('VIX (Fear)')
    if d:
        state = "안정" if d['current'] < 20 else "공포" if d['current'] > 30 else "경계"
        st.metric(
            label=f"😨 VIX 공포지수 ({state})",
            value=f"{d['current']:.2f}",
            delta=f"{d['change']:.2f}",
            delta_color="inverse"
        )

# 4. 새로고침 버튼
if st.button('데이터 새로고침'):
    st.cache_data.clear()
    st.rerun()

# 5. 참고사항 (사이드바)
with st.sidebar:
    st.header("💡 투자 포인트")
    st.markdown("""
    - **10년물 금리**: 4.0% 넘어가면 기술주 주의
    - **환율**: 1,350원 넘으면 외국인 매도 가능성
    - **VIX**: 20 이하면 평온, 급등하면 조정장
    """)
    st.info("데이터 출처: Yahoo Finance")