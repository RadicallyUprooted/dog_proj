import json
import chromadb
from sentence_transformers import SentenceTransformer

# --- 1. Data Preparation ---
def chunk_text(text, chunk_size=256, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

print("Loading and chunking data...")
with open('msdvetmanual_dog_owners_data.json', 'r') as f:
    data = json.load(f)

chunked_data = []
for item in data:
    text_chunks = chunk_text(item['text'])
    for i, chunk in enumerate(text_chunks):
        chunked_data.append({
            "id": f"{item['id']}_{i}",
            "text": chunk,
            "metadata": {
                "url": item['url'],
                "chapter": item['chapter'],
                "topic": item['topic']
            }
        })

# --- 2. Database Setup and Population ---
DB_PATH = "./vet_manual_db"

print("Initializing embedding model...")
# Use a specific model for consistency across scripts
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Setting up persistent database at: {DB_PATH}")
# Use PersistentClient to save the database to disk
client = chromadb.PersistentClient(path=DB_PATH)

# Create a new collection or get it if it already exists
collection = client.get_or_create_collection(
    name="dog_diseases",
    metadata={"hnsw:space": "cosine"} # Using cosine similarity
)

print(f"Populating database with {len(chunked_data)} chunks...")
# Add data in batches for efficiency
batch_size = 100
for i in range(0, len(chunked_data), batch_size):
    batch = chunked_data[i:i+batch_size]
    
    ids = [item['id'] for item in batch]
    documents = [item['text'] for item in batch]
    metadatas = [item['metadata'] for item in batch]
    
    # Create embeddings for the batch
    embeddings = embedding_model.encode(documents).tolist()
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

print("\nDatabase creation complete!")
print(f"Total documents in collection: {collection.count()}")