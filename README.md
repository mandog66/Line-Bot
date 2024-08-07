# Line-Bot

## 目標

* Line Bot能夠將爬蟲爬到的資料回應到使用者。
* 使用者可以在聊天室輸入關鍵字就能夠呼叫Line Bot執行程式。
* 聊天室介面是按鈕選單，利用另一個方式呼叫Line Bot執行程式。

## 說明

* ### 爬蟲(crawler.py)

  * 載入函式庫

    ```PYTHON
    import os
    from dotenv import load_dotenv
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    ```

  * 載入環境變數

    ```PYTHON
    load_dotenv()
    ```

  * 初始化

    ```PYTHON
    def __init__(self, page: int = 1):
        self.url = os.environ.get("SEARCH_URL") + f"&start={(page - 1) * 10}"
        self.executable_path = os.environ.get("EXECUTABLE_PATH")
    ```

  * 建立瀏覽器

    ```PYTHON
    def build_browser(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless') # 隱藏瀏覽器
        self.service = webdriver.ChromeService(executable_path=self.executable_path)
        self.browser = webdriver.Chrome(service=self.service, options=self.options)
        self.browser.get(self.url)
    ```

  * 爬取資料

    ```PYTHON
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
    ```

* ### Line Bot(main.py)

  * 載入函式庫

    ```PYTHON
    import os
    from flask import Flask, request, abort
    from dotenv import load_dotenv
    from crawler import GoogleScholar
    from linebot.v3 import WebhookHandler
    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.messaging import Configuration,ApiClient, MessagingApi, PostbackAction, ReplyMessageRequest, ShowLoadingAnimationRequest, PushMessageRequest, TextMessage, StickerMessage, TemplateMessage, ButtonsTemplate
    from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent, StickerMessageContent
    ```

  * 載入環境變數

    ```PYTHON
    load_dotenv()
    ```

  * 建立web應用框架

    ```PYTHON
    app = Flask(__name__)
    ```

  * 執行爬蟲

    ```PYTHON
    crawler = GoogleScholar(1)
    crawler.build_browser()
    message_text = crawler.search()
    ```

  * 建置Line Token

    ```PYTHON
    configuration = Configuration(access_token=os.environ.get("CHANNEL_ACCESS_TOKEN"))
    handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
    ```

  * 建置路由

    ```PYTHON
    @app.route("/search", methods=['POST'])
    def search():
        signature = request.headers['X-Line-Signature']

        body = request.get_data(as_text=True)
        app.logger.info(body)

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)
        return 'OK'
    ```

  * 加入文字事件

    ```PYTHON
    @handler.add(MessageEvent, message=TextMessageContent)  # text event
    def handle_message(event):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 顯示輸入動畫
            line_bot_api.show_loading_animation_with_http_info(
                ShowLoadingAnimationRequest(
                    chatId=event.source.user_id,
                    loadingSeconds=5
                )
            )

            if (event.message.text == "get"):
                msg = [TextMessage(text=message_text)]
            else:
                msg = [TemplateMessage(altText="ButtonsTemplate", template=ButtonsTemplate(
                    thumbnailImageUrl="https://images.pexels.com/photos/160755/kittens-cats-foster-playing-160755.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
                    text="PostBack",
                    actions=[PostbackAction(
                        label="PostBackButton Label",
                        data="Google Scholar",
                        displayText="Google Scholar"
                    )]
                ))]

            # 回覆訊息
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=msg
                )
            )
    ```

  * 加入貼圖事件

    ```PYTHON
    @handler.add(MessageEvent, message=StickerMessageContent)  # sticker event
    def handle_sticker(event):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 顯示輸入動畫
            line_bot_api.show_loading_animation_with_http_info(
                ShowLoadingAnimationRequest(
                    chatId=event.source.user_id,
                    loadingSeconds=5
                )
            )

            # 回覆相同貼圖(限官方貼圖)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[StickerMessage(stickerId=event.message.sticker_id, packageId=event.message.package_id)]
                )
            )
    ```

  * 加入回發事件

    ```PYTHON
    @handler.add(PostbackEvent)
    def handle_postback(event):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 回覆訊息
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text="reply post Back Message in postback fuc"+f"{event.postback.data}")]
                )
            )

            # line_bot_api.push_message_with_http_info(
            #     PushMessageRequest(
            #         to=event.source.user_id,
            #         messages=[TextMessage(text=" push post Back Message in postback fuc"+f"{event.postback.data}")]
            #     )
            # )
    ```

* ### Line 聊天室(rich_menu.py)

  * 載入函式庫

    ```PYTHON
    import os
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        MessagingApiBlob,
        RichMenuRequest,

        CreateRichMenuAliasRequest
    )
    ```

  * 初始化

    ```PYTHON
    def __init__(self, configuration: Configuration, richMenuRequest: RichMenuRequest):
        self.configuration = configuration
        self.richMenuRequest = richMenuRequest
    ```

  * 建置圖文選單

    ```PYTHON
    def create(self, image_path: str):
        extension = os.path.splitext(image_path)
        extension = 'image/jpeg' if extension == 'jpg' else 'image/png'
        with ApiClient(self.configuration)as api_client:
            self.line_bot_api = MessagingApi(api_client)
            self.line_blob_api = MessagingApiBlob(api_client)
            self.richMenuId = self.line_bot_api.create_rich_menu(
                rich_menu_request=self.richMenuRequest
            ).rich_menu_id

            with open(image_path, 'rb') as image:
                self.line_blob_api.set_rich_menu_image(
                    rich_menu_id=self.richMenuId,
                    body=bytearray(image.read()),
                    _headers={'Content-Type': extension}
                )

            self.line_bot_api.set_default_rich_menu(
                rich_menu_id=self.richMenuId
            )

            # 圖文選單分頁
            # self.line_bot_api.create_rich_menu_alias(
            #     CreateRichMenuAliasRequest(
            #         richMenuAliasId="test-rich-meun",
            #         richMenuId=self.richMenuId
            #     )
            # )

    ```

## 筆記

* ### 爬蟲

  * 為了讓環境變數方便更改，學到`dotenv`函式庫，可以將.env檔案(與主程式檔同層)的內容讀取出來。在需要使用環境變數的地方互叫下面的程式建立變數。

    ```PYTHON
    os.environ.get('Environment Variables')
    ```

  * `selenium`是一個開源的自動化測試工具，能夠簡單的測試web應用程式。

  * selenium 函式庫語法有一些改變，現在尋找元素必須要用 `By`類別來選擇要使用哪種方式找到網頁元素。

    ```PYTHON
    # 更改前
    browser.find_element_by_xpath('XPath Syntax')

    # 更改後
    from selenium.webdriver.common.by import By
    browser.find_elements(By.XPATH, 'XPath Syntax')
    ```

  * 如果瀏覽器需要增加參數可以增加下面的程式。

    ```PYTHON
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # 執行時不會跳出瀏覽器
    ```

* ### Line Bot

  * Flask
    * 這是一個web應用框架，可以協助開發web應用程式。
    * web應用框架是一個函式庫和模組的集合，可以在開發應用程式時不必在意太細節的網路協定。
    * 符合WSGI。WSGI(Web Server Gateway Interface)是一種`協定`，存在於web server 和 web應用程式之間，目的是只要web server 和 web應用程式符合WSGI就能夠有彈性地去開發，不會因為web server無法相容 web應用程式而打掉重練。

  * 設定路由
    * 藉著裝飾器(@ symbol)去改變函式行為。
    * `@app.route('/search')`就是透過裝飾器設定路由並執行下面的函式。
    * `logger.info(body)`能夠顯示log。這裡就是顯示出請求的結果。
    * `flask.abort()`能夠彈出HTTP例外，類似 Python 的 raise。

  * 文字事件
    * 這也有利用裝飾器，但這是增加一個功能，可以透過使用者輸入文字觸發。
    * `with as`可以銜接with後的實例並給定as後的變數。當with區塊執行結束會自動釋放實例。
    * 如果事件屬於文字事件(文字、貼圖、圖片...)，那add()的message參數就要增加`TextMessageContent類別`。
    * `TemplateMessage`是在聊天室顯示可互動視窗，有不同的方式互動。這裡我是用按鈕的方式去觸發事件。
    * 按鈕觸發事件後會執行回發行為。回發會把資料回傳給Line Bot而使用者是看不到後台回傳什麼，比較屬於收集資料進而了解使用者的行為並加以回應。

  * 貼圖事件
    * 基本上跟文字事件相同，只是message參數改為`StickerMessageContent`。貼圖也屬於文字事件的一種，所以才需要設定message參數。
    * 貼圖預設只能使用官方的貼圖。

  * 回發事件
    * 在按鈕事件有設定回發事件，當使用者按下按鈕後就會觸發這個事件。
    * 回發事件不屬於文字事件的一種，所以message不用設定。
    * 這裡只是簡單執行回覆文字，但reply和push有些差異。reply是跟使用者互動，當使用者做了某個事件，那reply能夠根據事件做出回應。push是Line Bot可以主動去執行事件，如果是文字事件，那就會發送訊息到使用者的聊天室。

* ### Webhook

  * 在Line Developers設定中可以開啟功能。
  * 這裡是透過Ngrok取得URL(Http端點)，一個可以讓外網連接本機指定的Port。
  * webhook扮演的腳色可以想像成讓使用者和Line Bot可以互相溝通，避免`輪巡`的方式造成伺服器的負擔。而輪巡是原本使用者和伺服器互動的方式。先由使用者發出請求，請求發送到伺服器，伺服器接收到請求後回應，回應再回傳給使用者。可想而知，要是一直發出請求伺服器會負荷不了。這時webhook就可以發揮作用，發生事件時伺服器主動回應給使用者。
  * 這裡的伺服器是由Flask建立。
  * Ngrok產生一個可以讓外網連接本機的URL，也可以說是一個可以接收webhook事件的伺服器入口。
  * 整個流程大概就是 : User發送訊息 <-> Line Platform <-> webhook <-> Server(Bot) ==> 當user發送訊息，Line Platform知道有訊息了，所以透過Ngrok產生的URL發送webhook事件給由Flask建立的Server，Server處理事件後回應給Line Platform，最終回覆User。

* ### Line 聊天室

  * 圖文選單格式可以在`RichMenuRequest`客製化。
    1. size : 顯示在聊天室的大小(可以看官方給的樣板RichMenu_DesignTemplate)
    2. selected : 預設是否開啟選單
    3. name : 後台能看到此選單的名字
    4. chatBarText : 在聊天室能看到收起/展開的按鈕名字
    5. areas : 關於按鈕的配置和行為(Bounds中x, y代表按鈕的左上角)

  * 建立兩個Api物件，分別是`MessagingApi`和`MessagingApiBlob`。差異是Blob(Binary Large Object)物件實際上是一個二進制物件，它能夠是任何形式的資料，包含文字、影片、圖片等，使這個檔案能夠被JavaScript利用。這裡創建的目的是使用本機的圖片當作圖文選單的背景圖案。
  * `set_rich_menu_image`參數列表中的`_headers`依照圖片副檔名分成`image/jepg`和`image/png`。
  * 如果有是有分頁類型的圖文選單，則必須要多設定`create_rich_menu_alias`區分不同的選單。

## 使用方法

* **Step 1.** 安裝套件

```BASH
pip install -r requirements.txt
```

* **Step 2.** 新增.env並新增環境變數
* **Step 3.** 在images/放入圖文選單的背景圖片
* **Step 4.** 可以在crawler.py更改搜尋路徑和搜尋元素
* **Step 5.** 如果需要Line 聊天室有分頁類型的圖文選單，可以在rich_menu.py更改程式
* **Step 6.** 在main.py中可以更改大部分動作。
  * `RichMenuRequestObj`可以更改圖文選單的大小和觸發事件
  * `richMenuObj.create('Your images')`變更背景圖片
  * `handle_message(event)`變更發生文字事件的回應
  * `handle_sticker(event)`變更發生貼圖事件的回應
  * `handle_postback(event)`變更發生回發事件的回應

## 參考資料

* ### 爬蟲

  * [dotenv](https://github.com/theskumar/python-dotenv)
  * [What is Selenium](https://www.simplilearn.com/tutorials/selenium-tutorial/what-is-selenium)
  * [Selenium docs](https://selenium-python.readthedocs.io/locating-elements.html#locating-elements)

* ### Line Bot

  * [Flask docs](https://flask.palletsprojects.com/en/3.0.x/)
  * [What is Falsk](https://pythonbasics.org/what-is-flask-python/)
  * [什麼是 WSGI](https://medium.com/@eric248655665/%E4%BB%80%E9%BA%BC%E6%98%AF-wsgi-%E7%82%BA%E4%BB%80%E9%BA%BC%E8%A6%81%E7%94%A8-wsgi-f0d5f3001652)
  * [STEAM 教育學習網](https://steam.oxxostudio.tw/category/python/example/line-reply-message.html)
  * [Line Messaging API](https://developers.line.biz/en/reference/messaging-api/)
  * [Python Logging docs](https://docs.python.org/3/library/logging.html#logging.Logger)
  * [Python with as](https://openhome.cc/zh-tw/python/exception/with-as/)
  * [Python @ Symbol](https://www.geeksforgeeks.org/what-is-the-symbol-in-python/)

* ### Webhook

  * [Ngrok](https://ngrok.com/docs/what-is-ngrok/)
  * [什麼是Webhook](https://medium.com/@justinlee_78563/line-bot-%E7%B3%BB%E5%88%97%E6%96%87-%E4%BB%80%E9%BA%BC%E6%98%AF-webhook-d0ab0bb192be)

* ### Line 聊天室

  * [Line official docs : Rich menu object](https://developers.line.biz/en/reference/messaging-api/#rich-menu-object)
  * [Line official docs : Upload rich menu image](https://developers.line.biz/en/reference/messaging-api/#upload-rich-menu-image)
  * [Blob](https://developer.mozilla.org/zh-TW/docs/Web/API/Blob)
  * [Blob 物件是什麼](https://wenku.csdn.net/answer/f197c2640c104bcfa220008e40c1653e?ydreferer=aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8%3D)
