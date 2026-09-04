__version__ = (0, 0, 1)
#            ███████████  ██████████ █████       █████   ████   █████████  
#            ░███░░░░░███░░███░░░░░█░░███       ░░███   ███░   ███░░░░░███ 
#            ░███    ░███ ░███  █ ░  ░███        ░███  ███    ░███    ░███ 
#            ░██████████  ░██████    ░███        ░███████     ░███████████ 
#            ░███░░░░░███ ░███░░█    ░███        ░███░░███    ░███░░░░░███ 
#            ░███    ░███ ░███ ░   █ ░███      █ ░███ ░░███   ░███    ░███ 
#            ███████████  ██████████ ███████████ █████ ░░████ █████   █████
#            ░░░░░░░░░░░  ░░░░░░░░░░ ░░░░░░░░░░░ ░░░░░   ░░░░ ░░░░░   ░░░░░ 
#                                                                    
#                                                                    
#            ██████   ██████    ███████    ██████████    █████████ 
#            ░██████ ██████   ███░░░░░███  ░███░░░░███  ███░░░░░███
#            ░███░█████░███  ███     ░░███ ░███   ░░███░███    ░░░ 
#            ░███░░███ ░███ ░███      ░███ ░███    ░███░░█████████ 
#            ░███ ░░░  ░███ ░███      ░███ ░███    ░███ ░░░░░░░░███
#            ░███      ░███ ░░███     ███  ░███    ███  ███    ░███
#            █████     █████ ░░░███████░   ██████████  ░░█████████ 
#            ░░░░░     ░░░░░    ░░░░░░░    ░░░░░░░░░░    ░░░░░░░░░  
#       
#                                © Copyright 2024
#
#                             https://t.me/belka_mod
#
#                               ── 𝙱ᥱ᧘κᥲ | 𝙼𝙾𝙳𝚂 ──
#                          meta developer: @psycho_belka

from ... import loader, utils
import random

@loader.tds
class RollModule(loader.Module):
    """Модуль для генерации случайного числа в заданном диапазоне."""

    strings = {
        "name": "/roll",
        "info_about_module": "Этот модуль позволяет генерировать случайные числа. Используйте команду: .roll <min>:<max>",
        "incorrect_format": "Пожалуйста, укажите диапазон в формате <min>:<max>.",
        "min_max_error": "Минимальное значение должно быть меньше максимального значения.",
        "value_error": "Пожалуйста, укажите корректные числовые значения в формате <min>-<max>."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "MT", "Вы выбросили {otv} ({diapos})",
            lambda: "Шаблон сообщения для вывода результата.\n\nИспользуй {diapos} для диапазона значений\nИпользуй {otv} для результата."
        )

    async def rollcmd(self, message):
        """Генерирует случайное число в указанном диапазоне min:max.\n\n💻 developer [@belka_mod]"""
        args = utils.get_args_raw(message)

        if '-' not in args:
            await utils.answer(message, self.strings["incorrect_format"])
            return

        try:
            min_val, max_val = map(int, args.split('-'))
            if min_val >= max_val:
                await utils.answer(message, self.strings["min_max_error"])
                return
        except ValueError:
            await utils.answer(message, self.strings["value_error"])
            return

        random_number = random.randint(min_val, max_val)
        
        # Формируем ответ с использованием шаблона из конфига
        result_message = self.config["MT"].format(diapos=f"{min_val}-{max_val}", otv=random_number)
        await utils.answer(message, result_message)


    async def setconf(self, message):
        """Позволяет изменять конфигурацию шаблона."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "Укажите новое значение для шаблона.")
            return

        self.config["MT"] = args
        await utils.answer(message, f"{self.strings['config_updated'].format(template=self.config['MT'])}")
