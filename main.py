from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from crawler import GoogleScholar

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage,
    ShowLoadingAnimationRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent
)

# 載入環境變數
load_dotenv()

# web application framework
app = Flask(__name__)

# 爬取資料
crawler = GoogleScholar(1)
crawler.build_browser()
message_text = crawler.search()

# setting line token
configuration = Configuration(access_token=os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))


@app.route("/search", methods=['POST'])
def search():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


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

        userText = event.message.text == "get"

        # 回覆相同訊息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=(message_text if userText else "Please input get."))]
            )
        )


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


if __name__ == "__main__":
    app.run(debug=True)
