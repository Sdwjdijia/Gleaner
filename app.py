import streamlit as st #網頁模塊
import pandas as pd #資料分析
import jieba #中文詞庫
import time 
from collections import Counter #容器資料型態
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR #YT留言擷取

# =========================================================================
# 1. 網頁自訂背景與樣式 (優化留白、變更深灰色調背景)
# =========================================================================
st.set_page_config(page_title="Gleaner", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #1a1c23;
        color: #ffffff;
    }
    
    /* 標題流體漸層動畫 */
    @keyframes gradient-move {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .cool-title {
        font-size: 50px !important;
        font-weight: 900 !important;
        text-align: center;
        background: linear-gradient(-45deg, #ff007f, #7928ca, #00dfd8);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-move 4s ease infinite;
        padding: 15px;
        margin-bottom: 60px !important;
    }

    .footer {
        text-align: center;
        color: #6b7280;
        font-size: 14px;
        margin-top: 60px;
        border-top: 1px solid #2d3139;
        padding-top: 15px;
    }
    </style>
    
    <h1 class="cool-title">🕵️ Gleaner偵查系統</h1>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# 2. 簡化版 5 秒開場進度條
# =========================================================================
if "loaded" not in st.session_state:
    st.session_state.loaded = False

placeholder = st.empty()

if not st.session_state.loaded:
    with placeholder.container():
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.05)  # 準確的 5 秒
            progress_bar.progress(percent_complete + 1)
        st.session_state.loaded = True
        placeholder.empty()

# =========================================================================
# 3. 主程式+左側控制邊欄與功能區
# =========================================================================
if st.session_state.loaded:
    
    # 左側可以打開控制面板
    st.sidebar.header("⚙️ 偵查參數設定")
    max_comments = st.sidebar.slider(
        "選擇要偵查的留言數量上限", 
        min_value=100, 
        max_value=1000, 
        value=300, 
        step=50
    )
    st.sidebar.markdown("---")
    st.sidebar.info("💡 抓取數量越多，後端解析關鍵字需要的時間就會稍微變長。")

    # 主頁面網址輸入
    raw_video_url = st.text_input("🔗 請輸入要為您偵查的YouTube影片連結:", placeholder="https://www.youtube.com/watch?v=...")
    
    video_url = raw_video_url.strip() if raw_video_url else ""

    if video_url:
        with st.spinner("正在為您查詢和分析中..."):
            try:
                downloader = YoutubeCommentDownloader()
                comments_iter = downloader.get_comments_from_url(video_url, sort_by=SORT_BY_POPULAR)
                
                comments_list = []
                for i, comment in enumerate(comments_iter):
                    if i >= max_comments: 
                        break
                    comments_list.append({
                        "發言者": comment.get('author', '匿名'),
                        "留言內容": comment.get('text', ''),
                        "讚數": int(comment.get('votes', 0)),
                        "時間": comment.get('time', '')
                    })
                
                df = pd.DataFrame(comments_list)
                
                if df.empty:
                    st.warning("該影片沒有留言，或網址有誤。")
                else:
                    st.success(f"✅ 成功攻破並分析前排 {len(df)} 條熱門留言！")
                    
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.subheader("🏆 1. 最高讚數留言 Top 5")
                        top_5_df = df.sort_values(by="讚數", ascending=False).head(5)
                        st.dataframe(top_5_df[["發言者", "讚數", "留言內容"]], use_container_width=True, hide_index=True)
                    
                    with col_right:
                        st.subheader("🔍 2. 熱門關鍵字統計 (前 10 名)")
                        all_text = " ".join(df["留言內容"].astype(str).tolist())
                        
                try:
                    with open("stopwords.txt", "r", encoding="utf-8") as f:
                        stopwords = {line.strip() for line in f if line.strip()}
                except FileNotFoundError:
                        # 防呆機制：萬一檔案不小心不見了，預設一個空的集合，避免整個網頁掛掉
                        stopwords = set()                        
                        # 在斷詞時，順便把在過濾清單裡的字以及單個字排除掉
                        words = [
                            w for w in jieba.cut(all_text) 
                            if len(w) > 1 and not w.isspace() and w not in stopwords
                        ]
                        
                        word_counts = Counter(words).most_common(10)
                        
                        if word_counts:
                            df_words = pd.DataFrame(word_counts, columns=["關鍵字", "出現次數"])
                            st.bar_chart(df_words.set_index("關鍵字"), color="#7928ca")
                        else:
                            st.write("無法提取足夠的關鍵字。")

            except Exception as e:
                st.error(f"發生錯誤: {e}")

    # =========================================================================
    # 4. 最底部的專屬製作者標籤 Salmon
    # =========================================================================
    st.markdown(
        """
        <div class="footer">
            🚀 系統運行中 | 製作者：Salmon
        </div>
        """,
        unsafe_allow_html=True
    )
