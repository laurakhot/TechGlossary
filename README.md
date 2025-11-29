# TechGlossary

This project is a search application built on top of the MDN Glossary repository. It parses Markdown files from the MDN content repository, extracts raw text, indexes the data using PyTerrier, and provides retrieval capabilities with TF-IDF and BM25 models. A simple and modern Flask web UI allows users to search and explore glossary entries.

### Retrieval Models

- **TF-IDF**: Standard term frequency-inverse document frequency scoring  
- **BM25**: Okapi BM25 scoring for improved relevance ranking

### Key Libraries Installed

- **frontmatter** – parse Markdown metadata  
- **pandas** – structure and manipulate data  
- **markdown** – convert Markdown to HTML  
- **beautifulsoup4** – extract raw text from HTML  
- **pyterrier** – indexing and retrieval  
- **flask** – web application framework
