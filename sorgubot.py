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
import re
from io import BytesIO
from datetime import datetime

# ===================== AYARLAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_BASE = "https://arastir.vip/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# User-Agent listesi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

# ===================== TEMİZLEME FONKSİYONU =====================
def clean_api_message(text):
    """API'den gelen istenmeyen mesajları temizle"""
    if not text:
        return text
    
    # Temizlenecek kelimeler/listeler
    clean_patterns = [
        r'UMARIM BU APİYİ ÜCRETLİ ALMAMIŞSINDIR',
        r'UMARIM BU APIYI UCRETLI ALMAMISSINDIR',
        r'umarim bu apiye ucretli almamissindir',
        r'ÜCRETLİ ALMA',
        r'PARALI API',
        r'APIYİ SATIN ALMA',
        r'BEDAVA API',
        r'REKLAM',
        r'REKLAMLAR',
        r'Sponsor',
        r'SPONSOR'
    ]
    
    for pattern in clean_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

def clean_data_dict(data):
    """Dictionary içindeki istenmeyeyen mesajları temizle"""
    if not isinstance(data, dict):
        return data
    
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned_value = clean_api_message(value)
            if cleaned_value:  # Boş değilse ekle
                cleaned[key] = cleaned_value
        elif isinstance(value, dict):
            cleaned[key] = clean_data_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_data_dict(item) if isinstance(item, dict) else 
                           clean_api_message(item) if isinstance(item, str) else item 
                           for item in value]
        else:
            cleaned[key] = value
    
    return cleaned

# ===================== API İSTEĞİ =====================
async def api_get(endpoint: str, params: dict, retry_count=0):
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
                        # Veriyi temizle
                        cleaned_data = clean_data_dict(data)
                        return cleaned_data
                    except json.JSONDecodeError:
                        return None
                elif resp.status == 403:
                    return {"success": "false", "message": "Erişim engellendi"}
                else:
                    return None
    except Exception as e:
        return None

# ===================== TXT DOSYASI OLUŞTURMA =====================
def create_full_txt(data, query_type, query_value, raw_data):
    """Tüm datayı ve ham veriyi içeren txt oluştur"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Önce raw datayı temizle
    cleaned_raw = clean_data_dict(raw_data)
    
    content = []
    content.append("=" * 70)
    content.append("SANTES SORGULAMA SISTEMI - TUM VERILER")
    content.append("=" * 70)
    content.append(f"Sorgu Tarihi: {timestamp}")
    content.append(f"Sorgu Tipi: {query_type}")
    content.append(f"Sorgu Degeri: {query_value}")
    content.append("=" * 70)
    content.append("")
    
    # Formatli veri
    content.append("FORMATLI VERI")
    content.append("-" * 50)
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "data" and isinstance(value, (list, dict)):
                content.append(f"\n[ {key.upper()} ]")
                content.append(json.dumps(value, indent=2, ensure_ascii=False))
            elif value:  # Bos degilse yaz
                content.append(f"\n[ {key.upper()} ]: {value}")
    else:
        content.append(json.dumps(data, indent=2, ensure_ascii=False))
    
    content.append("")
    content.append("=" * 70)
    content.append("HAM JSON VERISI (RAW DATA)")
    content.append("-" * 50)
    content.append(json.dumps(cleaned_raw, indent=2, ensure_ascii=False))
    content.append("")
    content.append("=" * 70)
    content.append("made by -santes")
    
    return "\n".join(content)

# ===================== MESAJ OLUŞTURMA =====================
def format_json_as_message(data):
    if not data:
        return "**VERI ALINAMADI**"
    
    if isinstance(data, dict) and data.get("success") == "false":
        return f"**{data.get('message', 'Bir hata olustu')}**"
    
    # Veriyi temizle
    cleaned_data = clean_data_dict(data)
    
    message = "```json\n"
    message += json.dumps(cleaned_data, indent=2, ensure_ascii=False)[:1900]
    message += "\n```"
    return message

# ===================== MODALLAR =====================

class TcModal(discord.ui.Modal, title="TC Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tc.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
                txt_content = create_full_txt(data, "TC Sorgulama", self.tc.value, data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Kayit bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

class AdSoyadModal(discord.ui.Modal, title="Ad Soyad Sorgulama"):
    ad = discord.ui.TextInput(label="Ad", placeholder="Ad giriniz", required=True)
    soyad = discord.ui.TextInput(label="Soyad", placeholder="Soyad giriniz", required=True)
    il = discord.ui.TextInput(label="Il (Opsiyonel)", placeholder="Istanbul", required=False)
    ilce = discord.ui.TextInput(label="Ilce (Opsiyonel)", placeholder="Kadikoy", required=False)

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
                    await interaction.followup.send("**Kayit bulunamadi**", ephemeral=True)
                    return
                
                mesaj = f"**AD SOYAD SORGULAMA SONUCU**\n"
                mesaj += f"**Aranan:** {self.ad.value} {self.soyad.value}\n"
                mesaj += f"**Bulunan:** {len(kayitlar)} kayit\n\n"
                
                for i, k in enumerate(kayitlar[:5], 1):
                    mesaj += f"**{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}**\n"
                    mesaj += f"TC: {k.get('TC', '-')}\n"
                    mesaj += f"Dogum: {k.get('DOGUMTARIHI', '-')}\n"
                
                if len(kayitlar) > 5:
                    mesaj += f"\n**...tum kayitlar txt dosyasinda**"
                
                await interaction.followup.send(mesaj, ephemeral=True)
                
                txt_content = create_full_txt(data, "Ad Soyad Sorgulama", f"{self.ad.value} {self.soyad.value}", data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum kayitlari iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Kayit bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

class TcGsmModal(discord.ui.Modal, title="TC GSM Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("tel.php", {"tc": self.tc.value})
        
        if not data or data.get("success") == "false":
            endpoints = ["telefon.php", "gsm.php", "phone.php"]
            for endpoint in endpoints:
                data = await api_get(endpoint, {"tc": self.tc.value})
                if data and data.get("success") == "true":
                    break
        
        if data:
            if data.get("success") == "true":
                await interaction.followup.send(format_telefon_data(data), ephemeral=True)
                txt_content = create_full_txt(data, "TC GSM Sorgulama", self.tc.value, data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Telefon bilgisi bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

class GsmTcModal(discord.ui.Modal, title="GSM TC Sorgulama"):
    gsm = discord.ui.TextInput(label="GSM Numarasi", placeholder="5551234567")
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        
        endpoints = ["gsmtc.php", "gsm.php", "gsm_tc.php", "telno.php"]
        sonuc = None
        
        for endpoint in endpoints:
            data = await api_get(endpoint, {"gsm": gsm})
            if data and data.get("success") == "true":
                sonuc = data
                break
        
        if sonuc:
            await interaction.followup.send(format_json_as_message(sonuc), ephemeral=True)
            txt_content = create_full_txt(sonuc, "GSM TC Sorgulama", gsm, sonuc)
            file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
            await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
        else:
            await interaction.followup.send("**GSM numarasina ait kayit bulunamadi**", ephemeral=True)

class IsyeriModal(discord.ui.Modal, title="Isyeri Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("isyeri.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
                txt_content = create_full_txt(data, "Isyeri Sorgulama", self.tc.value, data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Kayit bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

class AdresModal(discord.ui.Modal, title="Adres Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("adres.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
                txt_content = create_full_txt(data, "Adres Sorgulama", self.tc.value, data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Kayit bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

class SulaleModal(discord.ui.Modal, title="Sulale Sorgulama"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="12345678901", min_length=11, max_length=11)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await api_get("sulale.php", {"tc": self.tc.value})
        
        if data:
            if data.get("success") == "true" or data.get("data"):
                await interaction.followup.send(format_json_as_message(data), ephemeral=True)
                txt_content = create_full_txt(data, "Sulale Sorgulama", self.tc.value, data)
                file = discord.File(BytesIO(txt_content.encode('utf-8')), filename="data.txt")
                await interaction.followup.send("**Tum verileri iceren dosya:**", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"**{data.get('message', 'Kayit bulunamadi')}**", ephemeral=True)
        else:
            await interaction.followup.send("**API'ye baglanilamadi**", ephemeral=True)

# ===================== TELEFON FORMAT =====================
def format_telefon_data(data):
    if not data or data.get("success") == "false":
        return f"**{data.get('message', 'Telefon bilgisi bulunamadi')}**"
    
    telefonlar = []
    if "data" in data:
        telefon_listesi = data["data"]
        if isinstance(telefon_listesi, list):
            telefonlar = telefon_listesi
    
    if not telefonlar:
        return "**Telefon bilgisi bulunamadi**"
    
    mesaj = "**TELEFON BILGILERI**\n\n"
    for i, tel in enumerate(telefonlar[:10], 1):
        if isinstance(tel, dict):
            numara = tel.get("telefon") or tel.get("gsm") or tel.get("tel") or "Bilinmiyor"
            mesaj += f"**{i}.** `{numara}`\n"
        elif isinstance(tel, str):
            mesaj += f"**{i}.** `{tel}`\n"
    
    if len(telefonlar) > 10:
        mesaj += f"\n**...ve {len(telefonlar)-10} kayit daha**"
    
    return mesaj

# ===================== KOMUTLAR =====================
@bot.tree.command(name="tc", description="TC ile kisi sorgula")
async def tc(interaction: discord.Interaction):
    await interaction.response.send_modal(TcModal())

@bot.tree.command(name="adsoyad", description="Ad Soyad ile sorgu")
async def adsoyad(interaction: discord.Interaction):
    await interaction.response.send_modal(AdSoyadModal())

@bot.tree.command(name="tcgsm", description="TC GSM sorgula")
async def tcgsm(interaction: discord.Interaction):
    await interaction.response.send_modal(TcGsmModal())

@bot.tree.command(name="gsmtc", description="GSM TC sorgula")
async def gsmtc(interaction: discord.Interaction):
    await interaction.response.send_modal(GsmTcModal())

@bot.tree.command(name="isyeri", description="TC ile isyeri sorgula")
async def isyeri(interaction: discord.Interaction):
    await interaction.response.send_modal(IsyeriModal())

@bot.tree.command(name="adres", description="TC ile adres sorgula")
async def adres(interaction: discord.Interaction):
    await interaction.response.send_modal(AdresModal())

@bot.tree.command(name="sulale", description="TC ile sulale sorgula")
async def sulale(interaction: discord.Interaction):
    await interaction.response.send_modal(SulaleModal())

@bot.tree.command(name="yardim", description="Yardim menusu")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="SANTES SORGULAMA BOTU", color=discord.Color.purple())
    embed.add_field(name="Komutlar", value="""
`/tc` - TC ile kisi sorgula (Tum veriler txt olarak gelir)
`/adsoyad` - Ad soyad ile sorgula (Tum veriler txt olarak gelir)
`/tcgsm` - TC GSM sorgula
`/gsmtc` - GSM TC sorgula
`/isyeri` - TC ile isyeri sorgula
`/adres` - TC ile adres sorgula
`/sulale` - TC ile sulale sorgula
""", inline=False)
    embed.add_field(name="Dosya", value="Tum sorgu sonuclari **data.txt** olarak indirilebilir.", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"{bot.user} olarak giris yapildi!")
    print(f"Bot ID: {bot.user.id}")
    print("=" * 50)
    
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"Hata: {e}")
    
    await bot.change_presence(activity=discord.Game(name=".yardim | made by -santes"))

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("BOT_TOKEN bulunamadi!")
    else:
        bot.run(BOT_TOKEN)
