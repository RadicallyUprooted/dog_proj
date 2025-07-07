import os
import sys
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = "vector_dbs/vet_manual_faiss_db"
MODEL_NAME = 'gemini-1.5-flash'

def consult_the_expert(query, gemini_model, faiss_db):
    """
    Performs Retrieval-Augmented Generation to answer a user's query using Gemini.
    """
    results = faiss_db.similarity_search(query, k=3)

    if not results:
        retrieved_texts = "No relevant information found in the manual."
    else:
        retrieved_contents = [doc.page_content for doc in results]
        retrieved_texts = "\n\n---\n\n".join(retrieved_contents)

    prompt = f"""
        You are a helpful veterinary assistant providing information based on a veterinary manual.
        Use the following retrieved context to answer the user's question.

        CONTEXT:
        {retrieved_texts}

        USER'S QUESTION:
        {query}

        If the context contains related information, you may include it. 
        Otherwise, state that the information is not available in the manual.
        In any case, you can provide general advice that is suitable in the given situation.
        
        If the question is in English, answer in English.
        If the question is in Ukrainian, answer in Ukrainian.

        ANSWER:
    """

    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
                "top_p": 1,
                "top_k": 1,
            },
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini API: {e}."

def main():
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    if API_KEY is None:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        print("Please set it before running the script. Example: export GOOGLE_API_KEY='YOUR_API_KEY'")
        return

    try:
        genai.configure(api_key=API_KEY)
        print("Gemini API client configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API client: {e}")
        return

    gemini_model = genai.GenerativeModel(MODEL_NAME)

    try:
        embeddings = HuggingFaceEmbeddings(model_name='intfloat/multilingual-e5-large')
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return

    try:
        loaded_faiss_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"Successfully connected to FAISS.")
    except Exception as e:
        print(f"Error connecting to FAISS: {e}")
        print(f"Please ensure the database exists at '{DB_PATH}'.")
        return

    print("\nDog Disease Consultant is ready. Type 'exit' to quit.")
    while True:
        user_question = input("\nYour question: ")
        if user_question.lower() == 'exit':
            break
        
        answer = consult_the_expert(user_question, gemini_model, loaded_faiss_db)
        print(f"\nAssistant: {answer}")

if __name__ == "__main__":
    main()
