import threading
import time
import json
import csv
from selenium import webdriver
from bs4 import BeautifulSoup
import trafilatura
from tqdm import tqdm

class DataCollection():
    def __init__(self, lang, num_pages, num_item_per_page):
        self.thread_local = threading.local()
        self.lang = lang
        self.num_pages = num_pages
        self.num_item_per_page = num_item_per_page
        self.id_counter = 838
    
    def get_driver(self):
        driver = getattr(self.thread_local, 'driver', None)
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('user-data-dir=C:/Users/haica/AppData/Local/Google/Chrome/User Data')
            driver = webdriver.Chrome(options=chrome_options)
            setattr(self.thread_local, 'driver', driver)
        return driver
    
    def visit_content(self, target_url):
        try:
            driver_visit = self.get_driver()
            driver_visit.implicitly_wait(10)
            driver_visit.set_page_load_timeout(30)
            driver_visit.get(target_url)
            time.sleep(10)
            
            page_content = trafilatura.bare_extraction(driver_visit.page_source)
            
            title = page_content.get("title", "")
            author = page_content.get("author", "unknown")
            date = page_content.get("date", "")
            article = page_content.get("text", "") if page_content.get("text", "") else page_content.get("raw_text", "")
            url = target_url
            
            return {
                "url": url,
                "title": title,
                "article": article,
                "date": date,
                "author": author
            }
        except Exception as e:
            print(f"Error visiting content: {e}")
            return None
    
    def fetch_search_result(self, url, query, label):
        driver = self.get_driver()
        driver.implicitly_wait(10)
        driver.get(url)
        
        results = []
        
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        search_lists = page_content.find_all("div", attrs={"class": 'MjjYud'})
        search_lists = search_lists[:self.num_item_per_page]
        
        for cnt in tqdm(search_lists, desc="Processing search results"):
            try:
                title_element = cnt.find("h3", attrs={"class": 'DKV0Md'})
                if title_element:
                    source_url = cnt.find("a", attrs={"jsname": "UWckNb"})["href"]
                    if source_url.endswith(".pdf"):
                        continue
                    
                    content = self.visit_content(source_url)
                    if content:
                        if len(results) < self.num_item_per_page:
                            results.append(content)
            except Exception as e:
                print(f"Error processing search result: {e}")
                continue

        return {
            "id": f"mendaley_{self.id_counter}",
            "query": query,
            "claim": query,
            "label": label,
            "evidence": results
        }
    
    def search(self, query, label):
        all_results = []
        for i_p in range(self.num_pages):
            start_index = i_p * 10
            url = "https://www.google.com/search?"\
                  f"q={query}&"\
                  f"hl={self.lang}&"\
                  f"lr={self.lang}&"\
                  f"start={start_index}"
            page_results = self.fetch_search_result(url, query, label)
            all_results.append(page_results)
            self.id_counter += 1
        return all_results

def read_csv_and_search(file_path, lang, num_pages, num_item_per_page):
    data_collect = DataCollection(lang=lang, num_pages=num_pages, num_item_per_page=num_item_per_page)
    all_results = []

    with open(file_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in tqdm(reader, desc="Reading CSV rows"):
            headline = row['Headline']  # Access the 'Headline' column
            label = row['Label']  # Access the 'Label' column
            results = data_collect.search(headline, label)
            all_results.extend(results)

    with open("datasets/tbh/tbh_result_v4.json", "w") as json_w:
        json.dump(all_results, json_w, indent=4)

if __name__ == "__main__":
    csv_file_path = "../datasets/tbh/tbh_part_4.csv"
    read_csv_and_search(csv_file_path, lang="id", num_pages=1, num_item_per_page=10)
