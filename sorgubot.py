#!/usr/bin/env python3
# ================================================
#           SANTES SORGULAMA BOTU - RAILWAY
# ================================================

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_BASE = "https://arastir.vip/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict):
    url = f"{API_BASE}/{endpoint}.php"
    print(f"🔍 İstek: {url}?{ '&'.join([f'{k}={v}' for k,v in params.items()])}")  # Tam URL log

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                print(f"📡 Status: {resp.status}")
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                        print(f"📦 Cevap: {data}")
                        return data
                    except:
                        text = await resp.text()
                        print(f"Raw Cevap: {text[:400]}")
                        return None
                else:
                    text = await resp.text()
                    print(f"❌ Hata İçeriği: {text[:300]}")
                    return None
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None


def hata_mesaji():
    return "❌ Kayıt bulunamadı veya bir hata oluştu."


def create_embed(title: str, data: dict):
    embed = discord.Embed(title=title, color=discord.Color.gold())
    for key, value in data.items():
        if key.lower() in ["success", "message", "status", "data"]:
            continue
        embed.add_field(name=key.replace("_", " ").upper(), value=f"`{value if value else '-'}`", inline=True)
    embed.set_footer(text="made by -santes")
    return embed


# ===================== MODALLAR =====================
class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tc", {"tc": self.tc.value})
        if data and data.get("success") == "true":
            await interaction.followup.send(embed=create_embed("✅ TC Sorgu Sonucu", data), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji(), ephemeral=True)


class AdSoyadModal(discord.ui.Modal, title="Ad Soyad Sorgulama"):
    ad = discord.ui.TextInput(label="Ad", placeholder="Ad giriniz", required=True)
    soyad = discord.ui.TextInput(label="Soyad", placeholder="Soyad giriniz", required=True)
    il = discord.ui.TextInput(label="İl (Opsiyonel)", placeholder="İstanbul", required=False)
    ilce = discord.ui.TextInput(label="İlçe (Opsiyonel)", placeholder="Kadıköy", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        params = {"adi": self.ad.value, "soyadi": self.soyad.value}
        if self.il.value: params["il"] = self.il.value
        if self.ilce.value: params["ilce"] = self.ilce.value

        data = await api_get("adsoyad", params)
        if data and data.get("success") == "true":
            await interaction.followup.send(embed=create_embed("✅ Ad Soyad Sonucu", data), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji(), ephemeral=True)


class TcGsmModal(discord.ui.Modal, title="TC → GSM"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tcgsm", {"tc": self.tc.value})
        if data and data.get("success") == "true":
            await interaction.followup.send(embed=create_embed("✅ TC → GSM Sonucu", data), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji(), ephemeral=True)


class GsmTcModal(discord.ui.Modal, title="GSM → TC"):
    gsm = discord.ui.TextInput(label="GSM Numarası", placeholder="5551234567")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        data = await api_get("gsmtc", {"gsm": gsm})
        if data and data.get("success") == "true":
            await interaction.followup.send(embed=create_embed("✅ GSM → TC Sonucu", data), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji(), ephemeral=True)


# ===================== KOMUTLAR =====================
@bot.tree.command(name="tc", description="TC ile kişi sorgula")
async def tc(interaction: discord.Interaction):
    await interaction.response.send_modal(TcModal())

@bot.tree.command(name="adsoyad", description="Ad Soyad ile sorgu")
async def adsoyad(interaction: discord.Interaction):
    await interaction.response.send_modal(AdSoyadModal())

@bot.tree.command(name="tcgsm", description="TC'den GSM sorgula")
async def tcgsm(interaction: discord.Interaction):
    await interaction.response.send_modal(TcGsmModal())

@bot.tree.command(name="gsmtc", description="GSM'den TC sorgula")
async def gsmtc(interaction: discord.Interaction):
    await interaction.response.send_modal(GsmTcModal())

@bot.tree.command(name="yardim", description="Yardım menüsü")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="Komutlar", value="""
/tc
/adsoyad
/tcgsm
/gsmtc
""", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    activity = discord.Activity(type=discord.ActivityType.playing, name="SANTES IS COMING BACK")
    await bot.change_presence(activity=activity)


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
    else:
        bot.run(BOT_TOKEN)
