import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="プロット生成エージェント", layout="wide")

# --- ここから：パスワード認証システム ---
def check_password():
    """パスワードが正しければTrueを返す"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 深掘りプロット生成（会員限定）")
        st.write("note記事で発行されたパスワードを入力してください。")
        
        # パスワード入力欄
        pwd = st.text_input("パスワード", type="password")
        
        if st.button("ログイン"):
            if pwd == "arata2026":  # アプリ間で共通のパスワード
                st.session_state["password_correct"] = True
                st.rerun() # 画面をリロード
            else:
                st.error("パスワードが間違っています。")
        return False
    return True

# --- パスワードが正しい場合のみ、以下の本編を表示する ---
if check_password():
    
    st.title("🧠 深掘りプロット生成エージェント")
    st.write("思いつきのアイデアを、AIが「7段階の思考プロセス」で限界まで深掘りし、執筆クローン用の完璧な構成案（指示書）を作成します。")

    with st.sidebar:
        st.header("⚙️ 初期設定")
        api_key = st.text_input("Gemini APIキーを入力", type="password")
        st.write("※APIキーは保存されません。")

    st.subheader("📝 企画の種（アイデア）を入力")
    theme = st.text_input("テーマ（例：リモートワークにおける雑談の重要性）")
    keywords = st.text_input("キーワード（例：孤独感、心理的安全性、イノベーション、タバコ部屋）")
    summary = st.text_area("内容概略（思いついていることを箇条書きなどで自由に）", height=100)

    if st.button("🔥 7段階の脳内会議を開始し、プロットを生成する"):
        if not api_key:
            st.error("左のサイドバーからAPIキーを入力してください。")
        elif not theme:
            st.error("テーマは必須項目です。")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')

                agent_prompt = f"""
                あなたは日本トップクラスの敏腕編集者であり、深い洞察力を持つリサーチャーです。
                ユーザーから与えられた以下の「企画の種」を元に、絶対にありきたりな記事にならないよう、以下の【7つのステップ】を順番に実行し、深く鋭いプロット（構成案）を作成してください。

                【企画の種】
                ・テーマ: {theme}
                ・キーワード: {keywords}
                ・内容概略: {summary}

                【実行すべき7つのステップ】
                必ずステップ番号と見出しを書き、あなたの思考過程を明文化しながら進めてください。
                
                ステップ1【リサーチ】: このテーマに関する一般的な常識、世間の思い込み、読者の潜在的な悩みを列挙する。
                ステップ2【考察】: ステップ1を踏まえ、「よくある一般論」を打破するための『独自の切り口』や『逆説的な視点』を模索する。
                ステップ3【仮構成】: 導入・本文・結論の骨組みを仮で作成する。
                ステップ4【再考察】: 仮構成の弱点、論理の飛躍、読者が退屈しそうな箇所を批判的にチェックし、ダメ出しをする。
                ステップ5【再リサーチ】: ダメ出しされた箇所を補強するための、具体的な事例のアイデアや比喩表現を考える。
                ステップ6【再々考察】: 最終的なメッセージの強度を最大化するため、結論のトーンや余韻の残し方を推敲する。
                ステップ7【最終プロット作成】: これまでの全思考を統合し、ライター（執筆AI）に渡すための「詳細な構成と内容の指示書」を作成する。

                【出力ルール】
                ステップ1〜6までは「思考プロセス」として出力し、最後のステップ7はそのままコピーして使えるように明確に区切って出力してください。
                """

                status_text = st.empty()
                progress_bar = st.progress(0)

                steps = ["リサーチ中...", "独自の切り口を模索中...", "仮構成を作成中...", "構成にダメ出し中...", "事例を補強中...", "最終推敲中...", "プロット出力中..."]
                for i in range(7):
                    status_text.write(f"🧠 {steps[i]}")
                    progress_bar.progress((i + 1) * 14)
                    time.sleep(0.5)

                status_text.write("✨ 脳内会議完了！出力しています...")
                progress_bar.progress(100)

                response = model.generate_content(agent_prompt)

                st.success("プロットの生成が完了しました！")
                st.markdown(response.text)

                st.info("💡 【使い方】一番下にある「ステップ7」の内容を全選択してコピーし、執筆クローンアプリの【テーマ】欄に貼り付けて執筆させてください！")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
