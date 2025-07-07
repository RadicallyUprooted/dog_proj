import json
import math
import sys
import os
from transformers import AutoTokenizer
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MAX_TOKENS = 512
CHUNK_SIZE_TOKENS = 480
OVERLAP_TOKENS = 50
DB_PATH = "vector_dbs/vet_manual_faiss_db"


def main(input_json):
    '''
    Performs chunking of the given document based on E5 tokenizer, and then constructs FAISS vector store.
    '''

    with open(input_json, 'r') as f:
        data = json.load(f)

    embedding_model = 'intfloat/multilingual-e5-large'
    tokenizer = AutoTokenizer.from_pretrained(embedding_model)

    chunked_documents = []

    for item in data:
        full_text = item['text']
        tokens = tokenizer.encode(full_text, add_special_tokens=False)

        num_tokens = len(tokens)
        
        # Calculate the number of chunks needed
        num_chunks = math.ceil(num_tokens / (CHUNK_SIZE_TOKENS - OVERLAP_TOKENS)) if num_tokens > CHUNK_SIZE_TOKENS - OVERLAP_TOKENS else 1

        for i in range(num_chunks):
            start_token = i * (CHUNK_SIZE_TOKENS - OVERLAP_TOKENS)
            end_token = min(start_token + CHUNK_SIZE_TOKENS, num_tokens)

            # Handle overlap for subsequent chunks
            if i > 0:
                start_token = max(0, start_token - OVERLAP_TOKENS)

            chunk_tokens = tokens[start_token:end_token]
            chunk_text = tokenizer.decode(chunk_tokens)

            # Add the "passage:" prefix as recommended for E5 models
            prefixed_chunk_text = "passage: " + chunk_text

            final_chunk_tokens = tokenizer.encode(prefixed_chunk_text, truncation=True, max_length=MAX_TOKENS)
            final_chunk_text = tokenizer.decode(final_chunk_tokens)

            chunked_documents.append(Document(
                page_content=final_chunk_text,
                metadata={
                    "chapter": item['chapter'],
                    "topic": item['topic'],
                    "chunk_id": f"{item['id']}_{i}",
                    "token_count": len(final_chunk_tokens)
                }
            ))


    embeddings = HuggingFaceEmbeddings(model_name='intfloat/multilingual-e5-large')

    print(f"Setting up FAISS database at: {DB_PATH}")
    faiss_db = FAISS.from_documents(chunked_documents, embeddings)

    print("\nFAISS database creation complete!")
    print(f"Total documents in FAISS index (approx): {len(faiss_db.docstore._dict)}")

    faiss_db.save_local(DB_PATH)
    print(f"FAISS index saved to {DB_PATH}")

def test():

    embeddings = HuggingFaceEmbeddings(model_name='intfloat/multilingual-e5-large')
    loaded_faiss_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    print(f"Loaded FAISS index with {len(loaded_faiss_db.docstore._dict)} documents.")

    query = "How would you differentiate between symptoms of kennel cough and canine distemper?"
    docs = loaded_faiss_db.similarity_search(query, k=3)
    print("\nSimilarity search results:")
    for doc in docs:
        print(f"Content: {doc.page_content}...")
        print(f"Metadata: {doc.metadata}\n")

if __name__ == '__main__':
    
    main('data/msdvetmanual_dog_owners_data.json')