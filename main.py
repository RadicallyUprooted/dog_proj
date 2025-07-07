import argparse
import asyncio
from scrapers.scraper import main as scrape_main
from vector_dbs.faiss_db import main as faiss_main
from services.agent import main as agent_main

def main():
    parser = argparse.ArgumentParser(description="Dog Disease Consultant")
    parser.add_argument('action', choices=['scrape', 'create_db', 'consult'], 
                        help="Action to perform: 'scrape' to fetch data, 'create_db' to build the vector database, 'consult' to start the agent.")

    args = parser.parse_args()

    if args.action == 'scrape':
        scrape_main()
    elif args.action == 'create_db':
        faiss_main('data/msdvetmanual_dog_owners_data.json')
    elif args.action == 'consult':
        agent_main()

if __name__ == "__main__":
    main()
