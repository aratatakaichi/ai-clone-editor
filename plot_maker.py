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

st.title("🧠 深掘りプロット生成エージェント")
st.write("認証に成功しました！ようこそ。")


with st.sidebar:
    api_key = st.text_input("Gemini APIキー", type="password")

theme = st.text_input("テーマ（例：リモートワークにおける雑談の重要性）")
keywords = st.text_input("キーワード")
summary = st.text_area("内容概略")

if st.button("🔥 7段階の脳内会議を開始し、プロットを生成する"):
    if api_key and theme:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        agent_prompt = f"""
        あなたは敏腕編集者です。以下の企画の種を元に、7つのステップで深く鋭いプロットを作成してください。
        【種】テーマ: {theme} / キーワード: {keywords} / 概略: {summary}
        【7ステップ】1.リサーチ 2.考察 3.仮構成 4.再考察(ダメ出し) 5.再リサーチ 6.再々考察 7.最終プロット作成
        ステップ1〜6は思考プロセスを出力し、ステップ7は明確に区切って構成指示書を出力すること。
        """
        
        with st.spinner("AIが脳内会議中..."):
            response = model.generate_content(agent_prompt)
            st.success("プロット生成完了！")
            st.markdown(response.text)
    else:
        st.error("APIキーとテーマを入力してください。")