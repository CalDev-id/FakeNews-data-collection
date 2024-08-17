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
    
    def get_driver(self):
        driver = getattr(self.thread_local, 'driver', None)
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('user-data-dir=C:/Users/haica/AppData/Local/Google/Chrome/User Data')
            driver = webdriver.Chrome( options=chrome_options)
            # edge_options = webdriver.EdgeOptions()
            # edge_options.add_argument('--log-level=1')
            # driver = webdriver.Edge(options = edge_options)
            setattr(self.thread_local, 'driver', driver)
            
        return driver
    
    def visit_content(self, target_url):
        try:
            driver_visit = self.get_driver()
            driver_visit.implicitly_wait(20)  # Increased wait time
            driver_visit.set_page_load_timeout(60)  # Increased load timeout
            driver_visit.get(target_url)
            time.sleep(10)
            
            page_content = trafilatura.bare_extraction(driver_visit.page_source)
            
            title = page_content["title"]
            author = page_content["author"]
            date = page_content["date"]
            url = page_content["url"]
            article = page_content["text"] if page_content["text"] else page_content["raw_text"]
            
            search_content = {
                "title": title,
                "date": date,
                "author": author,
                "url": url,
                "article": article,
            }
                
            return search_content
        except Exception as e:
            print(f"Error visiting content: {e}")
            return False
    
    def fetch_search_result(self, url, page, query="no_name"):
        driver = self.get_driver()
        driver.implicitly_wait(10)
        driver.get(url)
        
        all_datasets = []
        
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        search_lists = page_content.find_all("div", attrs={"class": 'MjjYud'})
        search_lists = search_lists[:self.num_item_per_page]
        for i_cnt, cnt in enumerate(tqdm(search_lists, desc="Processing search results")):
            try:
                title = cnt.find_all("h3", attrs={"class": 'DKV0Md'})
                if len(title) > 0:
                    title = title[0].text
                    root_url = cnt.find("cite").text.split(" › ")[0]
                    source_url = cnt.find_all("a", attrs={"jsname": "UWckNb"})[0]["href"]
                    print(source_url)
                    if source_url.endswith(".pdf"):
                        continue
                    
                    search_content_result = self.visit_content(source_url)
                    if not search_content_result:
                        continue
                    
                    all_datasets.append(search_content_result)
            except Exception as e:
                print(f"Error processing search result: {e}")
                continue

        return all_datasets
    
    def search(self, query):
        datasets = []
        for i_p in range(self.num_pages):
            start_index = i_p * 10
            url = "https://www.google.com/search?"\
                  f"q={query}&"\
                  f"hl={self.lang}&"\
                  f"lr={self.lang}&"\
                  f"start={start_index}"
            page_data = self.fetch_search_result(url, i_p, query)
            datasets += page_data
        return datasets

def read_csv_and_search(file_path, lang, num_pages, num_item_per_page):
    data_collect = DataCollection(lang=lang, num_pages=num_pages, num_item_per_page=num_item_per_page)
    all_results = []

    with open(file_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in tqdm(reader, desc="Reading CSV rows"):
            Headline = row['Headline']  # Access the 'Headline' column
            results = data_collect.search(Headline)
            all_results.extend(results)

    with open(f"datasets/all_result_v3.json", "w") as json_w:
        json.dump(all_results, json_w, indent=4)

if __name__ == "__main__":
    csv_file_path = "../datasets/github500Berita.csv"
    read_csv_and_search(csv_file_path, lang="id", num_pages=1, num_item_per_page=1)
