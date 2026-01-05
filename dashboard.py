import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Macro Investment Dashboard", layout="wide")

st.title("📈 Global Macro & Market Dashboard")
st.markdown("---")

# 2. 사이드바: 매크로 해석 가이드
with st.sidebar:
    st.header("📚 매크로 체크 포인트")
    
    with st.expander("1️⃣ 인플레이션 (가장 중요)"):
        st.markdown("""
        - **CPI/PCE**: 금리 방향 결정 1번 변수
        - **체크**: 전월 대비 상승/둔화 여부, Core 하락세 확인
        """)
        
    with st.expander("2️⃣ 고용 사이클 (침체 신호)"):
        st.markdown("""
        - **실업률/실업수당**: 경기 침체 시작점
        - **체크**: 실업률 방향성, 실업수당 지속 증가 여부
        """)
        
    with st.expander("3️⃣ 금리 & 실질금리 (중력)"):
        st.markdown("""
        - **10Y/2Y**: 자산 가격의 중력
        - **체크**: 실질금리 하락(호재), 장단기 스프레드 정상화
        """)

    with st.expander("4️⃣ 유동성 (버티는 힘)"):
        st.markdown("""
        - **Fed Balance Sheet**: 유동성 공급/흡수
        - **체크**: QT 강도, 유동성 환경 변화
        """)

    with st.expander("5️⃣ 환율 (자금 흐름)"):
        st.markdown("""
        - **DXY/원달러**: 글로벌 자금 이동
        - **체크**: 달러 강세(리스크 압박), 원화 약세(국장 불리)
        """)

    with st.expander("6️⃣ 경기 체감 (실물)"):
        st.markdown("""
        - **PMI/소매판매**: 실물 체력
        - **체크**: 50 상회/하회, 제조업 회복 신호
        """)

    with st.expander("7️⃣ 스트레스 신호 (경보등)"):
        st.markdown("""
        - **VIX/High Yield**: 위기 감지기
        - **체크**: HY 스프레드 확대 = 위험 진입
        """)
    
    st.info("데이터 출처: Yahoo Finance & FRED(St. Louis Fed)")

# 3. 데이터 가져오기 함수 (Direct CSV 방식 - 에러 해결)
@st.cache_data(ttl=3600*12) # 12시간마다 갱신
def get_macro_data():
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365*2) # 최근 2년
    
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
                # Yahoo 데이터 구조 처리
                if isinstance(df.columns, pd.MultiIndex):
                     df = df['Close']
                else:
                     df = df['Close']
                data[name] = df
        except:
            pass

    # B. FRED 데이터 (Direct CSV Download 방식)
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
            # 라이브러리 없이 FRED 웹사이트에서 직접 CSV 다운로드 (호환성 문제 해결)
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
            df = pd.read_csv(url, index_col=0, parse_dates=True)
            
            # 날짜 필터링
            df = df.loc[start:]
            
            # YoY 계산
            if name in ['CPI (YoY)', 'Core CPI (YoY)', 'Retail Sales']:
                df = df.pct_change(periods=12) * 100
            
            data[name] = df
        except:
            pass
            
    return data

# 데이터 로딩
with st.spinner('FRED 및 Yahoo Finance에서 데이터를 수집 중입니다...'):
    macro_data = get_macro_data()

# 4. 화면 표시 함수
def display_metric_and_chart(name, format_str="{:.2f}"):
    if name in macro_data and not macro_data[name].empty:
        series = macro_data[name]
        # Series 변환
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
            
        # 최신 값 추출
        current_val = series.iloc[-1]
        
        # 전일/전월 대비 변화량
        if len(series) >= 2:
            prev_val = series.iloc[-2]
            delta = current_val - prev_val
        else:
            delta = 0
        
        st.metric(label=name, value=format_str.format(current_val), delta=format_str.format(delta))
        st.line_chart(series, height=200)
    else:
        st.warning(f"{name} 데이터 로드 실패")

# 5. 메인 대시보드 레이아웃
tab1, tab2, tab3, tab4 = st.tabs(["🔥 인플레/고용", "💰 금리/환율", "🏦 유동성/경기", "🚨 스트레스"])

with tab1:
    st.subheader("1️⃣ 인플레이션 & 2️⃣ 고용")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('CPI (YoY)', "{:.2f}%")
        display_metric_and_chart('Core CPI (YoY)', "{:.2f}%")
    with col2:
        display_metric_and_chart('Unemployment Rate', "{:.1f}%")
        display_metric_and_chart('Initial Claims', "{:.0f}")

with tab2:
    st.subheader("3️⃣ 금리 & 5️⃣ 환율")
    col1, col2 = st.columns(2)
    with col1:
        if 'US 10Y Yield' in macro_data:
            s = macro_data['US 10Y Yield']
            val = s.iloc[-1].item()
            # Yahoo 데이터 40.0 -> 4.0% 보정
            if val > 10: val = val / 10
            
            # 전일 대비
            prev = s.iloc[-2].item()
            if prev > 10: prev = prev / 10
            delta = val - prev
            
            st.metric("US 10Y Yield", f"{val:.2f}%", f"{delta:.2f}%p")
            st.line_chart(s)
            
        display_metric_and_chart('10Y-2Y Spread', "{:.2f}")
        display_metric_and_chart('Real Yield (10Y)', "{:.2f}%")

    with col2:
        display_metric_and_chart('DXY', "{:.2f}")
        display_metric_and_chart('KRW/USD', "{:.2f} 원")

with tab3:
    st.subheader("4️⃣ 유동성 & 6️⃣ 경기")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('Fed Balance Sheet', "{:.0f}")
    with col2:
        display_metric_and_chart('Retail Sales', "{:.2f}% (YoY)")

with tab4:
    st.subheader("7️⃣ 스트레스 신호 (리스크 관리)")
    col1, col2 = st.columns(2)
    with col1:
        display_metric_and_chart('VIX', "{:.2f}")
    with col2:
        display_metric_and_chart('High Yield Spread', "{:.2f}%")

# 새로고침
if st.button("데이터 최신화"):
    st.cache_data.clear()
    st.rerun()
