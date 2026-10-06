<div align="center">
  <img src="https://github.com/user-attachments/assets/PLACEHOLDER_IMAGE_URL" alt="Cohere RepoRAG Banner" width="800"/>
  
  <h1>Cohere RepoRAG</h1>
  <p><strong>A fast, lightweight CLI tool that semantic-searches local codebases with precise citation grounding using Cohere Command-R+.</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
  [![Cohere API](https://img.shields.io/badge/Powered_by-Cohere-5e50ee.svg)](https://cohere.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## 📖 Overview
**Cohere RepoRAG** is a developer-focused CLI utility that brings Retrieval-Augmented Generation (RAG) directly into your local terminal. By indexing a local Git repository, it allows developers to ask complex, architectural questions about their systems and receive highly accurate, **verifiably grounded** answers.

Built specifically to showcase the power of **Cohere's Enterprise AI stack**, this tool leverages:
- **`embed-english-v3.0`**: For semantic chunking and high-accuracy vector retrieval of code snippets.
- **`command-r-plus-08-2024`**: For synthesizing architectural explanations with native, rigorous **Citation Grounding** (explicitly referencing exact file paths and line numbers).

## ✨ Features
- **Local Codebase Indexing:** Recursively parses supported code files (`.py`, `.cpp`, `.go`, `.js`, etc.) while intelligently ignoring build artifacts and virtual environments.
- **Rate-Limit Resilient:** Built-in smart chunking, batching, and automated retry loops to smoothly respect API rate limits.
- **Precision Citations:** Uses Cohere's documents parameter to provide verifiable answers—never hallucinations.
- **Beautiful CLI Output:** Uses `Rich` to format markdown, panels, and progress bars natively in the terminal.

## 🚀 Quick Start

### 1. Installation
Clone the repository and install the minimal dependencies:
```bash
git clone https://github.com/Abh-igyan/Cohere-RepoRAG.git
cd Cohere-RepoRAG
pip install cohere numpy rich
```

### 2. Setup API Key
Obtain a free API key from the [Cohere Dashboard](https://dashboard.cohere.com/) and set it in your environment:

**Windows (PowerShell):**
```powershell
$env:COHERE_API_KEY="your_api_key_here"
```
**Linux / macOS:**
```bash
export COHERE_API_KEY="your_api_key_here"
```

### 3. Usage
Point the CLI at any local project directory and ask a question:
```bash
python cohere_code_search.py "/path/to/your/project" -q "Where is the main execution pipeline handled and how does it sandbox the code?"
```

**Example Output:**
```text
Indexing codebase at: /path/to/your/project
Found 236 code chunks. Embedding...
Generating Embeddings... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 

Querying: Explain the main architecture.
Analyzing code with Command-R+...

+------------------------- Cohere Command-R+ Response ------------------------+
| The backend is written in Python and uses the Flask framework. It uses a    |
| PostgreSQL database to store data and the SQLAlchemy ORM to interact with   |
| the database. The system leverages AWS Lambda for serverless functions      |
| and isolates execution pipelines into gVisor-sandboxed worker nodes.        |
+-----------------------------------------------------------------------------+

Citations (Code Snippets Used):
- backend/src/handlers/api.py (Lines 161-229)
- backend/src/engine/sandbox.py (Lines 321-339)
```

## 🛠️ Built With
- **[Cohere Python SDK](https://github.com/cohere-ai/cohere-python)**
- **[NumPy](https://numpy.org/)** (For fast cosine similarity)
- **[Rich](https://github.com/Textualize/rich)** (For beautiful CLI rendering)

## 📄 License
This project is licensed under the MIT License.
