# app.py
# 터미널에 cd ./data 경로지정 후 streamlit run app.py
# 참고 링크
# https://codemagician.tistory.com/entry/Streamlit-05-Streamlit-%EC%95%B1-%EB%B0%B0%ED%8F%AC%ED%95%98%EA%B8%B0#google_vignette

import streamlit as st
import pandas as pd
df = pd.DataFrame({
  'first column': [1, 2, 3, 4],
  'second column': [10, 20, 30, 40]
})
df2 = "Hello World"
st.write(df2)
st.write(df)

# 생성된 링크
# https://share.streamlit.io/ # 배포하는 사이트(github 연동해놓음)
# https://appdemo-w3bqqpronqrhifshxtcfad.streamlit.app/