import pandas as pd
import yfinance as yf


# [수정됨] 데이터 수집 함수 개선
def get_yahoo_data(tickers, get_type="Adj Close"):
	# 1. start 옵션을 주어 충분한 기간의 데이터를 요청합니다.
	# 2. auto_adjust=False로 설정하여 Adj Close를 확보합니다.
	df = yf.download(tickers, start="2010-01-01", auto_adjust=False)
	
	df = df[get_type]
	
	# 3. [중요] dropna() 전에 ffill()을 먼저 수행합니다.
	# 중간에 이빨이 빠진 데이터(NaN)가 있으면 전날 가격을 가져와서 채웁니다.
	# 이렇게 해야 멀쩡한 날짜가 통째로 삭제되는 것을 막을 수 있습니다.
	df.ffill(inplace=True)
	
	# 4. 그래도 비어있는 데이터(상장 이전 데이터 등)는 삭제합니다.
	df.dropna(inplace=True)
	
	return df


# 리밸런싱 하는 날의 데이터만 뽑기(월말 데이터만 추출)
def get_rebal_date(df, rebal="month"):
	res_df = pd.DataFrame()
	df["year"] = df.index.year
	df["month"] = df.index.month
	df["day"] = df.index.day
	days_df = df.groupby(["year", "month"])["day"].max()
	for i in range(len(days_df)):
		if days_df.iloc[i] >= 25:
			day = "{}-{}-{}".format(days_df.index[i][0], days_df.index[i][1], days_df.iloc[i])
			# loc을 사용하여 경고 메시지 방지 및 명확한 인덱싱
			res_df = pd.concat([res_df, df.loc[df.index == day]])
	return res_df


agg_tickers = ["SPY", "IWM", "VEA", "VWO", "TLT", "IEF", "PDBC", "VNQ"]
safe_tickers = ["IEF", "BIL"]

all_tickers = list(set(agg_tickers + safe_tickers + ["TIP"]))

print("데이터 다운로드 중...")
data = get_yahoo_data(all_tickers)
month_data = get_rebal_date(data)

# [디버깅] 데이터 개수 확인
print(f"다운로드 된 원본 데이터 개수: {data.shape[0]}일")
print(f"월말 리밸런싱 데이터 개수: {month_data.shape[0]}개월")

# 데이터 검증 로직
if month_data.shape[0] < 13:
	print("오류: 데이터가 여전히 부족합니다. 특정 종목의 상장일이 너무 최근일 수 있습니다.")
	# 어떤 종목이 데이터를 깎아먹는지 확인하기 위해 가장 짧은 데이터를 가진 컬럼 출력
	print("각 종목별 데이터 시작일 확인:")
	print(data.apply(lambda x: x.first_valid_index()))
else:
	safe_num = 0
	agg_num = 0
	buy_history = []
	
	# logic
	# TLT 1-3-6-12 모멘텀 점수 구하기
	# 데이터가 충분하므로 루프 실행
	for i in range(12, month_data.shape[0]):
		# iloc 접근 시 에러 방지를 위해 변수 할당
		tip_prices = month_data["TIP"]
		
		m1 = (tip_prices.iloc[i] - tip_prices.iloc[i - 1]) / tip_prices.iloc[i - 1]
		m3 = (tip_prices.iloc[i] - tip_prices.iloc[i - 3]) / tip_prices.iloc[i - 3]
		m6 = (tip_prices.iloc[i] - tip_prices.iloc[i - 6]) / tip_prices.iloc[i - 6]
		m12 = (tip_prices.iloc[i] - tip_prices.iloc[i - 12]) / tip_prices.iloc[i - 12]
		score = m1 + m3 + m6 + m12
		
		if score > 0:
			agg_num += 1
			asset_type = agg_tickers
			
			# 해당 자산군 데이터 추출
			asset_prices = month_data[asset_type]
			
			m1 = (asset_prices.iloc[i] - asset_prices.iloc[i - 1]) / asset_prices.iloc[i - 1]
			m3 = (asset_prices.iloc[i] - asset_prices.iloc[i - 3]) / asset_prices.iloc[i - 3]
			m6 = (asset_prices.iloc[i] - asset_prices.iloc[i - 6]) / asset_prices.iloc[i - 6]
			m12 = (asset_prices.iloc[i] - asset_prices.iloc[i - 12]) / asset_prices.iloc[
				i - 12]
			
			score_assets = m1 + m3 + m6 + m12
			top4 = score_assets.nlargest(4)
			
			buy = []
			for name, value in zip(top4.index, top4.values):
				if value <= 0:
					buy.append("BIL")
				else:
					buy.append(name)
		
		else:
			safe_num += 1
			asset_type = safe_tickers
			asset_prices = month_data[asset_type]
			
			m1 = (asset_prices.iloc[i] - asset_prices.iloc[i - 1]) / asset_prices.iloc[i - 1]
			m3 = (asset_prices.iloc[i] - asset_prices.iloc[i - 3]) / asset_prices.iloc[i - 3]
			m6 = (asset_prices.iloc[i] - asset_prices.iloc[i - 6]) / asset_prices.iloc[i - 6]
			m12 = (asset_prices.iloc[i] - asset_prices.iloc[i - 12]) / asset_prices.iloc[
				i - 12]
			
			score_assets = m1 + m3 + m6 + m12
			buy = list(score_assets.nlargest(1).index)
		
		buy_history.append(buy)
	
	df_buy = pd.DataFrame(buy_history)
	
	total_trades = agg_num + safe_num
	if total_trades > 0:
		df_buy["Date"] = month_data.index[12:]
		df_buy.set_index("Date", drop=True, inplace=True)
		df_buy.fillna("", inplace=True)
		
		print("-" * 30)
		print("백테스트 결과")
		print("-" * 30)
		print(f"총 거래 횟수: {total_trades}개월")
		print("상승장 : 하락장 비율  = {:.1f}% : {:.1f}%".format(agg_num / total_trades * 100,
														 safe_num / total_trades * 100))
		# print(df_buy.tail())  # 최근 매수 신호 확인
		# 1. 콘솔에 전체 다 출력하기 (비추천, 너무 길어서 잘림)
		# pd.set_option('display.max_rows', None) # 줄 생략 없이 설정
		# print(df_buy)
		
		# 2. 엑셀이나 CSV 파일로 저장하기 (강력 추천)
		df_buy.to_csv("backtest_result.csv")  # 같은 폴더에 파일이 생성됩니다.
		print("backtest_result.csv 파일로 전체 내역을 저장했습니다.")
	else:
		print("결과: 매매 신호가 발생하지 않았습니다.")