import os
from flask import Flask, request, render_template
from rank_bm25 import BM25Okapi
import pandas as pd

# -----------------------------
# Load preprocessed glossary data
# -----------------------------

# Expecting CSV: content/parsed_glossary.csv
# Columns: docno, text
df = pd.read_csv("content/parsed_glossary.csv")

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

