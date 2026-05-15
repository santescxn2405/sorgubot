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
import json

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_BASE = "https://arastir.vip/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Connection": "keep-alive"
}

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict):
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"{API_BASE}/{endpoint}?{param_string}"
    
    print(f"🔍 İstek URL: {url}")

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=30) as resp:
                print(f"📡 Status Code: {resp.status}")
                
                if resp.status == 200:
                    try:
                        text = await resp.text()
                        data = json.loads(text)
                        print(f"✅ API Başarılı")
                        return data
                    except Exception as e:
                        print(f"❌ JSON Hatası: {e}")
                        return None
                else:
                    text = await resp.text()
                    print(f"❌ HTTP Hatası {resp.status}: {text[:200]}")
                    return None
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None

# ===================== MESAJ OLUŞTURMA =====================
def format_json_as_message(data):
    if not data:
        return "❌ Veri alınamadı."
    
    message = "```json\n"
    message += json.dumps(data, indent=2, ensure_ascii=False)[:1900]
    message += "\n```"
    return message

async def send_long_message(interaction, message, ephemeral=True):
    """Uzun mesajları parçalara bölerek gönder"""
    if len(message) <= 2000:
        await interaction.followup.send(message, ephemeral=ephemeral)
    else:
        parts = []
        current_part = ""
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 > 1900:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        if current_part:
            parts.append(current_part)
        
        for i, part in enumerate(parts):
            if i == 0:
                await interaction.followup.send(part, ephemeral=ephemeral)
            else:
                await interaction.followup.send(part, ephemeral=ephemeral)

# ===================== MODALLAR =====================

# 1. TC Sorgulama
class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tc.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 2. Ad Soyad Sorgulama (TÜM KAYITLAR - AYNI SENDEKİ GİBİ)
class AdSoyadModal(discord.ui.Modal, title="Ad Soyad Sorgulama"):
    ad = discord.ui.TextInput(label="Ad", placeholder="Ad giriniz", required=True)
    soyad = discord.ui.TextInput(label="Soyad", placeholder="Soyad giriniz", required=True)
    il = discord.ui.TextInput(label="İl (Opsiyonel)", placeholder="İstanbul", required=False)
    ilce = discord.ui.TextInput(label="İlçe (Opsiyonel)", placeholder="Kadıköy", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        params = {"adi": self.ad.value, "soyadi": self.soyad.value}
        if self.il.value:
            params["il"] = self.il.value
        if self.ilce.value:
            params["ilce"] = self.ilce.value
        
        data = await api_get("adsoyad.php", params)
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                kayitlar = data.get("data", [])
                if len(kayitlar) == 0:
                    await interaction.followup.send("❌ Kayıt bulunamadı.", ephemeral=True)
                    return
                
                baslik = f"**📋 AD SOYAD SORGULAMA SONUCU**\n"
                baslik += f"**Aranan:** {self.ad.value} {self.soyad.value}"
                if self.il.value:
                    baslik += f" - {self.il.value} {self.ilce.value}"
                baslik += f"\n**Bulunan:** {len(kayitlar)} kayıt\n\n"
                
                mesaj = baslik
                for i, k in enumerate(kayitlar, 1):
                    kayit_mesaji = f"**{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}**\n"
                    kayit_mesaji += f"├ TC: {k.get('TC', '-')}\n"
                    kayit_mesaji += f"├ Doğum: {k.get('DOGUMTARIHI', '-')}\n"
                    kayit_mesaji += f"├ Nüfus: {k.get('NUFUSIL', '-')}/{k.get('NUFUSILCE', '-')}\n"
                    kayit_mesaji += f"├ Anne: {k.get('ANNEADI', '-')} (TC: {k.get('ANNETC', '-')})\n"
                    kayit_mesaji += f"└ Baba: {k.get('BABAADI', '-')} (TC: {k.get('BABATC', '-')})\n\n"
                    
                    if len(mesaj) + len(kayit_mesaji) > 1900:
                        mesaj += "\n*made by -santes*"
                        await send_long_message(interaction, mesaj)
                        mesaj = baslik + f"\n*...devam ediyor*\n\n"
                    
                    mesaj += kayit_mesaji
                
                if mesaj != baslik:
                    mesaj += "\n*made by -santes*"
                    await send_long_message(interaction, mesaj)
                else:
                    await interaction.followup.send("❌ Kayıt bulunamadı.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 3. TC'den GSM - DOKÜMANTASYONA GÖRE tcgsm.php
class TcGsmModal(discord.ui.Modal, title="TC'den GSM Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tcgsm.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 4. GSM'den TC - DOKÜMANTASYONA GÖRE gsmtc.php
class GsmTcModal(discord.ui.Modal, title="GSM'den TC Sorgulama"):
    gsm = discord.ui.TextInput(label="GSM Numarası", placeholder="5551234567", min_length=10, max_length=10)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        data = await api_get("gsmtc.php", {"gsm": gsm})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 5. İşyeri Sorgulama
class IsyeriModal(discord.ui.Modal, title="İşyeri Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("isyeri.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 6. Adres Sorgulama
class AdresModal(discord.ui.Modal, title="Adres Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("adres.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

# 7. Sülale Sorgulama
class SulaleModal(discord.ui.Modal, title="Sülale Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("sulale.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

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
`/adsoyad` - Ad soyad ile sorgula (il/ilçe opsiyonel)
`/tcgsm` - TC'den GSM sorgula
`/gsmtc` - GSM'den TC sorgula
`/isyeri` - TC ile işyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sülale sorgula
""", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi!")
        for cmd in synced:
            print(f"   /{cmd.name}")
    except Exception as e:
        print(f"❌ Slash komut senkronizasyon hatası: {e}")
    
    print("=" * 50)
    await bot.change_presence(activity=discord.Game(name=".yardim | made by -santes"))

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
    else:
        bot.run(BOT_TOKEN)
