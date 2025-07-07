import time
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import plotly.graph_objects as go
import io

class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ping_history = []
        self.ping_task.start()
    
    def cog_unload(self):
        self.ping_task.cancel()
    
    @tasks.loop(seconds=10)
    async def ping_task(self):
        now = datetime.datetime.utcnow()
        ping_ms = round(self.bot.latency * 1000, 2)
        self.ping_history.append((now, ping_ms))
        if len(self.ping_history) > 360:
            self.ping_history.pop(0)
    
    @ping_task.before_loop
    async def before_ping_task(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="ping", description="checks if bot is lagging or if the bot is down")
    @app_commands.default_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not self.ping_history:
            await interaction.followup.send("No ping data yet, try again in a few seconds.", ephemeral=True)
            return
        
        times = [t[0] for t in self.ping_history]
        pings = [t[1] for t in self.ping_history]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=times,
            y=pings,
            mode='lines+markers',
            line=dict(color='#1DB954', width=3),
            marker=dict(size=6, color='#1DB954'),
            name='Ping (ms)'
        ))

        fig.update_layout(
            title="Bot Ping Over Time",
            xaxis_title="Time (UTC)",
            yaxis_title="Ping (ms)",
            template="plotly_white",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif", size=14, color="#333"),
            hovermode="x unified",
            plot_bgcolor='white',
        )
        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='lightgrey',
            tickformat="%H:%M:%S",
            tickangle=45,
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgrey',
            zeroline=False,
        )

        img_bytes = fig.to_image(format="png", engine="kaleido")
        img_file = discord.File(io.BytesIO(img_bytes), filename="pinggraph.png")

        current_ping = round(self.bot.latency * 1000, 2)
        #timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        timestamp = f"<t:{int(time.time())}:F>"

        embed = discord.Embed(
            title="Bot Ping Over Time",
            description=f"Current ping: **{current_ping} ms**\nLast updated: {timestamp}",
            color=0x1DB954
        )
        embed.set_image(url="attachment://pinggraph.png")
        embed.set_footer(text="Data updated every 10 seconds")

        await interaction.followup.send(embed=embed, file=img_file)

async def setup(bot: commands.Bot):
    await bot.add_cog(PingCog(bot))
