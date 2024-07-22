import threading
import time
import json

from os import sys
from selenium import webdriver
from bs4 import BeautifulSoup
from tqdm import tqdm
import trafilatura

class DataCollection():
    def __init__(self, lang, num_pages, num_item_per_page):
        self.thread_local = threading.local()
        self.lang = lang
        self.num_pages = num_pages
        self.num_item_per_page = num_item_per_page
    
    def get_driver(self):
        driver = getattr(self.thread_local, 'driver', None)
        # Cek browser sudah run atau belum
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--log-level=1')
            driver = webdriver.Chrome(options = chrome_options)
            
            # firefox_options = webdriver.FirefoxOptions()
            # chrome_options.add_argument('--headless=new')
            # driver = webdriver.Firefox(options = chrome_options)

            # chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument('--headless=new')
            # driver = webdriver.Edge(options = chrome_options)

            setattr(self.thread_local, 'driver', driver)

        return driver

    def visit_content(self, target_url):
        try:
            driver_visit = self.get_driver()
            # driver_visit.implicitly_wait(10)
            driver_visit.set_page_load_timeout(30)
            driver_visit.get(target_url)
            time.sleep(10)

            page_content = trafilatura.bare_extraction(driver_visit.page_source)
            print(type(page_content))
            print(page_content.keys())
            # print(page_content["title"])
            # print("="*50)
            # print(page_content["raw_text"])

            title = page_content["title"]
            author = page_content["author"]
            date = page_content["date"]
            url = page_content["url"]
            if page_content["text"] == "" and page_content["text"] != None:
                article = page_content["title"]
            else:
                article = page_content["raw_text"]
            
            search_content = {
                "title": title,
                "author": author,
                "date": date,
                "url": url,
                "article": article,
            }

            return search_content

            print (article)
            sys.exit()
        except:
            return False
    
    def fetch_search_result(self, url, query = "no_name"):
        driver = self.get_driver()
        driver.implicitly_wait(15)
        driver.set_page_load_timeout (20)
        driver.get(url)
        time.sleep(5)

        all_datasets = []

        # Page content = Element HTML
        # page_content = driver.page_source
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        search_lists = page_content.find_all("div", attrs={"class": 'MjjYud'})
        search_lists = search_lists[:self.num_item_per_page]

        # print(page_content)

        for i_cnt, cnt in enumerate(tqdm(search_lists)):
            title = cnt.find_all("h3", attrs={"class": 'DKV0Md'})
            # print(title[0].text)

            # if num_item_per_page and i_cnt >= self.num_item_per_page:
            #     break

            if len(title) > 0:
                title = title[0].text
                root_url = cnt.find("cite").text.split(" > ")[0]
                source_url = cnt.find_all("a", attrs={"jsname": 'UWckNb'})[0]["href"]
                # print(source_url)

                if source_url.endswith(".pdf"):
                    continue

                search_content_result = self.visit_content(source_url)
                
                if not search_content_result:
                    continue

                all_datasets.append(search_content_result)

                with open(f"datasets/{query}.json", "w") as json_w:
                    json.dump(all_datasets, json_w, indent = 4)
                
                # sys.exit()

            # break
    
    def search(self, query):
        for i_p in range(self.num_pages):
            start_index = i_p * 10
            url = "https://www.google.com/search?"\
            f"q={query}&"\
            f"hl={self.lang}&"\
            f"lr={self.lang}&"\
            f"start={start_index}"
            self.fetch_search_result(url, query)

if __name__ == "__main__":
    data_collect = DataCollection(lang="id", num_pages=10, num_item_per_page=5)
    data_collect.search("apa ibu kota negara indonesia")