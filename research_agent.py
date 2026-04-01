import streamlit as st
from google import genai
import requests
import time

st.set_page_config(page_title="学術リサーチ自動化エージェント", layout="wide")

# --- パスワード認証システム ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔒 学術リサーチ・エージェント（会員限定）")
        pwd = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if pwd == "arata2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("パスワードが間違っています。")
        return False
    return True

# --- 論文検索用関数（429エラー対策版） ---
def fetch_real_papers(query, limit=5, s2_api_key=""):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,authors,year,abstract,url,publicationTypes"
    
    # 門番に弾かれないための「身分証明書（ヘッダー）」を設定
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    
    # もし専用APIキーがあれば、VIPパスとして追加する
    if s2_api_key:
        headers["x-api-key"] = s2_api_key

    try:
        # 連続アクセスと思われないよう、一呼吸（1秒）置く
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=15)
        
        # もし429エラーが出たら、専用のエラーメッセージを出す
        if response.status_code == 429:
            st.error("【サーバー混雑エラー (429)】論文データベースへのアクセスが集中し、一時的に制限されています。数分待ってから再度お試しいただくか、サイドバーからSemantic ScholarのAPIキーを入力してください。")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        valid_papers = []
        for paper in data.get('data', []):
            if paper.get('abstract'):
                authors = ", ".join([a['name'] for a in paper.get('authors', [])])
                valid_papers.append({
                    "title": paper.get('title', 'No Title'),
                    "authors": authors,
                    "year": paper.get('year', 'Unknown'),
                    "abstract": paper.get('abstract', ''),
                    "url": paper.get('url', '')
                })
        return valid_papers
        
    except requests.exceptions.RequestException as e:
        st.error(f"通信エラーが発生しました: {e}")
        return []

# --- 本編 ---
if check_password():
    st.title("🔬 学術リサーチ＆サマリー自動化エージェント")
    st.write("入力されたテーマに基づき、世界中の学術データベースから実在する論文を検索。その内容をAIが読み込み、瞬時にサマリーレポートを作成します。（※ハルシネーションを防止するRAGアーキテクチャ採用）")

    with st.sidebar:
        st.header("⚙️ 初期設定")
        api_key = st.text_input("1. Gemini APIキーを入力", type="password")
        
        st.markdown("---")
        st.write("※データベースの混雑エラー(429)が頻発する場合は、無料の専用キーを取得して入力してください。")
        s2_api_key = st.text_input("2. Semantic Scholar APIキー（任意）", type="password")
        
        st.markdown("---")
        paper_count = st.slider("検索する論文数（最大）", 3, 10, 5)

    st.subheader("📊 リサーチ条件の入力")
    research_theme = st.text_input("研究テーマ・キーワード（例：LLM in medical diagnosis）", help="※英語で入力すると、より精度の高い最新論文がヒットしやすくなります。")
    
    if st.button("🚀 実データ検索 ＆ サマリー生成を開始"):
        if not api_key:
            st.error("左のサイドバーからGemini APIキーを入力してください。")
        elif not research_theme:
            st.error("研究テーマを入力してください。")
        else:
            with st.spinner("ステップ1/2: 世界中の学術データベースから実在する論文を検索中..."):
                papers = fetch_real_papers(research_theme, limit=paper_count, s2_api_key=s2_api_key)

            if not papers:
                st.warning("論文データを取得できませんでした。時間をおいて試すか、キーワードを変更してください。")
            else:
                with st.spinner(f"ステップ2/2: 見つかった {len(papers)} 件の論文データをAIに読み込ませ、統合サマリーを執筆中..."):
                    papers_text = ""
                    for i, p in enumerate(papers, 1):
                        papers_text += f"【論文{i}】\nTitle: {p['title']}\nYear: {p['year']}\nAuthors: {p['authors']}\nAbstract: {p['abstract']}\nURL: {p['url']}\n\n"

                    summary_prompt = f"""
                    あなたは優秀なシニアリサーチャーです。
                    以下の「実際の論文データ」のみを情報源として、指定されたテーマに関する包括的なサマリーレポートを日本語で作成してください。
                    
                    【テーマ】{research_theme}
                    
                    【厳守事項】
                    1. 決してあなたの事前知識で架空の論文を作らないでください。必ず以下の【実際の論文データ】の内容のみに基づいて記述してください。
                    2. レポートは以下の構成で出力してください。
                       - はじめに（このテーマの現在の重要性）
                       - 収集した論文の統合サマリー（トレンド、主要な発見、見解の対立など）
                       - 今後の研究の余地（ギャップ）
                       - 参考文献リスト（タイトル、著者、発行年、URLをリスト化）

                    【実際の論文データ】
                    {papers_text}
                    """

                    try:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=summary_prompt
                        )
                        st.success("✅ リサーチレポートの作成が完了しました！")
                        st.markdown(response.text)
                        
                        with st.expander("🔍 AIが読み込んだ元の論文データ（生のアブストラクト）を確認する"):
                            for p in papers:
                                st.markdown(f"**[{p['title']}]({p['url']})** ({p['year']})")
                                st.caption(p['abstract'])
                                st.divider()

                    except Exception as e:
                        st.error(f"サマリー生成中にエラーが発生しました: {e}")
