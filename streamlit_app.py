# streamlit_app.py
import streamlit as st
import pandas as pd
import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import re
import base64
from io import BytesIO
import tempfile
import os

# 页面配置
st.set_page_config(
    page_title="拼多多标题关键词分析",
    page_icon="📊",
    layout="wide"
)

# 设置中文分词
jieba.setLogLevel('WARN')

# 自定义样式
st.markdown("""
<style>
    .st-emotion-cache-1y4p8pa {
        padding: 2rem 1rem;
    }
    .title {
        color: #165DFF;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-area {
        border: 2px dashed #165DFF;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .wordcloud-container {
        display: flex;
        justify-content: center;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 获取停用词
def get_stopwords():
    try:
        with open("stopwords.txt", "r", encoding="utf-8") as f:
            return set([line.strip() for line in f])
    except FileNotFoundError:
        return {"的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一", "一个", "上", "也", "很",
                "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

# 预处理文本
def preprocess_text(titles, stopwords):
    all_words = []
    for title in titles:
        if not isinstance(title, str):
            title = str(title)
        title = re.sub(r'[^\u4e00-\u9fa5]', ' ', title)
        words = jieba.cut(title)
        filtered_words = [word for word in words if len(word) > 1 and word.strip() and word not in stopwords]
        all_words.extend(filtered_words)
    return all_words

# 分析关键词
def analyze_keywords(words, top_n=100):
    word_counts = Counter(words)
    top_words = word_counts.most_common(top_n)
    return top_words, dict(word_counts)

# 生成词云
def generate_wordcloud(word_dict):
    wc = WordCloud(
        font_path="SimHei.ttf",  # 使用内置字体或上传字体文件
        width=800,
        height=600,
        background_color="white",
        max_words=200,
        contour_width=3,
        contour_color='steelblue'
    )
    wc.generate_from_frequencies(word_dict)
    return wc

# 主应用
def main():
    st.markdown("<h1 class='title'>拼多多标题关键词分析</h1>", unsafe_allow_html=True)
    
    # 文件上传区域
    with st.container():
        st.markdown("### 上传商品标题数据")
        st.markdown("""
        <div class='upload-area'>
            <p>上传包含拼多多商品标题的Excel文件，系统将自动分析标题中的高频关键词并生成词云图</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "选择Excel文件 (.xlsx, .xls)", 
            type=["xlsx", "xls"],
            label_visibility="collapsed"
        )
    
    if uploaded_file is not None:
        try:
            # 读取Excel文件
            df = pd.read_excel(uploaded_file)
            
            # 查找标题列
            possible_columns = ['标题', '商品标题', 'product_title', 'title']
            title_column = None
            
            for col in possible_columns:
                if col in df.columns:
                    title_column = col
                    break
                    
            if title_column is None:
                st.error("未找到标题列，请确保Excel包含以下列名之一: " + ", ".join(possible_columns))
                return
            
            titles = df[title_column].tolist()
            
            if not titles:
                st.error("Excel文件中没有找到有效的标题数据")
                return
            
            # 显示进度
            with st.spinner("正在分析数据..."):
                # 预处理和分析
                stopwords = get_stopwords()
                words = preprocess_text(titles, stopwords)
                top_words, word_dict = analyze_keywords(words)
                
                # 显示结果
                st.success("分析完成！")
                
                # 创建两列布局
                col1, col2 = st.columns([1, 2])
                
                # 左侧显示高频词
                with col1:
                    st.markdown("### 高频关键词 (Top 20)")
                    for i, (word, count) in enumerate(top_words[:20], 1):
                        st.markdown(f"{i}. **{word}**: {count}次")
                
                # 右侧显示词云
                with col2:
                    st.markdown("### 关键词词云图")
                    wordcloud = generate_wordcloud(word_dict)
                    
                    # 显示词云
                    fig, ax = plt.subplots(figsize=(10, 8))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    
                    # 添加下载按钮
                    buf = BytesIO()
                    plt.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)
                    st.download_button(
                        label="下载词云图",
                        data=buf,
                        file_name="pdd_wordcloud.png",
                        mime="image/png"
                    )
        
        except Exception as e:
            st.error(f"分析过程中出错: {str(e)}")

if __name__ == "__main__":
    main()