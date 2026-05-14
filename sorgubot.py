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
import random

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Yetkili rol ID (sadece bu rol /apiekle komutunu kullanabilir)
YETKILI_ROL_ID = 1479124710397579527

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# API Base (başlangıçta boş, /apiekle ile doldurulacak)
API_BASE = None

# ===================== ROL KONTROLÜ =====================
def has_permission(interaction: discord.Interaction) -> bool:
    """Kullanıcının yetkili role sahip olup olmadığını kontrol et"""
    role = discord.utils.get(interaction.user.roles, id=YETKILI_ROL_ID)
    return role is not None

# ===================== RANDOM HEADERS =====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict, retry_count=0):
    if not API_BASE:
        return {"success": "false", "message": "API adresi ayarlanmamış! /apiekle komutunu kullanın."}
    
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"{API_BASE}/{endpoint}?{param_string}"

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(headers=get_headers(), connector=connector) as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    try:
                        text = await resp.text()
                        if "<title>Just a moment..." in text or "Cloudflare" in text:
                            if retry_count < 2:
                                await asyncio.sleep(3)
                                return await api_get(endpoint, params, retry_count + 1)
                            return {"success": "false", "message": "Cloudflare koruması aşılamadı"}
                        
                        data = json.loads(text)
                        return data
                    except json.JSONDecodeError:
                        return None
                elif resp.status == 403:
                    text = await resp.text()
                    if "Just a moment..." in text:
                        if retry_count < 2:
                            await asyncio.sleep(5)
                            return await api_get(endpoint, params, retry_count + 1)
                    return {"success": "false", "message": "Erişim engellendi (Cloudflare)"}
                else:
                    return None
    except asyncio.TimeoutError:
        if retry_count < 2:
            await asyncio.sleep(2)
            return await api_get(endpoint, params, retry_count + 1)
        return None
    except Exception as e:
        return None

# ===================== MESAJ OLUŞTURMA =====================
def format_json_as_message(data):
    if not data:
        return "❌ Veri alınamadı."
    
    if isinstance(data, dict) and data.get("success") == "false":
        return f"❌ {data.get('message', 'Bir hata oluştu')}"
    
    message = "```json\n"
    message += json.dumps(data, indent=2, ensure_ascii=False)[:1900]
    message += "\n```"
    return message

def format_telefon_data(data):
    if not data or data.get("success") == "false":
        return f"❌ {data.get('message', 'Telefon bilgisi bulunamadı')}"
    
    telefonlar = []
    
    if "data" in data:
        telefon_listesi = data["data"]
        if isinstance(telefon_listesi, list):
            telefonlar = telefon_listesi
        elif isinstance(telefon_listesi, dict):
            telefonlar = [telefon_listesi]
    elif "telefon" in data:
        telefonlar = [{"telefon": data["telefon"]}]
    elif "gsm" in data:
        telefonlar = [{"telefon": data["gsm"]}]
    elif "tel" in data:
        telefonlar = [{"telefon": data["tel"]}]
    
    if not telefonlar:
        return "❌ Telefon bilgisi bulunamadı"
    
    mesaj = "**📞 TELEFON BİLGİLERİ**\n\n"
    for i, tel in enumerate(telefonlar[:10], 1):
        if isinstance(tel, dict):
            numara = tel.get("telefon") or tel.get("gsm") or tel.get("tel") or tel.get("number") or "Bilinmiyor"
            operator = tel.get("operator") or tel.get("operatör") or ""
            mesaj += f"**{i}.** `{numara}`"
            if operator:
                mesaj += f" - {operator}"
            mesaj += "\n"
        elif isinstance(tel, str):
            mesaj += f"**{i}.** `{tel}`\n"
    
    if len(telefonlar) > 10:
        mesaj += f"\n*...ve {len(telefonlar)-10} kayıt daha*"
    
    return mesaj

# ===================== APİ EKLE KOMUTU (SADCE YETKİLİ ROL) =====================
class ApiEkleModal(discord.ui.Modal, title="API Adresi Ekle"):
    api_adres = discord.ui.TextInput(
        label="API Base URL",
        placeholder="https://arastir.vip/api",
        default="https://arastir.vip/api",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global API_BASE
        API_BASE = self.api_adres.value.rstrip('/')
        await interaction.response.send_message(f"✅ API adresi ayarlandı: `{API_BASE}`", ephemeral=True)

@bot.tree.command(name="apiekle", description="API adresini ayarla (Sadece yetkili rol)")
async def apiekle(interaction: discord.Interaction):
    """API adresini ayarla - Sadece yetkili rol kullanabilir"""
    if not has_permission(interaction):
        # Yetkisi yoksa sessizce işlem yapma, hiçbir şey gösterme
        return
    await interaction.response.send_modal(ApiEkleModal())

# ===================== MODALLAR (HERKES KULLANABİLİR) =====================

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
            if data.get("success") == "true" and data.get("data"):
                kayitlar = data.get("data", [])
                if len(kayitlar) == 0:
                    await interaction.followup.send("❌ Kayıt bulunamadı.", ephemeral=True)
                    return
                
                mesaj = f"**📋 AD SOYAD SORGULAMA SONUCU**\n"
                mesaj += f"**Aranan:** {self.ad.value} {self.soyad.value}"
                if self.il.value:
                    mesaj += f" - {self.il.value} {self.ilce.value}"
                mesaj += f"\n**Bulunan:** {len(kayitlar)} kayıt\n\n"
                
                for i, k in enumerate(kayitlar[:15], 1):
                    mesaj += f"**{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}**\n"
                    mesaj += f"├ TC: {k.get('TC', '-')}\n"
                    mesaj += f"├ Doğum: {k.get('DOGUMTARIHI', '-')}\n"
                    mesaj += f"├ Nüfus: {k.get('NUFUSIL', '-')}/{k.get('NUFUSILCE', '-')}\n"
                    mesaj += f"├ Anne: {k.get('ANNEADI', '-')}\n"
                    mesaj += f"└ Baba: {k.get('BABAADI', '-')}\n\n"
                
                if len(kayitlar) > 15:
                    mesaj += f"\n*...ve {len(kayitlar)-15} kayıt daha*"
                
                if len(mesaj) > 2000:
                    for i in range(0, len(mesaj), 1900):
                        await interaction.followup.send(mesaj[i:i+1900], ephemeral=True)
                else:
                    await interaction.followup.send(mesaj, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Kayıt bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

class TcGsmModal(discord.ui.Modal, title="TC'den GSM Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        data = await api_get("tel.php", {"tc": self.tc.value})
        
        if not data or data.get("success") == "false":
            endpoints = ["telefon.php", "gsm.php", "phone.php", "iletisim.php"]
            for endpoint in endpoints:
                data = await api_get(endpoint, {"tc": self.tc.value})
                if data and data.get("success") == "true":
                    break
        
        if data:
            if data.get("success") == "true":
                formatted_msg = format_telefon_data(data)
                await interaction.followup.send(formatted_msg, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {data.get('message', 'Telefon bilgisi bulunamadı')}", ephemeral=True)
        else:
            await interaction.followup.send("❌ API'ye bağlanılamadı.", ephemeral=True)

class GsmTcModal(discord.ui.Modal, title="GSM'den TC Sorgulama"):
    gsm = discord.ui.TextInput(label="GSM Numarası", placeholder="5551234567")
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        
        endpoints = ["gsmtc.php", "gsm.php", "gsm_tc.php", "telno.php", "no.php"]
        sonuc = None
        
        for endpoint in endpoints:
            data = await api_get(endpoint, {"gsm": gsm})
            if data and data.get("success") == "true":
                sonuc = data
                break
        
        if sonuc:
            await interaction.followup.send(format_json_as_message(sonuc), ephemeral=True)
        else:
            await interaction.followup.send("❌ GSM numarasına ait kayıt bulunamadı.", ephemeral=True)

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

# ===================== SLASH KOMUTLARI (HERKESE AÇIK) =====================
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
    embed = discord.Embed(title="📱 SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="🔧 Komutlar", value="""
`/tc` - TC ile kişi sorgula
`/adsoyad` - Ad soyad ile sorgula (il/ilçe opsiyonel)
`/tcgsm` - TC'den GSM/telefon sorgula
`/gsmtc` - GSM'den TC sorgula
`/isyeri` - TC ile işyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sülale sorgula
""", inline=False)
    if not API_BASE:
        embed.add_field(name="⚠️ Uyarı", value="API adresi ayarlanmamış! Yetkili birisi `/apiekle` komutunu kullanmalı.", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name='yardim', aliases=['menu', 'help'])
async def yardim_prefix(ctx):
    embed = discord.Embed(title="📱 SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="🔧 Komutlar", value="""
`/tc` - TC ile kişi sorgula
`/adsoyad` - Ad soyad ile sorgula
`/tcgsm` - TC'den GSM/telefon sorgula
`/gsmtc` - GSM'den TC sorgula
`/isyeri` - TC ile işyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sülale sorgula
""", inline=False)
    embed.set_footer(text="made by -santes")
    await ctx.send(embed=embed)

# ===================== BOT OLAYI =====================
@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🔐 Yetkili Rol ID: {YETKILI_ROL_ID}")
    print(f"📡 API Durumu: {'Ayarlanmış' if API_BASE else 'Ayarlanmamış (/apiekle ile ayarlayın)'}")
    print("=" * 50)
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"❌ Slash komut senkronizasyon hatası: {e}")
    
    await bot.change_presence(activity=discord.Game(name=".yardim | made by -santes"))

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
    else:
        bot.run(BOT_TOKEN)
