import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Macro Investment Dashboard", layout="wide")

st.title("📈 Global Macro & Market Dashboard (5Y)")
st.markdown(f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.markdown("---")

# 2. 사이드바: 상세 매크로 해석 가이드 (요청사항 반영)
with st.sidebar:
    st.header("📚 지표 상세 해설")
    
    with st.expander("1️⃣ 인플레이션 & 고용 (방향성)"):
        st.markdown("""
        **1. CPI (소비자물가지수)**
        - **정의**: 소비자가 구입하는 상품/서비스의 가격 변동.
        - **High**: 인플레이션 심화 → 금리 인상 압력 (주가 악재)
        - **Low**: 디플레이션 우려 or 물가 안정 (주가 호재)
        
        **2. Core CPI (근원 소비자물가지수)**
        - **정의**: 변동성이 큰 식품/에너지를 제외한 물가. 추세 판단에 더 중요.
        - **해석**: CPI가 내려도 Core가 안 내리면 연준은 금리를 못 내림.
        
        **3. Initial Claims (신규 실업수당 청구건수)**
        - **정의**: 지난주에 해고당해서 실업수당을 처음 신청한 사람 수.
        - **High**: 고용 시장 침체 → 경기 둔화 (침체 공포)
        - **Low**: 고용 시장 탄탄함 → 금리 인하 명분 약화
        
        **4. Unemployment Rate (실업률)**
        - **정의**: 일할 의사가 있는데 일자리를 못 구한 비율.
        - **해석**: 급격히 오르면 경기 침체(Recession) 확정 신호. (가장 중요한 후행지표)
        """)
        
    with st.expander("2️⃣ 금리 & 환율 (자금 흐름)"):
        st.markdown("""
        **1. 10Y-2Y Spread (장단기 금리차)**
        - **정의**: 10년물 금리에서 2년물 금리를 뺀 값.
        - **음수(역전)**: 경기 침체 전조 현상 (단기 금리가 더 높음).
        - **양수 전환**: 침체가 실제로 닥치거나, 경기가 회복될 때 정상화됨.
        
        **2. DXY (달러 인덱스)**
        - **정의**: 주요 6개국 통화 대비 달러의 가치.
        - **High (>104)**: 달러 강세. 신흥국/한국 자금 이탈 (국장 악재).
        - **Low (<100)**: 달러 약세. 위험자산 선호 심리 (국장 호재).
        
        **3. Real Yield (실질 금리)**
        - **정의**: 명목 금리(10년물) - 기대 인플레이션. (TIPS 금리)
        - **해석**: '진짜 돈의 비용'. 실질 금리가 오르면 기술주/성장주 밸류에이션이 급격히 하락함.
        """)

    with st.expander("3️⃣ 유동성 & 경기 (체력)"):
        st.markdown("""
        **1. Fed Balance Sheet (연준 대차대조표)**
        - **정의**: 연준이 가지고 있는 자산 총액.
        - **증가**: 양적 완화(Money Printing) → 증시 폭등 요인.
        - **감소(QT)**: 양적 긴축(돈 회수) → 증시 하방 압력.
        
        **2. Retail Sales (소매 판매)**
        - **정의**: 백화점, 마트 등에서의 매출액 변화 (미국 GDP의 70%는 소비).
        - **High**: 경기가 너무 뜨거움 → 인플레 재점화 우려.
        - **Low**: 소비 위축 → 경기 침체 우려. (적당한 2~3% 성장이 베스트)
        """)

    with st.expander("4️⃣ 스트레스 (위기 신호)"):
        st.markdown("""
        **1. VIX (변동성 지수)**
        - **정의**: S&P500 옵션에 반영된 향후 30일간의 변동성 기대치.
        - **High (>30)**: 공포 구간. 투매가 나옴 (역발상 매수 기회).
        - **Low (<20)**: 시장이 평온함 (탐욕 구간).
        
        **2. High Yield Spread (하이일드 스프레드)**
        - **정의**: 신용등급 낮은 회사채 금리 - 국채 금리 차이.
        - **해석**: 이 수치가 치솟으면 기업들이 돈을 못 빌려 부도 위기라는 뜻. (경제 위기의 가장 정확한 신호)
        """)
    
    st.info("데이터: Yahoo Finance & FRED (최근 5년)")

# 3. 데이터 가져오기 함수 (5년으로 확장)
@st.cache_data(ttl=3600*12) 
def get_macro_data():
    end = datetime.datetime.now()
    # [수정됨] 최근 5년 데이터 (days=365*5)
    start = end - datetime.timedelta(days=365*5) 
    
    data = {}
    
    # A. Yahoo Finance 데이터
    yahoo_tickers = {
        'US 10Y Yield': '^TNX',
        'US 2Y Yield': '^IRX',
        'DXY': 'DX-Y.NYB',
        'KRW/USD': 'KRW=X',
        'VIX': '^VIX',
        'S&P 500': '^GSPC'
    }
    
    for name, ticker in yahoo_tickers.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                     df = df['Close']
                else:
                     df = df['Close']
                data[name] = df
        except:
            pass

    # B. FRED 데이터 (Direct CSV 방식)
    fred_tickers = {
        'CPI (YoY)': 'CPIAUCSL',
        'Core CPI (YoY)': 'CPILFESL',
        'Unemployment Rate': 'UNRATE',
        'Initial Claims': 'ICSA',
        '10Y-2Y Spread': 'T10Y2Y',
        'Real Yield (10Y)': 'DFII10',
        'Fed Balance Sheet': 'WALCL',
        'High Yield Spread': 'BAMLH0A0HYM2',
        'Retail Sales': 'RSAFS' 
    }
    
    for name, code in fred_tickers.items():
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
            df = pd.read_csv(url, index_col=0, parse_dates=True)
            df = df.loc[start:] # 5년치로 자르기
            
            # YoY 계산 (CPI, 소매판매)
            if name in ['CPI (YoY)', 'Core CPI (YoY)', 'Retail Sales']:
                df = df.pct_change(periods=12) * 100
            
            data[name] = df
        except:
            pass
            
    return data

with st.spinner('최근 5년치 데이터를 수집 중입니다...'):
    macro_data = get_macro_data()

# 4. 화면 표시 함수
def display_metric_and_chart(name, format_str="{:.2f}"):
    if name in macro_data and not macro_data[name].empty:
        series = macro_data[name]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
            
        current_val = series.iloc[-1]
        
        if len(series) >= 2:
            prev_val = series.iloc[-2]
            delta = current_val - prev_val
        else:
            delta = 0
        
        st.metric(label=name, value=format_str.format(current_val), delta=format_str.format(delta))
        st.line_chart(series, height=200) # 5년치 그래프가 그려짐
    else:
        st.warning(f"{name} 데이터 로드 실패")

# 5. 메인 대시보드 레이아웃 (탭 구성)
tab1, tab2, tab3, tab4 = st.tabs(["🔥 인플레/고용", "💰 금리/환율", "🏦 유동성/경기", "🚨 스트레스"])

with tab1:
    st.subheader("인플레이션 & 고용 지표 (5 Year)")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('CPI (YoY)', "{:.2f}%")
        display_metric_and_chart('Core CPI (YoY)', "{:.2f}%")
    with col2:
        display_metric_and_chart('Unemployment Rate', "{:.1f}%")
        display_metric_and_chart('Initial Claims', "{:.0f}")

with tab2:
    st.subheader("금리 & 환율 지표 (5 Year)")
    col1, col2 = st.columns(2)
    with col1:
        # 장단기 금리차 계산 로직 추가
        if 'US 10Y Yield' in macro_data and 'US 2Y Yield' in macro_data:
             # Yahoo 데이터 기반 실시간 스프레드 계산 (보조)
             t10 = macro_data['US 10Y Yield'].iloc[-1].item()
             if t10 > 10: t10 /= 10
             t2 = macro_data['US 2Y Yield'].iloc[-1].item()
             if t2 > 10: t2 /= 10
             
             st.metric("US 10Y Treasury", f"{t10:.2f}%")
             
        display_metric_and_chart('10Y-2Y Spread', "{:.2f}")
        display_metric_and_chart('Real Yield (10Y)', "{:.2f}%")

    with col2:
        display_metric_and_chart('DXY', "{:.2f}")
        display_metric_and_chart('KRW/USD', "{:.2f} 원")

with tab3:
    st.subheader("유동성 & 경기 지표 (5 Year)")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('Fed Balance Sheet', "{:.0f}")
    with col2:
        display_metric_and_chart('Retail Sales', "{:.2f}% (YoY)")

with tab4:
    st.subheader("스트레스 & 리스크 지표 (5 Year)")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('VIX', "{:.2f}")
    with col2:
        display_metric_and_chart('High Yield Spread', "{:.2f}%")

if st.button("데이터 최신화"):
    st.cache_data.clear()
    st.rerun()
