import asyncio
import json
import uuid
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, NavigableString

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
]

async def scrape_msdvetmanual():
    """
    Scrapes text content from the 'Dog Owners' section of the MSD Vet Manual website.
    It navigates to main categories, then to their subsections, extracts text
    from each paragraph (excluding specific tags and the last paragraph),
    and saves it into a JSON file formatted for a vector database.
    """
    base_url = "https://www.msdvetmanual.com/dog-owners"
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=random.choice(user_agents))

        print(f"Navigating to base URL: {base_url}")

        await page.goto(base_url, wait_until="domcontentloaded")
        await page.screenshot(path="screenshot.png")
        
        all_links = await page.locator("a").all()
        main_category_links = []
        
        for link_element in all_links:
            href = await link_element.get_attribute("href")
            text = await link_element.text_content()
            
            if href and href.startswith("/dog-owners/") and href != "/dog-owners" and '#' not in href:
                path_segments = href.strip('/').split('/')
                if len(path_segments) == 2 and path_segments[0] == 'dog-owners':
                    full_url = f"https://www.msdvetmanual.com{href}"
                    main_category_links.append({"text": text.strip(), "url": full_url})
                print(href)
        # Use a dictionary to remove duplicate links based on their URL
        unique_main_category_links = {link['url']: link for link in main_category_links}.values()
        print(f"Found {len(unique_main_category_links)} potential main categories.")
        
        for main_cat_link_info in unique_main_category_links:
            main_category_name = main_cat_link_info["text"]
            main_category_url = main_cat_link_info["url"]

            print(f"\n--- Processing Main Category: {main_category_name} ({main_category_url}) ---")
            
            await page.goto(main_category_url, wait_until="domcontentloaded")
            
            all_links_on_category_page = await page.locator("a").all()
            subsection_links = []

            for link_element in all_links_on_category_page:
                href = await link_element.get_attribute("href")
                text = await link_element.text_content()

                main_category_path_segment = main_cat_link_info["url"].replace("https://www.msdvetmanual.com", "")
                if href and href.startswith(main_category_path_segment + '/') and '#' not in href:
                    path_segments = href.strip('/').split('/')
                    if len(path_segments) == 3 and path_segments[0] == 'dog-owners' and path_segments[1] == main_category_path_segment.strip('/').split('/')[-1]:
                        full_url = f"https://www.msdvetmanual.com{href}"
                        # Ensure we don't add the main category URL itself as a subsection
                        if full_url != main_category_url:
                            subsection_links.append({"text": text.strip(), "url": full_url})
            
            unique_subsection_links = {link['url']: link for link in subsection_links}.values()
            
            print(f"Found {len(unique_subsection_links)} potential subsections for '{main_category_name}'.")

            for sub_link_info in unique_subsection_links:
                subsection_name = sub_link_info["text"]
                subsection_url = sub_link_info["url"]

                print(f"--- Scraping Subsection: '{subsection_name}' ({subsection_url}) ---")
                
                try:
                    await page.goto(subsection_url, wait_until="domcontentloaded")
                    
                    content_locator = page.locator("div.TopicMainContent_content__MEmoN").first
                    if content_locator:
                        html_content = await content_locator.inner_html()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Remove all <img> tags
                        for img_tag in soup.find_all('img'):
                            img_tag.decompose()
                        
                        # Remove all <h2> tags
                        for h2_tag in soup.find_all('h2'):
                            h2_tag.decompose()

                        # Remove all <h3> tags
                        for h3_tag in soup.find_all('h3'):
                            h3_tag.decompose()

                        # Remove table containers
                        for table_wrapper in soup.find_all('table'):
                            table_wrapper.decompose()

                        # Find all paragraph tags
                        all_paragraphs = soup.find_all('p')
                        paragraphs_to_process = []

                        if all_paragraphs:
                            # Check the last paragraph
                            last_paragraph = all_paragraphs[-1]
                            # Remove <a> tags within the last paragraph for accurate text check
                            for a_tag in last_paragraph.find_all('a'):
                                a_tag.replace_with(NavigableString(a_tag.get_text()))
                            
                            last_paragraph_text = last_paragraph.get_text().strip()

                            if "Also see" in last_paragraph_text:
                                paragraphs_to_process = all_paragraphs[:-1] # Exclude the last paragraph
                                print(f"  - Last paragraph ignored for '{subsection_name}' (contains 'Also see').")
                            else:
                                paragraphs_to_process = all_paragraphs # Include all paragraphs
                                print(f"  - Last paragraph included for '{subsection_name}' (does not contain 'Also see').")
                        else:
                            print(f"  - No paragraphs found for '{subsection_name}'.")
                        
                        for p_tag in paragraphs_to_process:
                            # Remove <a> tags but keep their text content
                            for a_tag in p_tag.find_all('a'):
                                # Replace the <a> tag with its text content
                                a_tag.replace_with(NavigableString(a_tag.get_text()))

                            paragraph_text = p_tag.get_text()
                            cleaned_paragraph_text = ' '.join(paragraph_text.split()).strip()
                            
                            if cleaned_paragraph_text:
                                scraped_data.append({
                                    "id": str(uuid.uuid4()), # Unique ID for each text chunk
                                    "url": subsection_url,
                                    "chapter": main_category_name,
                                    "topic": subsection_name,
                                    "text": cleaned_paragraph_text
                                })
                        print(f"Successfully scraped '{subsection_name}'. Added {len(paragraphs_to_process)} paragraphs.")
                    else:
                        print(f"WARNING: Could not find main content element for '{subsection_name}' at {subsection_url}. Skipping.")

                except Exception as e:
                    print(f"ERROR: Failed to scrape '{subsection_url}': {e}")
                
        await browser.close()

    output_filename = "msdvetmanual_dog_owners_data_new.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraping complete. Data saved to {output_filename}")
    print(f"Total entries scraped: {len(scraped_data)}")

asyncio.run(scrape_msdvetmanual())
