import os
from rich_menu import RichMenu
from dotenv import load_dotenv
from crawler import GoogleScholar
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler,
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,

    PostbackAction,
    MessageAction,

    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    PushMessageRequest,
    RichMenuRequest,
    CreateRichMenuAliasRequest,
    RichMenuSize,
    RichMenuArea,
    RichMenuBounds,
    RichMenuResponse,


    TextMessage,
    StickerMessage,
    TemplateMessage,

    ButtonsTemplate,
)
from linebot.v3.webhooks import (
    MessageEvent,
    PostbackEvent,

    TextMessageContent,
    StickerMessageContent,
    PostbackContent
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

# create rich menu
RichMenuRequestObj = RichMenuRequest(
    size=RichMenuSize(
        width=800,
        height=540
    ),
    selected=False,
    name="New Rich Menu",
    chatBarText="圖文選單",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(
                x=0,
                y=0,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="A"
            )
        ),  # A
        RichMenuArea(
            bounds=RichMenuBounds(
                x=267,
                y=0,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="B"
            )
        ),  # B
        RichMenuArea(
            bounds=RichMenuBounds(
                x=534,
                y=0,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="C"
            )
        ),  # C
        RichMenuArea(
            bounds=RichMenuBounds(
                x=0,
                y=271,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="D"
            )
        ),  # D
        RichMenuArea(
            bounds=RichMenuBounds(
                x=267,
                y=271,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="E"
            )
        ),  # E
        RichMenuArea(
            bounds=RichMenuBounds(
                x=534,
                y=271,
                width=266,
                height=270
            ),
            action=MessageAction(
                type='message',
                text="F"
            )
        )  # F
    ]

)
richMenuObj = RichMenu(configuration=configuration, richMenuRequest=RichMenuRequestObj)
richMenuObj.create('./images/richmenu_2.jpg')


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
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret.")
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

        if (event.message.text == "get"):
            msg = [TextMessage(text=message_text)]
        else:
            # 按按鈕發生回發事件
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
                messages=[StickerMessage(
                    stickerId=event.message.sticker_id, packageId=event.message.package_id)]
            )
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 顯示輸入動畫
        line_bot_api.show_loading_animation_with_http_info(
            ShowLoadingAnimationRequest(
                chatId=event.source.user_id,
                loadingSeconds=5
            )
        )

        # 回覆訊息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(
                    text="reply post Back Message in postback fuc"+f"{event.postback.data}")]
            )
        )

        # line_bot_api.push_message_with_http_info(
        #     PushMessageRequest(
        #         to=event.source.user_id,
        #         messages=[TextMessage(text=" push post Back Message in postback fuc"+f"{event.postback.data}")]
        #     )
        # )


if __name__ == "__main__":
    app.run(debug=True)
