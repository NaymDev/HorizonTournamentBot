import logging
from logging.handlers import RotatingFileHandler
import discord
from discord.ext import commands

from bot.core.services.issue_reporter import report_unhandled_exception

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.errors.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await report_unhandled_exception(interaction=interaction, error=error, source="slash_command")


    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        import traceback
        error_text = traceback.format_exc()
        await report_unhandled_exception(ctx=None, error=error_text, source=event_method)
