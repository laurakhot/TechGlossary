import os
from flask import Flask, request, render_template
from rank_bm25 import BM25Okapi
import pandas as pd
import frontmatter
import markdown
from bs4 import BeautifulSoup
import re

# -----------------------------
# Load glossary from markdown files
# -----------------------------
def load_glossary_for_pyterrier(glossary_root: str) -> pd.DataFrame:
    rows = []
    for term_folder in os.listdir(glossary_root):
        folder_path = os.path.join(glossary_root, term_folder)
        if os.path.isdir(folder_path):
            md_file = os.path.join(folder_path, "index.md")
            if os.path.exists(md_file):
                try:
                    post = frontmatter.load(md_file)
                    content_no_placeholders = re.sub(r"\{\{.*?\}\}", "", post.content)
                    html_content = markdown.markdown(content_no_placeholders)
                    plain_text = BeautifulSoup(html_content, "html.parser").get_text()
                    clean_text = re.sub(r"\s+", " ", plain_text).strip()
                    
                    rows.append({
                        "docno": term_folder,
                        "text": clean_text,
                        "html": html_content
                    })
                except Exception as e:
                    print(f"Error processing {md_file}: {e}")
    
    return pd.DataFrame(rows, columns=["docno", "text", "html"])

# Load data at startup
glossary_root = "content/files/en-us/glossary"
df = load_glossary_for_pyterrier(glossary_root)

# BM25 initialization
corpus = df["text"].astype(str).tolist()
tokenized = [doc.lower().split() for doc in corpus]
bm25 = BM25Okapi(tokenized)

# -----------------------------
# Flask application setup
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Search Route
# -----------------------------
@app.route("/", methods=["GET"])
def search():
    query = request.args.get("q", "")

    results = []
    if query:
        tokens = query.lower().split()
        scores = bm25.get_scores(tokens)

        # Get top 5
        top = (
            pd.DataFrame({
                "docno": df["docno"],
                "text": df["text"],
                "score": scores
            })
            .sort_values(by="score", ascending=False)
            .head(5)
        )

        # Format results for rendering
        for rank, (_, row) in enumerate(top.iterrows(), start=1):
            results.append({
                "rank": rank,
                "docno": row["docno"],
                "snippet": row["text"][:200],
                "score": round(row["score"], 3)
            })

    return render_template("index.html", results=results, query=query)


# -----------------------------
# Full Document Viewer
# -----------------------------
@app.route("/doc/<docno>")
def show_doc(docno):
    row = df[df["docno"] == docno]
    if row.empty:
        return "Document not found", 404

    full_text = row["text"].iloc[0]
    return render_template("doc_view.html", docno=docno, full_text=full_text)


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
