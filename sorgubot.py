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

API_BASE = "https://arastir.vip/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict):
    url = f"{API_BASE}/{endpoint}.php"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                status = resp.status
                try:
                    data = await resp.json(content_type=None)
                    return data, status
                except:
                    return {"success": False, "message": "Veri okunamadı"}, status
    except:
        return None, 500


def hata_mesaji(status: int, message=None):
    errors = {
        403: "❌ Erişim engellendi.",
        404: "❌ Kayıt bulunamadı.",
        429: "❌ Çok fazla istek gönderdin.",
        500: "❌ Sunucu hatası."
    }
    return errors.get(status, f"❌ HATA {status}: {message or 'Bilinmeyen hata'}")


# ===================== DİNAMİK EMBED =====================
def create_dynamic_embed(title: str, data: dict):
    embed = discord.Embed(title=title, color=discord.Color.gold())
    for key, value in data.items():
        if key.lower() in ["success", "message", "status", "data"]:
            continue
        if isinstance(value, (dict, list)):
            value = str(value)[:500]
        embed.add_field(
            name=key.replace("_", " ").upper(), 
            value=f"`{value if value else '-'}`", 
            inline=True
        )
    embed.set_footer(text="made by -santes")
    return embed


# ===================== MODALLAR =====================
class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("tc", {"tc": self.tc.value})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ TC Sorgu Sonucu", data), ephemeral=True)


class AdSoyadModal(discord.ui.Modal, title="Ad Soyad Sorgulama"):
    ad = discord.ui.TextInput(label="Ad", placeholder="Ad giriniz", required=True)
    soyad = discord.ui.TextInput(label="Soyad", placeholder="Soyad giriniz", required=True)
    il = discord.ui.TextInput(label="İl (Opsiyonel)", required=False)
    ilce = discord.ui.TextInput(label="İlçe (Opsiyonel)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        params = {"adi": self.ad.value, "soyadi": self.soyad.value}
        if self.il.value: params["il"] = self.il.value
        if self.ilce.value: params["ilce"] = self.ilce.value
        data, status = await api_get("adsoyad", params)
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        
        kayitlar = data.get("data", [])[:10]
        embed = discord.Embed(title="✅ Ad Soyad Sonuçları", color=discord.Color.gold())
        for i, k in enumerate(kayitlar, 1):
            field_value = "\n".join([f"**{key.replace('_',' ').upper()}:** `{val}`" for key,val in k.items() if val])
            embed.add_field(name=f"{i}. {k.get('ADI','-')} {k.get('SOYADI','-')}", value=field_value or "Veri yok", inline=False)
        embed.set_footer(text="made by -santes")
        await interaction.followup.send(embed=embed, ephemeral=True)


class TcGsmModal(discord.ui.Modal, title="TC → GSM"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("tcgsm", {"tc": self.tc.value})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ TC → GSM Sonucu", data), ephemeral=True)


class GsmTcModal(discord.ui.Modal, title="GSM → TC"):
    gsm = discord.ui.TextInput(label="GSM Numarası", placeholder="5551234567")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        data, status = await api_get("gsmtc", {"gsm": gsm})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ GSM → TC Sonucu", data), ephemeral=True)


class IsyeriModal(discord.ui.Modal, title="İşyeri Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("isyeri", {"tc": self.tc.value})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ İşyeri Sorgu Sonucu", data), ephemeral=True)


class AdresModal(discord.ui.Modal, title="Adres Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("adres", {"tc": self.tc.value})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ Adres Sorgu Sonucu", data), ephemeral=True)


class SulaleModal(discord.ui.Modal, title="Sülale Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data, status = await api_get("sulale", {"tc": self.tc.value})
        if not data or status != 200 or data.get("success") not in [True, "true"]:
            return await interaction.followup.send(hata_mesaji(status, data.get("message") if data else None), ephemeral=True)
        await interaction.followup.send(embed=create_dynamic_embed("✅ Sülale Sorgu Sonucu", data), ephemeral=True)


# ===================== SLASH KOMUTLARI =====================
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

@bot.tree.command(name="isyeri", description="TC ile işyeri sorgula")
async def isyeri(interaction: discord.Interaction):
    await interaction.response.send_modal(IsyeriModal())

@bot.tree.command(name="adres", description="TC ile adres sorgula")
async def adres(interaction: discord.Interaction):
    await interaction.response.send_modal(AdresModal())

@bot.tree.command(name="sulale", description="TC ile sülale sorgula")
async def sulale(interaction: discord.Interaction):
    await interaction.response.send_modal(SulaleModal())

@bot.tree.command(name="yardim", description="Yardım menüsü")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="Komutlar", value="""
/tc
/adsoyad
/tcgsm
/gsmtc
/isyeri
/adres
/sulale
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
