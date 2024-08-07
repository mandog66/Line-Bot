import os
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,

    CreateRichMenuAliasRequest
)


class RichMenu:
    def __init__(self, configuration: Configuration, richMenuRequest: RichMenuRequest) -> None:
        self.configuration = configuration
        self.richMenuRequest = richMenuRequest

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
