import os
import logging
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Constants
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
COLLECTION_NAME = "company_docs"

# Sentence Transformer initialization (Loaded once)
_model = None
_chroma_client = None

def get_embedding_model() -> SentenceTransformer:
    """
    Retrieves the sentence-transformers model instance.
    """
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Retrieves the persistent ChromaDB client.
    """
    global _chroma_client
    if _chroma_client is None:
        logger.info(f"Initializing ChromaDB client at {CHROMA_DB_PATH}...")
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client

def embed(text: str) -> list:
    """
    Generates embedding vector (list of floats) for a given text.
    """
    model = get_embedding_model()
    # Handles both single strings and lists of strings
    if isinstance(text, str):
        return model.encode(text).tolist()
    return model.encode(list(text)).tolist()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Splits text into chunks of specified size with overlap.
    """
    chunks = []
    text_len = len(text)
    if text_len <= chunk_size:
        return [text]
    
    start = 0
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        # Move forward by chunk_size - overlap
        start += (chunk_size - overlap)
        # Avoid infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            break
    return chunks

def load_documents(folder_path: str):
    """
    Loads all .txt files from folder_path, chunks them, and stores them in ChromaDB.
    Skips indexing if documents are already loaded.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Check if already populated
    current_count = collection.count()
    if current_count > 0:
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' already has {current_count} documents. Skipping indexing.")
        return
        
    if not os.path.exists(folder_path):
        logger.warning(f"Documents folder not found: {folder_path}")
        return

    logger.info(f"Loading documents from {folder_path} into ChromaDB...")
    
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    if not txt_files:
        logger.warning("No .txt files found to load.")
        return

    for filename in txt_files:
        filepath = os.path.join(folder_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            chunks = chunk_text(text, chunk_size=500, overlap=50)
            logger.info(f"Split {filename} into {len(chunks)} chunks.")
            
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{filename}_chunk_{idx}"
                vector = embed(chunk)
                
                ids.append(chunk_id)
                documents.append(chunk)
                embeddings.append(vector)
                metadatas.append({"source": filename, "chunk_index": idx})
            
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Added chunks for {filename} to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to read/index document {filename}: {e}")
            raise e

def search(query: str, n_results: int = 5) -> list:
    """
    Searches ChromaDB for the top n_results matching the semantic query.
    Returns a list of matching document string chunks.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    
    try:
        query_vector = embed(query)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results
        )
        # Parse output
        if results and 'documents' in results and len(results['documents']) > 0:
            return results['documents'][0]
        return []
    except Exception as e:
        logger.error(f"Error querying vector store: {e}")
        return []
