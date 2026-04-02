import streamlit as st
from google import genai
import requests
import time
import xml.etree.ElementTree as ET

st.set_page_config(page_title="学術リサーチ自動化エージェント", layout="wide")

# --- パスワード認証 ---
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

# ==========================================
# 各種データベースの検索エンジン（API連携）
# ==========================================

# 1. Semantic Scholar (総合・英語)
def fetch_semantic_scholar(query, limit):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,authors,year,abstract,url"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code == 429:
        st.error("Semantic Scholarが混雑しています。時間を置くか、別のデータベースを試してください。")
        return []
    response.raise_for_status()
    papers = []
    for p in response.json().get('data', []):
        if p.get('abstract'):
            papers.append({
                "title": p.get('title', ''),
                "authors": ", ".join([a['name'] for a in p.get('authors', [])]),
                "year": str(p.get('year', '')),
                "abstract": p.get('abstract', ''),
                "url": p.get('url', '')
            })
    return papers

# 2. CiNii Research (国内・日本語)
def fetch_cinii(query, limit):
    url = f"https://cir.nii.ac.jp/opensearch/all?q={query}&format=json&count={limit}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    papers = []
    items = response.json().get("@graph", [{}])[0].get("items", [])
    for item in items:
        abstract = item.get("description", "")
        if abstract: # 概要があるもののみ抽出
            authors = item.get("dc:creator", "Unknown")
            if isinstance(authors, list):
                authors = ", ".join([a.get("@value", "") for a in authors if isinstance(a, dict)])
            papers.append({
                "title": item.get("title", ""),
                "authors": str(authors),
                "year": item.get("dc:date", "Unknown")[:4] if item.get("dc:date") else "Unknown",
                "abstract": abstract,
                "url": item.get("@id", "")
            })
    return papers

# 3. PubMed / EuropePMC (医療・健康)
def fetch_pubmed(query, limit):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={query}&format=json&resultType=core&pageSize={limit}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    papers = []
    for item in response.json().get("resultList", {}).get("result", []):
        abstract = item.get("abstractText", "")
        if abstract:
            pmid = item.get('pmid', '')
            papers.append({
                "title": item.get("title", ""),
                "authors": item.get("authorString", ""),
                "year": str(item.get("pubYear", "")),
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            })
    return papers

# 4. arXiv (AI・物理・IT)
def fetch_arxiv(query, limit):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={limit}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    papers = []
    for entry in root.findall('atom:entry', ns):
        abstract = entry.find('atom:summary', ns).text
        if abstract:
            papers.append({
                "title": entry.find('atom:title', ns).text.replace('\n', ' '),
                "authors": ", ".join([a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]),
                "year": entry.find('atom:published', ns).text[:4],
                "abstract": abstract.replace('\n', ' '),
                "url": entry.find('atom:id', ns).text
            })
    return papers

# 5. OpenAlex (全分野・巨大DB)
def fetch_openalex(query, limit):
    url = f"https://api.openalex.org/works?search={query}&per-page={limit}"
    headers = {"User-Agent": "mailto:personal_research@example.com"} # 優先レーン用
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    papers = []
    for item in response.json().get("results", []):
        inv_index = item.get("abstract_inverted_index")
        if inv_index:
            # 圧縮された要旨データを復元
            max_idx = max([max(positions) for positions in inv_index.values()])
            words = [""] * (max_idx + 1)
            for word, positions in inv_index.items():
                for pos in positions: 
                    words[pos] = word
            abstract = " ".join(words)
            papers.append({
                "title": item.get("title", ""),
                "authors": ", ".join([a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]),
                "year": str(item.get("publication_year", "")),
                "abstract": abstract,
                "url": item.get("id", "")
            })
    return papers

# ==========================================
# メイン画面
# ==========================================
if check_password():
    st.title("🔬 学術リサーチ＆サマリー自動化エージェント (Multi-Engine)")
    st.write("検索エンジンを切り替えることで、世界の先端研究から国内の泥臭い調査まで、あらゆるエビデンスを自動収集・要約します。")

    with st.sidebar:
        st.header("⚙️ 初期設定")
        api_key = st.text_input("Gemini APIキーを入力", type="password")
        
        st.markdown("---")
        st.subheader("📚 検索エンジンの選択")
        engine_choice = st.selectbox(
            "論文の仕入れ先",
            (
                "Semantic Scholar (総合・英語)",
                "CiNii Research (国内・日本語)", 
                "OpenAlex (全分野・巨大DB)",
                "PubMed (医療・生物)",
                "arXiv (AI・IT・物理)"
            )
        )
        paper_count = st.slider("検索する論文数（最大）", 3, 10, 5)

    st.subheader("📊 リサーチ条件の入力")
    research_theme = st.text_input(
        "研究テーマ・キーワード", 
        help="CiNiiは日本語、それ以外は英語で入力すると精度が高まります。"
    )
    
    if st.button("🚀 実データ検索 ＆ サマリー生成を開始"):
        if not api_key:
            st.error("左のサイドバーからGemini APIキーを入力してください。")
        elif not research_theme:
            st.error("研究テーマを入力してください。")
        else:
            with st.spinner(f"ステップ1/2: 【{engine_choice}】から実在する論文を検索中..."):
                try:
                    if "Semantic Scholar" in engine_choice: papers = fetch_semantic_scholar(research_theme, paper_count)
                    elif "CiNii" in engine_choice: papers = fetch_cinii(research_theme, paper_count)
                    elif "PubMed" in engine_choice: papers = fetch_pubmed(research_theme, paper_count)
                    elif "arXiv" in engine_choice: papers = fetch_arxiv(research_theme, paper_count)
                    elif "OpenAlex" in engine_choice: papers = fetch_openalex(research_theme, paper_count)
                    time.sleep(1)
                except Exception as e:
                    st.error(f"データベース通信エラー: {e}")
                    papers = []

            if not papers:
                st.warning("アブストラクト（要旨）を持つ論文データが取得できませんでした。キーワードを変えるか、検索エンジンを切り替えてみてください。")
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
                        st.success(f"✅ 【{engine_choice}】のデータに基づくレポートが完成しました！")
                        st.markdown(response.text)
                        
                        with st.expander("🔍 AIが読み込んだ元の論文データ（生のアブストラクト）を確認する"):
                            for p in papers:
                                st.markdown(f"**[{p['title']}]({p['url']})** ({p['year']})")
                                st.caption(p['abstract'])
                                st.divider()

                    except Exception as e:
                        st.error(f"サマリー生成中にエラーが発生しました: {e}")
