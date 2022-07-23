import math
from io import BytesIO
from typing import List, Union
from nonebot.params import Depends
from nonebot.utils import run_sync
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot import require, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
    MessageEvent,
    GroupMessageEvent,
)
from configs.path_config import DATA_PATH

require("nonebot_plugin_imageutils")
from nonebot_plugin_imageutils import BuildImage, Text2Image

from .utils import Meme
from .data_source import memes
from .depends import split_msg, regex
from .manager import meme_manager, ActionResult, MemeMode

__zx_plugin_name__ = "头像表情包"
__plugin_usage__ = """
usage：
    触发方式：指令 + @user/qq/自己/图片
    发送“头像表情包”查看支持的指令
    指令：
        摸 @任何人
        摸 qq号
        摸 自己
        摸 [图片]
""".strip()
__plugin_des__ = "生成各种表情"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["头像表情包", "头像相关表情包", "头像相关表情制作"]
__plugin_version__ = 0.5
__plugin_author__ = "MeetWq"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    'cmd': __plugin_cmd__
}
__plugin_resources__ = {
    "images": DATA_PATH / "petpet",
    "fonts": DATA_PATH / "petpet"}

help_cmd = on_command("头像表情包", aliases={"头像相关表情包", "头像相关表情制作"}, block=True, priority=5)


@run_sync
def help_image(user_id: str, memes: List[Meme]) -> BytesIO:
    def cmd_text(memes: List[Meme], start: int = 1) -> str:
        texts = []
        for i, meme in enumerate(memes):
            text = f"{i + start}. " + "/".join(meme.keywords)
            if not meme_manager.check(user_id, meme):
                text = f"[color=lightgrey]{text}[/color]"
            texts.append(text)
        return "\n".join(texts)

    text1 = "摸头等头像相关表情制作\n触发方式：指令 + @某人 / qq号 / 自己 / [图片]\n支持的指令："
    idx = math.ceil(len(memes) / 2)
    text2 = cmd_text(memes[:idx])
    text3 = cmd_text(memes[idx:], start=idx + 1)
    img1 = Text2Image.from_text(text1, 30, weight="bold").to_image(padding=(20, 10))
    img2 = Text2Image.from_bbcode_text(text2, 30).to_image(padding=(20, 10))
    img3 = Text2Image.from_bbcode_text(text3, 30).to_image(padding=(20, 10))
    w = max(img1.width, img2.width + img3.width)
    h = img1.height + max(img2.height, img2.height)
    img = BuildImage.new("RGBA", (w, h), "white")
    img.paste(img1, alpha=True)
    img.paste(img2, (0, img1.height), alpha=True)
    img.paste(img3, (img2.width, img1.height), alpha=True)
    return img.save_jpg()


def get_user_id():
    def dependency(event: MessageEvent) -> str:
        return (
            f"group_{event.group_id}"
            if isinstance(event, GroupMessageEvent)
            else f"private_{event.user_id}"
        )

    return Depends(dependency)


@help_cmd.handle()
async def _(user_id: str = get_user_id()):
    img = await help_image(user_id, memes)
    if img:
        await help_cmd.finish(MessageSegment.image(img))


def create_matchers():
    def handler(meme: Meme) -> T_Handler:
        async def handle(
                matcher: Matcher,
                res: Union[str, BytesIO] = Depends(meme.func),
        ):
            matcher.stop_propagation()
            if isinstance(res, str):
                await matcher.finish(res)
            await matcher.finish(MessageSegment.image(res))

        return handle

    for meme in memes:
        on_message(
            regex(meme.pattern),
            block=False,
            priority=5,
        ).append_handler(handler(meme), parameterless=[split_msg()])


create_matchers()
