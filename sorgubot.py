#!/usr/bin/env python3
# ================================================
#           SANTES SORGULAMA BOTU
# ================================================

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

API_BASE = "https://arastir.vip/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict):
    url = f"{API_BASE}/{endpoint}.php"
    headers = {"User-Agent": "Mozilla/5.0"}

    if API_KEY:
        params = params.copy()
        params.update({"apikey": API_KEY, "key": API_KEY, "api_key": API_KEY})

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=25) as resp:
                status = resp.status
                try:
                    data = await resp.json(content_type=None)
                    return data, status
                except:
                    return {"success": False, "message": "Parse hatası"}, status
    except:
        return None, 500


def hata_mesaji(status: int, message=None):
    errors = {
        403: "❌ Erişim engellendi. API anahtarını kontrol et.",
        404: "❌ Kayıt bulunamadı.",
        429: "❌ Çok fazla istek gönderdin.",
        500: "❌ Sunucu hatası.",
    }
    return errors.get(status, f"❌ HATA {status}: {message or 'Bilinmeyen hata'}")


# ===================== TC MODAL =====================
class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("tc", {"tc": self.tc.value})

        if not data or status != 200:
            return await interaction.followup.send(hata_mesaji(status), ephemeral=True)

        if data.get("success") in [True, "true"]:
            embed = discord.Embed(title="✅ Kişi Bilgileri", color=discord.Color.gold())
            embed.add_field(name="Ad Soyad", value=f"`{data.get('ADI', '-')} {data.get('SOYADI', '-')}`", inline=False)
            embed.add_field(name="TC", value=f"`{data.get('TC', '-')}`", inline=True)
            embed.add_field(name="Doğum Tarihi", value=f"`{data.get('DOGUMTARIHI', '-')}`", inline=True)
            embed.add_field(name="Nüfus", value=f"`{data.get('NUFUSIL', '-')} / {data.get('NUFUSILCE', '-')}`", inline=False)
            embed.add_field(name="Uyruk", value=f"`{data.get('UYRUK', 'TR')}`", inline=True)
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji(status, data.get("message")), ephemeral=True)


# ===================== AD SOYAD MODAL (İSTEDİĞİN GİBİ) =====================
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

        data, status = await api_get("adsoyad", params)

        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)

        kayitlar = data.get("data", [])[:12]

        embed = discord.Embed(
            title="✅ Ad Soyad Sorgu Sonuçları", 
            description=f"**Aranan:** {self.ad.value} {self.soyad.value}",
            color=discord.Color.gold()
        )

        for i, k in enumerate(kayitlar, 1):
            embed.add_field(
                name=f"{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}",
                value=f"**TC:** `{k.get('TC', '-')}`\n"
                      f"**Doğum Tarihi:** `{k.get('DOGUMTARIHI', '-')}`\n"
                      f"**Uyruk:** `{k.get('UYRUK', 'TR')}`\n"
                      f"**Nüfus:** `{k.get('NUFUSIL', '-')} / {k.get('NUFUSILCE', '-')}`",
                inline=False
            )

        embed.set_footer(text="made by -santes")
        await interaction.followup.send(embed=embed, ephemeral=True)


# ===================== SLASH KOMUTLARI =====================
@bot.tree.command(name="tc", description="TC ile kişi sorgula")
async def tc(interaction: discord.Interaction):
    await interaction.response.send_modal(TcModal())

@bot.tree.command(name="adsoyad", description="Ad Soyad ile sorgu")
async def adsoyad(interaction: discord.Interaction):
    await interaction.response.send_modal(AdSoyadModal())

@bot.tree.command(name="yardim", description="Yardım menüsü")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="Komutlar", value="""
/tc
/adsoyad
""", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    
    activity = discord.Activity(type=discord.ActivityType.playing, name="SANTES IS COMING BACK")
    await bot.change_presence(activity=activity)

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu yüklendi.")
    except Exception as e:
        print(f"Sync hatası: {e}")


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
    else:
        bot.run(BOT_TOKEN)
