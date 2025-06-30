import logging
from logging.handlers import RotatingFileHandler
from discord.ext import commands

from config import CONFIG
from core.services.issue_reporter import report_unhandled_exception
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.errors.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.tree.error(self.__dispatch_to_app_command_handler)
    
    async def __dispatch_to_app_command_handler(self, interaction, error):
        await self.on_app_command_error(interaction, error)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction, error):
        if interaction.command:
            logger.info(f"Slash command error in {interaction.command.name}: {error}")
            await report_unhandled_exception(interaction=interaction, error=error, source="slash_command")
        else:
            logger.info(f"Slash command error: {error}")
            await report_unhandled_exception(interaction=interaction, error=error, source="slash_command")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.interaction:
            logger.info(f"Slash command error in {ctx.interaction.command.name}: {error}")
            await report_unhandled_exception(interaction=ctx.interaction, error=error, source="slash_command")
        else:
            logger.info(f"Command error in {ctx.message.content}: {error}")
            await report_unhandled_exception(interaction=None, error=error, source="command")

    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        logger.info(f"Unhandled error in {event_method}: {args} {kwargs}")
        error_text = traceback.format_exc()
        await report_unhandled_exception(ctx=None, error=error_text, source=event_method)


async def setup(bot):
    if CONFIG.issues.github_repository is None:
        logger.warning("GitHub repository not configured, error reporting will be disabled.")
    elif CONFIG.issues.github_private_key_path is None:
        logger.warning("GitHub private key path not configured, error reporting will be disabled.")
    elif CONFIG.issues.github_app_id is None:
        logger.warning("GitHub App ID not configured, error reporting will be disabled.")
    elif CONFIG.issues.github_installation_id is None:
        logger.warning("GitHub Installation ID not configured, error reporting will be disabled.")
    else:
        await bot.add_cog(ErrorHandler(bot))
        import asyncio

        def handle_async_exception_sync(loop, context):
            asyncio.create_task(handle_async_exception(loop, context))
        
        async def handle_async_exception(loop, context):
            msg = context.get("exception", context["message"])
            logger.info(f"Unhandled asyncio exception: {msg}")
            await report_unhandled_exception(error=msg, source="asyncio loop exception")
            
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_async_exception_sync)
