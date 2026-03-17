# 📚 PDF Intelligence & Smart Entity Researcher

An AI-powered document assistant that doesn't just summarize—it **understands**. This tool extracts key entities from your files and performs web searches using context-aware re-ranking and "Light Dorking" to ensure you get the historical facts you need, not irrelevant search noise

used a carefully chosen LLM that uses few ressources and specializes in text summary to optimize memory consumption and reduce latency !

---

## 🚀 Key Features

* **Smart Context Extraction:** identifies the topic in 2/3 words to ground all future searches
* **Entity Search:** Uses a hybrid DuckDuckGo + Wikipedia logic. It does ranks search results based on document relevance
* **Local LLM Integration:** Powered by **Ollama**, ensuring your document data stays private and local
* **Question Answering:** Distinguishes Extractive vs Abstractive Question Answering

---

## 🛠️ The Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Streamlit |
| **Brain (LLM)** | Ollama (qwen3:0.6b) |
| **NLP Engine** | spaCy (`en_core_web_sm`) |
| **Search Engine** | DuckDuckGo (via `ddgs`) |
| **Data Source** | Wikipedia API |
| **PDF Parsing** | PyMuPDF (`fitz`) |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) |

---

## 📥 Installation

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/JO-00/file-researcher
    cd pdf-intel-researcher
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Download the SpaCy language model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```
4.  **Ensure Ollama is running:**
    Make sure you have Ollama installed and the model pulled:
    ```bash
    ollama pull qwen3:0.6b
    ```

5.  **Launch the App:**
    ```bash
    streamlit run main.py
    ```

---

## 🧠 Handling the "Irrelevance" Problem

Despite being efficient with many search results in terms of relevance, information about some entities aren't currently correctly fetched  **(working to fix that)**

### Current Solution: Semantic Re-Ranking
`external_search.py` does the following:
1.  **Broad Fetch:** grabs 10 results from DuckDuckGo.
3.  **The Pivot:** Results containing anchor words get a score boost; irrelevant "popular" results are penalized
4.  **Exact Matching:** Entity is therefore wrapped in double quotes `"Entity Name"` to prevent the search engine from splitting the name (basic google dorking)



---

## 📁 Project Structure

* `main.py`: The Streamlit interface and session state management.
* `models.py`: Singleton-style initialization for LLM and NLP tools.
* `query_handlers/`
    * `external_search.py`: The "Smart Search" engine with dorking and re-ranking.
    * `extract_people.py`: Just scans the whole document to find people names via **NLP**
    * `summarizer.py`: Either provides bullet points for summary or a 2-3 word topic (quite helpful for the search engine)
    * `extract_dates.py`
    * `specific_qa.py`: Answers specific precise questions
    * `broad_qa.py`: Answers broad questions
* `fileloader.py` : simply load the pdf file into place
* `utils/`: PDF processing and text cleaning utilities.
