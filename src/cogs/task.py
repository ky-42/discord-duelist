"""Contains task cog, which is used to run repeated tasks"""

from discord.ext import commands, tasks

from bot import Bot
from game_handling.game_module_loading import GameModuleLoading


class Task(commands.Cog):
    """Uses the tasks extension of discord.py to run repeated tasks"""

    def __init__(self) -> None:
        super().__init__()

    @tasks.loop(minutes=15)
    async def clear_old_loaded_games():
        """Clears old loaded games from memory"""

        GameModuleLoading.clear_old_games_modules()


async def setup(bot: Bot) -> None:
    await bot.add_cog(Task())
