import os
import sys
import argparse
import numpy as np
import cohere
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import track
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class ConsoleFallback:
        def print(self, *args, **kwargs):
            print(*args)
    console = ConsoleFallback()

# Supported file extensions for code
SUPPORTED_EXTENSIONS = {
    '.py', '.cpp', '.hpp', '.c', '.h', '.go', '.js', '.ts', 
    '.java', '.rs', '.tsx', '.jsx', '.cs', '.rb', '.md'
}

IGNORED_DIRS = {
    '.git', 'node_modules', 'venv', 'env', '__pycache__', 
    'build', 'dist', 'target', '.idea', '.vscode'
}

def chunk_text(text, filename, chunk_size=100, overlap=20):
    """Splits a file into chunks of lines."""
    lines = text.split('\n')
    chunks = []
    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        if not chunk_lines:
            break
        snippet = '\n'.join(chunk_lines)
        chunks.append({
            'title': filename,
            'snippet': snippet,
            'start_line': str(i + 1),
            'end_line': str(i + len(chunk_lines))
        })
    return chunks

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    parser = argparse.ArgumentParser(description="Cohere Code Search (RAG on Code)")
    parser.add_argument("repo_path", help="Path to the repository to index")
    parser.add_argument("--query", "-q", help="Question to ask about the codebase", required=True)
    args = parser.parse_args()

    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        console.print("[red]Error: COHERE_API_KEY environment variable not set.[/red]")
        console.print("Get your free API key at https://dashboard.cohere.com/")
        sys.exit(1)

    co = cohere.Client(api_key)
    repo_path = Path(args.repo_path).resolve()
    
    if not repo_path.is_dir():
        console.print(f"[red]Error: {repo_path} is not a valid directory.[/red]")
        sys.exit(1)

    # 1. Read and chunk files
    console.print(f"[cyan]Indexing codebase at:[/cyan] {repo_path}")
    documents = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    rel_path = str(file_path.relative_to(repo_path))
                    documents.extend(chunk_text(text, rel_path))
                except Exception as e:
                    # Skip files that can't be read (e.g. binary disguised as text)
                    pass

    if not documents:
        console.print("[red]No supported code files found in the directory.[/red]")
        sys.exit(1)
        
    console.print(f"[green]Found {len(documents)} code chunks. Embedding...[/green]")

    import time
    
    # 2. Embed the documents
    # The Cohere free tier has a limit of 100,000 tokens per minute.
    # We reduce the batch size and add a sleep to avoid hitting the rate limit.
    batch_size = 20
    embeddings = []
    
    if RICH_AVAILABLE:
        iterator = track(range(0, len(documents), batch_size), description="Generating Embeddings...")
    else:
        iterator = range(0, len(documents), batch_size)
        print("Generating embeddings...")

    for i in iterator:
        batch = documents[i:i + batch_size]
        texts = [doc['snippet'] for doc in batch]
        
        # Simple retry loop for rate limits
        while True:
            try:
                response = co.embed(
                    texts=texts,
                    model='embed-english-v3.0',
                    input_type='search_document'
                )
                embeddings.extend(response.embeddings)
                break # Success, break out of retry loop
            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower() or "TooManyRequests" in str(type(e).__name__):
                    # Sleep for a minute if we hit the limit
                    time.sleep(60)
                else:
                    raise e
        
        # Small sleep between batches to spread out requests
        time.sleep(1)
    
    embeddings = np.array(embeddings)

    # 3. Embed the query
    console.print(f"\n[cyan]Querying:[/cyan] {args.query}")
    query_response = co.embed(
        texts=[args.query],
        model='embed-english-v3.0',
        input_type='search_query'
    )
    query_embedding = np.array(query_response.embeddings[0])

    # 4. Calculate similarities and get top K
    similarities = [cosine_similarity(query_embedding, doc_emb) for doc_emb in embeddings]
    top_k_indices = np.argsort(similarities)[-5:][::-1] # Get top 5
    
    top_docs = [documents[i] for i in top_k_indices]
    
    # 5. Generate Answer with Command-R using documents for RAG
    console.print("[cyan]Analyzing code with Command-R...[/cyan]\n")
    
    chat_response = co.chat(
        message=args.query,
        model="command-r-plus-08-2024",
        documents=top_docs,
        prompt_truncation="AUTO"
    )

    # 6. Display results
    if RICH_AVAILABLE:
        console.print(Panel(Markdown(chat_response.text), title="Cohere Command-R Response", border_style="green"))
        
        if chat_response.citations:
            console.print("\n[bold yellow]Citations (Code Snippets Used):[/bold yellow]")
            for citation in chat_response.citations:
                doc_ids = citation.document_ids
                for doc_id in doc_ids:
                    doc = next((d for d in top_docs if d.get('id') == doc_id), None)
                    # The API assigns IDs to documents dynamically like 'doc_0'
                    # We will just print the cited source files
            
            cited_titles = set()
            for doc in chat_response.documents:
                cited_titles.add(f"{doc['title']} (Lines {doc.get('start_line', '?')}-{doc.get('end_line', '?')})")
            
            for title in cited_titles:
                console.print(f"- [cyan]{title}[/cyan]")
    else:
        print("\n--- Cohere Command-R Response ---")
        print(chat_response.text)
        print("\nCitations:")
        for doc in chat_response.documents:
            print(f"- {doc['title']} (Lines {doc.get('start_line')}-{doc.get('end_line')})")

if __name__ == "__main__":
    main()
