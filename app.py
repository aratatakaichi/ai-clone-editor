import streamlit as st
import google.generativeai as genai

# --- ここから：パスワード認証システム ---
def check_password():
    """パスワードが正しければTrueを返す"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 執筆クローンIDE（会員限定）")
        st.write("note記事で発行されたパスワードを入力してください。")
        
        # パスワード入力欄
        pwd = st.text_input("パスワード", type="password")
        
        # 例：「arata2026」が正しいパスワードの場合
        if st.button("ログイン"):
            if pwd == "arata2026": 
                st.session_state["password_correct"] = True
                st.rerun() # 画面をリロードして中身を表示
            else:
                st.error("パスワードが間違っています。")
        return False
    return True

# --- パスワードが正しい場合のみ、以下の本編を表示する ---
if check_password():
    

st.title("✍️ AI執筆統合開発環境")
st.write("認証に成功しました！ようこそ。")


if "clone_prompt" not in st.session_state:
    st.session_state.clone_prompt = ""
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

with st.sidebar:
    api_key = st.text_input("Gemini APIキー", type="password")

tab1, tab2 = st.tabs(["🧠 1. あなたを学習させる", "✍️ 2. クローンに執筆させる"])

with tab1:
    persona = st.text_area("あなたのスタンス（例：現場主義のマーケター）")
    sample1 = st.text_area("過去のサンプル記事 1")
    sample2 = st.text_area("過去のサンプル記事 2")

    if st.button("文体を分析し記憶する"):
        if api_key and persona and sample1:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            meta_prompt = f"以下の属性と文章からAIが文体を模倣するシステムプロンプトを作成せよ。\n属性:{persona}\n文1:{sample1}\n文2:{sample2}"
            with st.spinner("スキャン中..."):
                response = model.generate_content(meta_prompt)
                st.session_state.clone_prompt = response.text
                st.success("記憶完了！タブ2へ移動してください。")

with tab2:
    theme = st.text_area("アプリ①で作った【最終プロット】をここに貼り付けてください")
    
    if st.button("✨ クローンに執筆を開始させる"):
        if api_key and st.session_state.clone_prompt and theme:
            genai.configure(api_key=api_key)
            clone_model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=st.session_state.clone_prompt)
            with st.spinner("猛烈な勢いで執筆中..."):
                response = clone_model.generate_content(theme)
                st.session_state.generated_text = response.text

    if st.session_state.generated_text:
        st.text_area("エディター（自由に手直し可能）", value=st.session_state.generated_text, height=500)