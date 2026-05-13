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

# User-Agent ve header'lar (403 hatasını aşmak için)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

# ===================== GELİŞMİŞ API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict):
    url = f"{API_BASE}/{endpoint}.php"
    print(f"🔍 İstek: {url} | Params: {params}")

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params, timeout=30) as resp:
                print(f"📡 Status Code: {resp.status}")
                
                if resp.status == 200:
                    try:
                        text = await resp.text()
                        print(f"📦 API Cevabı: {text[:200]}")
                        # JSON parse etmeyi dene
                        import json
                        data = json.loads(text)
                        return data
                    except Exception as e:
                        print(f"❌ JSON Hatası: {e}")
                        return None
                elif resp.status == 403:
                    print(f"⚠️ 403 Hatası: Cloudflare koruması")
                    return {"success": "false", "message": "API 403 hatası veriyor (Cloudflare koruması). API sahibine ulaşın."}
                else:
                    text = await resp.text()
                    print(f"❌ Hata İçeriği: {text[:200]}")
                    return None
    except asyncio.TimeoutError:
        print(f"❌ Zaman aşımı hatası")
        return None
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None

def hata_mesaji(hata=None):
    if hata:
        return f"❌ {hata}"
    return "❌ Kayıt bulunamadı veya bir hata oluştu."

def create_embed(title: str, data: dict):
    embed = discord.Embed(title=title, color=discord.Color.gold())
    
    # Hata kontrolü
    if data.get("success") == "false":
        embed = discord.Embed(title="HATA", description=data.get("message", "Bilinmeyen hata"), color=discord.Color.red())
        embed.set_footer(text="made by -santes")
        return embed
    
    # Eğer 'data' listesi varsa
    if isinstance(data.get("data"), list) and len(data["data"]) > 0:
        record = data["data"][0]
        for key, value in record.items():
            if value:
                embed.add_field(name=key.replace("_", " ").upper(), value=f"`{value}`", inline=True)
    else:
        # Normal veri gösterimi
        for key, value in data.items():
            if key.lower() in ["success", "message", "status", "data", "author"]:
                continue
            if value:
                embed.add_field(name=key.replace("_", " ").upper(), value=f"`{value}`", inline=True)
    
    if len(embed.fields) == 0:
        embed = discord.Embed(title="SONUÇ BULUNAMADI", description="Bu kriterlere uygun kayıt bulunamadı.", color=discord.Color.red())
    
    embed.set_footer(text="made by -santes")
    return embed

# ===================== MODALLAR =====================
class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tc", {"tc": self.tc.value})
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(embed=create_embed("TC Sorgu Sonucu", data), ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

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
        if data:
            if data.get("success") == "true" or data.get("data"):
                kayitlar = data.get("data", [])
                if len(kayitlar) == 0:
                    await interaction.followup.send(hata_mesaji("Kayıt bulunamadı."), ephemeral=True)
                    return
                
                embed = discord.Embed(title=f"Ad Soyad Sorgu Sonucu ({len(kayitlar)} kayıt)", color=discord.Color.gold())
                for i, k in enumerate(kayitlar[:10], 1):
                    embed.add_field(
                        name=f"{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}",
                        value=f"TC: {k.get('TC', '-')}\n{k.get('NUFUSIL', '-')}/{k.get('NUFUSILCE', '-')}",
                        inline=False
                    )
                if len(kayitlar) > 10:
                    embed.set_footer(text=f"Toplam {len(kayitlar)} kayıttan ilk 10'u gösteriliyor | made by -santes")
                else:
                    embed.set_footer(text="made by -santes")
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

class TcGsmModal(discord.ui.Modal, title="TC → GSM"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tcgsm", {"tc": self.tc.value})
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(embed=create_embed("TC → GSM Sonucu", data), ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

class GsmTcModal(discord.ui.Modal, title="GSM → TC"):
    gsm = discord.ui.TextInput(label="GSM Numarası", placeholder="5551234567")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        data = await api_get("gsmtc", {"gsm": gsm})
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(embed=create_embed("GSM → TC Sonucu", data), ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

class IsyeriModal(discord.ui.Modal, title="İşyeri Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("isyeri", {"tc": self.tc.value})
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(embed=create_embed("İşyeri Sorgu Sonucu", data), ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

class AdresModal(discord.ui.Modal, title="Adres Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("adres", {"tc": self.tc.value})
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(embed=create_embed("Adres Sorgu Sonucu", data), ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

class SulaleModal(discord.ui.Modal, title="Sülale Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", min_length=11, max_length=11)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("sulale", {"tc": self.tc.value})
        if data:
            if data.get("success") == "true" or data.get("data"):
                embed = discord.Embed(title="Sülale Ağacı", color=discord.Color.gold())
                embed.add_field(name="MERKEZ KİŞİ", value=f"```{data.get('ADI', '-')} {data.get('SOYADI', '-')}\nTC: {self.tc.value}```", inline=False)
                if data.get('ANNEADI'):
                    embed.add_field(name="ANNE", value=f"```{data.get('ANNEADI', '-')}\nTC: {data.get('ANNETC', '-')}```", inline=True)
                if data.get('BABAADI'):
                    embed.add_field(name="BABA", value=f"```{data.get('BABAADI', '-')}\nTC: {data.get('BABATC', '-')}```", inline=True)
                embed.set_footer(text="made by -santes")
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif data.get("success") == "false":
                await interaction.followup.send(hata_mesaji(data.get("message")), ephemeral=True)
            else:
                await interaction.followup.send(hata_mesaji(), ephemeral=True)
        else:
            await interaction.followup.send(hata_mesaji("API'ye bağlanılamadı."), ephemeral=True)

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
`/tc` - TC ile kişi sorgula
`/adsoyad` - Ad soyad ile sorgula
`/tcgsm` - TC'den GSM sorgula
`/gsmtc` - GSM'den TC sorgula
`/isyeri` - TC ile işyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sülale sorgula
""", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Prefix komutlar
@bot.command(name='yardim', aliases=['menu', 'help'])
async def yardim_prefix(ctx):
    embed = discord.Embed(title="SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="Komutlar", value="""
`/tc` - TC ile kişi sorgula
`/adsoyad` - Ad soyad ile sorgula
`/tcgsm` - TC'den GSM sorgula
`/gsmtc` - GSM'den TC sorgula
`/isyeri` - TC ile işyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sülale sorgula
""", inline=False)
    embed.set_footer(text="made by -santes")
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    print(f"🆔 Bot ID: {bot.user.id}")
    print("=" * 50)
    
    # Slash komutlarını sync et
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi!")
        for cmd in synced:
            print(f"   /{cmd.name}")
    except Exception as e:
        print(f"❌ Slash komut senkronizasyon hatası: {e}")
    
    print("=" * 50)
    
    activity = discord.Activity(type=discord.ActivityType.playing, name=".yardim | made by -santes")
    await bot.change_presence(activity=activity)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
    else:
        bot.run(BOT_TOKEN)
