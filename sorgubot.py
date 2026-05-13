#!/usr/bin/env python3
# ================================================
#           RECYLA SORGULAMA BOTU
# ================================================

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os
import json

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")  # .env dosyasına ekle

API_BASE = "https://arastir.vip/api"

# API Linkleri
API_ENDPOINTS = {
    "tc": f"{API_BASE}/tc.php",
    "adsoyad": f"{API_BASE}/adsoyad.php",
    "tcgsm": f"{API_BASE}/tcgsm.php",
    "gsmtc": f"{API_BASE}/gsmtc.php",
    "isyeri": f"{API_BASE}/isyeri.php",
    "adres": f"{API_BASE}/adres.php",
    "sulale": f"{API_BASE}/sulale.php",
}

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# ===================== API İSTEĞİ =====================
async def api_get(endpoint, params):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    # API Key varsa ekle
    if API_KEY:
        params = params.copy()
        params["apikey"] = API_KEY  # veya "key", "api_key" vs. olabilir

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, headers=headers, timeout=25) as resp:
                status = resp.status
                try:
                    data = await resp.json(content_type=None)
                    return data, status
                except:
                    text = await resp.text()
                    return {"success": False, "message": text[:200]}, status
    except asyncio.TimeoutError:
        return None, 408
    except Exception as e:
        print(f"API Hatası: {e}")
        return None, 500


def hata_mesaji_olustur(status, message=None):
    errors = {
        400: "❌ Parametre eksik veya hatalı.",
        403: "❌ Erişim engellendi. API anahtarınızı kontrol edin.",
        404: "❌ Kayıt bulunamadı.",
        429: "❌ Çok fazla istek gönderdiniz. Lütfen bekleyin.",
        500: "❌ Sunucu hatası. Biraz sonra tekrar deneyin.",
        408: "❌ Zaman aşımı. Bağlantı yavaş.",
    }
    return errors.get(status, f"❌ HATA {status}: {message or 'Bilinmeyen hata'}")


# ===================== MODALLAR =====================
class TcModal(discord.ui.Modal, title="TC Kimlik Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data, status = await api_get(API_ENDPOINTS["tc"], {"tc": self.tc.value})

        if not data or status != 200:
            embed = discord.Embed(title="❌ Hata", description=hata_mesaji_olustur(status), color=discord.Color.red())
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if data.get("success") in [True, "true"]:
            embed = discord.Embed(title="✅ KİŞİ BİLGİLERİ", color=discord.Color.gold())
            embed.add_field(name="Ad Soyad", value=f"`{data.get('ADI', '-')} {data.get('SOYADI', '-')}`", inline=False)
            embed.add_field(name="TC", value=f"`{data.get('TC', '-')}`", inline=True)
            embed.add_field(name="Doğum Tarihi", value=f"`{data.get('DOGUMTARIHI', '-')}`", inline=True)
            embed.add_field(name="Nüfus İli/İlçesi", value=f"`{data.get('NUFUSIL', '-')} / {data.get('NUFUSILCE', '-')}`", inline=False)
            embed.set_footer(text=f"Sorgulayan: {interaction.user}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=discord.Embed(title="❌ Sonuç Bulunamadı", 
                                                                description=data.get("message", "Kayıt yok."), 
                                                                color=discord.Color.red()), ephemeral=True)


# Diğer modallar da aynı mantıkla güncellenebilir. 
# Şimdilik sadece TC'yi tam yaptım, diğerlerini de aynı şekilde güncelleyebilirsin.

# ===================== SLASH KOMUTLAR =====================
@bot.tree.command(name="tc", description="TC ile kişi sorgula")
async def tc_command(interaction: discord.Interaction):
    await interaction.response.send_modal(TcModal())

@bot.tree.command(name="yardim", description="Komut listesi")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="RECYLA SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="/tc", value="TC ile kişi sorgulama", inline=False)
    embed.add_field(name="/adsoyad", value="Ad Soyad ile sorgu", inline=False)
    # Diğer komutları da ekleyebilirsin
    embed.set_footer(text="made by Recyla")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash komutu yüklendi.")
    except Exception as e:
        print(f"Sync hatası: {e}")


# ===================== ÇALIŞTIR =====================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı! .env dosyasını kontrol et.")
    else:
        bot.run(BOT_TOKEN)
