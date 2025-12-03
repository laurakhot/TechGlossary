import os 
import pandas as pd
import frontmatter
import re
import markdown
from bs4 import BeautifulSoup
import html
from flask import Flask, request, render_template
import string
from rank_bm25 import BM25Okapi
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
import nltk
nltk.download('stopwords')  
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))

# -----------------------------
# Load MDN dataset
# -----------------------------
def load_md_glossary(glossary_root: str) -> pd.DataFrame:
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
    
    return pd.DataFrame(rows, columns=["docno", "text"])

# Load data at startup
glossary_root = "content/files/en-us/glossary"
mdn_df = load_md_glossary(glossary_root)

# -----------------------------
# Load GlossaryTech source 
# -----------------------------
glossary_items = []

def clean_text(cell):
    text = " ".join(cell.stripped_strings)
    text = html.unescape(text) # unescape HTML entities
    text = text.replace('\xa0', ' ') # replace non-breaking space with normal space
    text = re.sub(r'\s+([?,.!;:])', r'\1', text) # remove space before punctuation: "XML , " -> "XML,"
    text = re.sub(r'([?,.!;:])\s*', r'\1 ', text) # one space after punctuation
    text = re.sub(r'\s+\)', r')', text) # spaces around opening parenthesis
    text = re.sub(r'\(\s+', r'(', text) # spaces around closing parenthesis
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_html_glossary(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    for table in tables: 
        rows = table.find_all("tr", attrs={"data-term": True})
        for row in rows: 
            cells = row.find_all("td")
            if len(cells) >= 2:  
                term = clean_text(cells[0])
                description = clean_text(cells[1])
                glossary_items.append({'docno': term, 'text': description})


directory = "glossary_tech"
for filename in os.listdir(directory):
    filepath = os.path.join(directory, filename)  
    if os.path.isfile(filepath): # check not subdirectory 
        load_html_glossary(filepath)
        
html_df = pd.DataFrame(glossary_items)

# Combining the data sources 
df = pd.concat([html_df, mdn_df], ignore_index=True)
df['clean_descr'] = df['text']
df['clean_term'] = df['docno'].astype(str)
df['clean_text'] = df['clean_term'] + " . " + df['clean_descr'] + " . " + df['clean_term']

# -----------------------------
# Initializing BM25 from Index
# -----------------------------
# pt.init()
# index_ref = pt.IndexFactory.of("./glossary_index/data.properties")
# bm25 = pt.BatchRetrieve(index_ref, wmodel="BM25") 
# try:
#     index_path = "./glossary_index/data.properties"
#     if not os.path.exists(index_path):
#         raise FileNotFoundError(f"Index not found at {index_path}")
    
#     index_ref = pt.IndexFactory.of(index_path)
#     bm25 = pt.BatchRetrieve(index_ref, wmodel="BM25")
#     print("BM25 retriever initialized successfully.")
# except Exception as e:
#     print("Error initializing BM25:", e)
#     bm25 = None
def clean_and_tokenize(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = text.split()
    tokens = [stemmer.stem(t) for t in tokens if t not in stop_words]
    return tokens

tokenized_corpus = [clean_and_tokenize(doc) for doc in df["clean_text"].tolist()]
bm25 = BM25Okapi(tokenized_corpus)


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
        query_tokens = clean_and_tokenize(query)
        doc_scores = bm25.get_scores(query_tokens)
        top_indices = doc_scores.argsort()[-5:][::-1]

        for rank, idx in enumerate(top_indices, start=1):
            doc = df.iloc[idx]
            results.append({
                "rank": rank,
                "docno": doc["docno"],
                "snippet": doc["text"][:200],
                "score": round(doc_scores[idx], 3)
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
