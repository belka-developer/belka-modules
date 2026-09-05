# Name: deff
# meta developer: @mqone
# meta нахуй ты код смотришь?
# Commands:
# .deff 
# ---------------------------------------------------------------------------------

from .. import loader


@loader.tds
class deff(loader.Module):
    """Отправляет деффа"""

    strings = {"name": "deff men"}

    async def deffcmd(self, message):
        """Отправляет видео сообщение [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/9",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def nedoxcmd(self, message):
        """ Братан, только не докс [гс]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/10",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def mamacmd(self, message):
        """Бля, я твою маму выебу сука [гс]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/11",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def animecmd(self, message):
        """Э, анимешник баля [гс]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/12",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def alcmd(self, message):
        """Лежишь спокойно наверно да [гс]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/13",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def roscmd(self, message):
        """Трусы маме купи [гс]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/14",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def miyagicmd(self, message):
        """Песня мияги [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/15",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def lytocmd(self, message):
        """Лютая хуйня [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/16",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def repcmd(self, message):
        """Подкатил к продавщице [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/17",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return
     
    async def anticmd(self, message):
        """Не добавляйте меня в группы [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/19",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return
     
    async def huycmd(self, message):
        """Я хочу толстый хуй [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/20",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def xaxacmd(self, message):
        """xaxaxa [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/21",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def bustercmd(self, message):
        """завяжи глаза [кружок]"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/ajskalqpwoe/22",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return
     