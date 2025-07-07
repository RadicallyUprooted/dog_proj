# Dog Disease Consultant

This project is an AI-powered veterinary assistant that provides information about dog diseases and health issues. It uses a Retrieval-Augmented Generation (RAG) pipeline to answer user queries based on information scraped from the MSD Veterinary Manual.

## Project Structure

The project is organized into the following directories:

- **`data/`**: Contains the scraped data in JSON format.
- **`scrapers/`**: Includes the Python script for scraping data from the web.
- **`services/`**: Contains the main agent script for handling user queries.
- **`utils/`**: Stores utility functions and shared resources, including a script for keyword extraction.
- **`vector_dbs/`**: Houses the FAISS vector database and the script for its creation.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd dog_proj
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    
4. **Install Playwright dependencies:**
    ```bash
    playwright install
    ```

5.  **Set up your API key:**
    Export your Google API key as an environment variable.
    ```bash
    export GOOGLE_API_KEY='YOUR_API_KEY'
    ```

## Usage

The project has three main functionalities, which can be executed through `main.py`.

1.  **Scrape Data:**
    To scrape the MSD Veterinary Manual and create the data file, run:
    ```bash
    python3 main.py scrape
    ```
    This will create `msdvetmanual_dog_owners_data.json` in the `data/` directory.

2.  **Create the Vector Database:**
    After scraping the data, create the FAISS vector database:
    ```bash
    python3 main.py create_db
    ```
    This will create the `vet_manual_faiss_db` in the `vector_dbs/` directory.

3.  **Consult the Agent:**
    Once the database is created, you can start the consultation agent:
    ```bash
    python3 main.py consult
    ```
    The agent will prompt you to ask questions about dog health. Type `exit` to quit.

## Optional: Keyword Extraction

If you want to generate keywords for the scraped data, you can use the `keywords.py` script. This will add a "keywords" field to each entry in the JSON file, which can be useful for more advanced analysis or search.

To run the script:
```bash
python3 utils/keywords.py
```
This will create a new file, `msdvetmanual_dog_owners_data_with_keywords.json`, in the `data/` directory.
