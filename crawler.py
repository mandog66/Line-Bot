import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By

# 載入環境變數
load_dotenv()


class GoogleScholar:
    def __init__(self, page: int = 1):
        self.url = os.environ.get("SEARCH_URL") + f"&start={(page - 1) * 10}"
        self.executable_path = os.environ.get("EXECUTABLE_PATH")

    # 網頁下載至瀏覽器
    def build_browser(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.service = webdriver.ChromeService(executable_path=self.executable_path)
        self.browser = webdriver.Chrome(service=self.service, options=self.options)
        self.browser.get(self.url)

    # 爬取資料
    def search(self) -> str:
        searchResult = ""

        self.articles = self.browser.find_elements(By.XPATH, "//div/h3[@class='gs_rt']/a")
        self.dates = self.browser.find_elements(By.XPATH, "//div[@class='gs_rs']/span[@class='gs_age']")
        self.authors = self.browser.find_elements(By.XPATH, "//div[@class='gs_a']")

        for i, article, author, date in zip(range(10), self.articles, self.authors, self.dates):
            title = article.text
            author_ = author.text
            web = article.get_attribute('href')
            cleanDate = date.text.split(" ")
            cleanDate = cleanDate[0] + " " + cleanDate[1]

            searchResult += (f"Title :  {title}\nAuthor : {author_}\nLink  :  {web}\nDays  :  {cleanDate}" +
                             ("" if i == 9 else "\n\n"))

        # 關閉網站
        self.browser.quit()

        return searchResult


if __name__ == "__main__":
    obj = GoogleScholar(1)
    obj.build_browser()
    print(obj.search())
