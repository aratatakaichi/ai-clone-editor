import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="執筆クローンIDE", layout="wide")

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
        
        if st.button("ログイン"):
            if pwd == "arata2026":  # ←ここのパスワードは好きなものに変更可能です
                st.session_state["password_correct"] = True
                st.rerun() # 画面をリロード
            else:
                st.error("パスワードが間違っています。")
        return False
    return True

# --- パスワードが正しい場合のみ、以下の本編を表示する ---
if check_password():
    # ！！！ここから下はすべて、行の先頭にスペースが4つ入っています（インデント）！！！
    
    st.title("✍️ 執筆クローン統合開発環境")
    st.write("認証に成功しました！ようこそ。")

    if "clone_prompt" not in st.session_state:
        st.session_state.clone_prompt = ""
    if "generated_text" not in st.session_state:
        st.session_state.generated_text = ""

    with st.sidebar:
        st.header("⚙️ 初期設定")
        api_key = st.text_input("Gemini APIキーを入力", type="password")
        st.write("※APIキーは保存されません。")

    tab1, tab2 = st.tabs(["🧠 1. クローンに学習させる", "✍️ 2. クローンに執筆させる（エディター）"])

    with tab1:
        st.header("あなたの文体をAIにインプット")
        
        persona = st.text_area("1. あなたのスタンス・職業（例：辛口のマーケター）", height=100)
        sample1 = st.text_area("2. 過去のサンプル記事 1", height=200)
        sample2 = st.text_area("3. 過去のサンプル記事 2（オプション）", height=200)

        if st.button("文体を分析し、クローンを生成（記憶）する"):
            if not api_key:
                st.error("左のサイドバーからAPIキーを入力してください。")
            elif not persona or not sample1:
                st.error("「スタンス」と「サンプル記事1」は必須項目です。")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')

                    meta_prompt = f"""
                    あなたは言語学者です。以下のユーザー属性とサンプル文章から、AIがこの文体を完全に模倣するための【システムプロンプト】を作成してください。
                    【属性】{persona}
                    【サンプル1】{sample1}
                    【サンプル2】{sample2}
                    要件: 1.役割 2.トーン＆マナー 3.文末表現の癖 4.AI特有の表現（結論から言うと等）の禁止 5.サンプルを模倣例として組み込む。
                    出力はマークダウン形式のプロンプト本文のみ。
                    """

                    with st.spinner("あなたの脳内をスキャン中...（最大1分）"):
                        response = model.generate_content(meta_prompt)
                        st.session_state.clone_prompt = response.text
                        st.success("✅ クローンの生成と記憶が完了しました！「2. クローンに執筆させる」タブに移動してください。")

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    with tab2:
        st.header("クローンに記事を書かせる")
        
        theme = st.text_area("アプリ①で作った【最終プロット】をここに貼り付けてください", height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("人間らしさの揺らぎ（Temperature）", 0.0, 1.0, 0.7, 0.1)
        with col2:
            word_count = st.slider("文字数の目安", 500, 3000, 1000, 100)

        if st.button("✨ クローンに執筆を開始させる"):
            if not api_key:
                st.error("左のサイドバーからAPIキーを入力してください。")
            elif not st.session_state.clone_prompt:
                st.error("先に「1. クローンに学習させる」タブで、あなたの文体を記憶させてください。")
            elif not theme:
                st.error("テーマを入力してください。")
            else:
                try:
                    genai.configure(api_key=api_key)
                    clone_model = genai.GenerativeModel(
                        'gemini-2.5-flash',
                        system_instruction=st.session_state.clone_prompt
                    )
                    config = genai.GenerationConfig(temperature=temperature)
                    prompt = f"以下のテーマについて、約{word_count}文字でコラムを執筆してください。\nテーマ：{theme}"

                    with st.spinner("猛烈な勢いでタイピングしています..."):
                        response = clone_model.generate_content(prompt, generation_config=config)
                        st.session_state.generated_text = response.text

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

        if st.session_state.generated_text:
            st.subheader("📝 エディター（自由に加筆・修正してください）")
            edited_text = st.text_area(
                "ここで直接文字を打ち込んで手直しができます。", 
                value=st.session_state.generated_text, 
                height=500
            )
