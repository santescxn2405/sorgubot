import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os
import json

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API Linkleri
API_TC = "https://arastir.vip/api/tc.php"
API_ADSOYAD = "https://arastir.vip/api/adsoyad.php"
API_TCGSM = "https://arastir.vip/api/tcgsm.php"
API_GSMTC = "https://arastir.vip/api/gsmtc.php"
API_ISYERI = "https://arastir.vip/api/isyeri.php"
API_ADRES = "https://arastir.vip/api/adres.php"
API_SULALE = "https://arastir.vip/api/sulale.php"

# Bot intentleri
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# API istegi gonderme (HTTP status kodlarini da dondur)
async def api_get(url, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                status = response.status
                try:
                    data = await response.json()
                    return data, status
                except:
                    return None, status
    except Exception as e:
        print(f"API baglanti hatasi: {e}")
        return None, 500

# Hata mesaji olusturma fonksiyonu
def hata_mesaji_olustur(status, message=None):
    if status == 400:
        return "HATA 400: Parametre eksik veya hatali. Lutfen girdiginiz bilgileri kontrol edin."
    elif status == 404:
        return "HATA 404: Kayit bulunamadi. Bu bilgilere ait bir kayit sistemde yok."
    elif status == 500:
        return "HATA 500: Veritabani baglantisi basarisiz. API sunucusunda sorun olabilir."
    elif status == 429:
        return "HATA 429: Cok fazla istek gonderildi. Lutfen bekleyip tekrar deneyin."
    elif status == 403:
        return "HATA 403: Erisim engellendi. API anahtariniz gecerli olmayabilir."
    elif message:
        return f"HATA {status}: {message}"
    else:
        return f"HATA {status}: Bilinmeyen bir hata olustu."

# ==================== MODAL SINIFLARI ====================

# 1. TC Sorgulama Modal
class TcModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="TC KIMLIK SORGULAMA")
        
        self.tc = discord.ui.TextInput(
            label="TC Kimlik Numarasi",
            placeholder="11 haneli TC girin (ornek: 12345678901)",
            min_length=11,
            max_length=11,
            required=True
        )
        self.add_item(self.tc)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_TC, {"tc": self.tc.value})
        
        # API baglanti hatasi kontrolu
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Success kontrolu
        success = sonuc.get("success")
        if success == "true" or success == True:
            embed = discord.Embed(title="KISI BILGILERI", color=discord.Color.gold(), timestamp=interaction.created_at)
            embed.add_field(name="AD SOYAD", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
            embed.add_field(name="TC KIMLIK", value=f"```{sonuc.get('TC', '-')}```", inline=True)
            embed.add_field(name="DOGUM TARIHI", value=f"```{sonuc.get('DOGUMTARIHI', '-')}```", inline=True)
            embed.add_field(name="NUFUS KAYDI", value=f"```{sonuc.get('NUFUSIL', '-')} / {sonuc.get('NUFUSILCE', '-')}```", inline=False)
            embed.add_field(name="ANNE", value=f"```{sonuc.get('ANNEADI', '-')}```", inline=True)
            embed.add_field(name="ANNE TC", value=f"```{sonuc.get('ANNETC', '-') if sonuc.get('ANNETC') else '-'}```", inline=True)
            embed.add_field(name="BABA", value=f"```{sonuc.get('BABAADI', '-')}```", inline=True)
            embed.add_field(name="BABA TC", value=f"```{sonuc.get('BABATC', '-') if sonuc.get('BABATC') else '-'}```", inline=True)
            embed.add_field(name="UYRUK", value=f"```{sonuc.get('UYRUK', '-') if sonuc.get('UYRUK') else 'TR'}```", inline=True)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Hata mesajini goster
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="SONUC BULUNAMADI", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 2. Ad Soyad Sorgulama Modal
class AdSoyadModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="AD SOYAD SORGULAMA")
        
        self.ad = discord.ui.TextInput(label="AD", placeholder="Ad giriniz", required=True, max_length=50)
        self.add_item(self.ad)
        
        self.soyad = discord.ui.TextInput(label="SOYAD", placeholder="Soyad giriniz", required=True, max_length=50)
        self.add_item(self.soyad)
        
        self.il = discord.ui.TextInput(label="IL (OPSIYONEL)", placeholder="Il giriniz", required=False, max_length=50)
        self.add_item(self.il)
        
        self.ilce = discord.ui.TextInput(label="ILCE (OPSIYONEL)", placeholder="Ilce giriniz", required=False, max_length=50)
        self.add_item(self.ilce)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        params = {"adi": self.ad.value, "soyadi": self.soyad.value}
        if self.il.value:
            params["il"] = self.il.value
        if self.ilce.value:
            params["ilce"] = self.ilce.value
        
        sonuc, status = await api_get(API_ADSOYAD, params)
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            kayitlar = sonuc.get("data", [])
            
            if len(kayitlar) == 0:
                embed = discord.Embed(title="SONUC BULUNAMADI", description="Belirtilen kriterlere uygun kayit bulunamadi.", color=discord.Color.red())
                embed.set_footer(text="made by -santes")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="ARAMA SONUCLARI",
                description=f"{len(kayitlar)} kayit bulundu\nAranan: {self.ad.value} {self.soyad.value}" + (f" - {self.il.value} {self.ilce.value}" if self.il.value else ""),
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            
            for i, k in enumerate(kayitlar[:15], 1):
                embed.add_field(
                    name=f"{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}",
                    value=f"TC: {k.get('TC', '-')}\n{k.get('NUFUSIL', '-')} / {k.get('NUFUSILCE', '-')}",
                    inline=False
                )
            
            if len(kayitlar) > 15:
                embed.set_footer(text=f"Toplam {len(kayitlar)} kayittan ilk 15'i gosteriliyor | Sorgulayan: {interaction.user.name} | made by -santes")
            else:
                embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="HATA", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 3. TC'den GSM Sorgulama Modal
class TcGsmModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="TC'DEN GSM SORGULAMA")
        
        self.tc = discord.ui.TextInput(label="TC Kimlik Numarasi", placeholder="11 haneli TC girin", min_length=11, max_length=11, required=True)
        self.add_item(self.tc)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_TCGSM, {"tc": self.tc.value})
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            telefonlar = sonuc.get("data", [])
            
            if len(telefonlar) == 0:
                embed = discord.Embed(title="SONUC BULUNAMADI", description="Bu TC'ye kayitli telefon numarasi bulunamadi.", color=discord.Color.red())
                embed.set_footer(text="made by -santes")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="TELEFON NUMARALARI",
                description=f"TC: {self.tc.value}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            
            for i, tel in enumerate(telefonlar, 1):
                embed.add_field(
                    name=f"NUMARA {i}",
                    value=f"{tel.get('GSM', '-')}\nOperator: {tel.get('OPERATOR', '-')}",
                    inline=False
                )
            
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="HATA", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 4. GSM'den TC Sorgulama Modal
class GsmTcModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="GSM'DEN TC SORGULAMA")
        
        self.gsm = discord.ui.TextInput(label="GSM Numarasi", placeholder="10 haneli GSM girin (5551234567)", required=True)
        self.add_item(self.gsm)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        gsm = ''.join(filter(str.isdigit, self.gsm.value))
        
        if len(gsm) == 10:
            pass
        elif len(gsm) == 11 and gsm.startswith('0'):
            gsm = gsm[1:]
        elif len(gsm) == 12 and gsm.startswith('90'):
            gsm = gsm[2:]
        else:
            await interaction.followup.send("HATA: GSM 10 haneli olmalidir (Ornek: 5551234567)", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_GSMTC, {"gsm": gsm})
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            embed = discord.Embed(
                title="NUMARA SAHIBI",
                description=f"GSM: {gsm}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="AD SOYAD", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
            embed.add_field(name="TC KIMLIK", value=f"```{sonuc.get('TC', '-')}```", inline=True)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="SONUC BULUNAMADI", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 5. Isyeri Sorgulama Modal
class IsyeriModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="ISYERI SORGULAMA")
        
        self.tc = discord.ui.TextInput(label="TC Kimlik Numarasi", placeholder="11 haneli TC girin", min_length=11, max_length=11, required=True)
        self.add_item(self.tc)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_ISYERI, {"tc": self.tc.value})
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            embed = discord.Embed(
                title="ISYERI BILGILERI",
                description=f"TC: {self.tc.value}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="FIRMA ADI", value=f"```{sonuc.get('FirmaAdi', '-')}```", inline=False)
            embed.add_field(name="DEPARTMAN", value=f"```{sonuc.get('Departman', '-')}```", inline=True)
            embed.add_field(name="BASLANGIC TARIHI", value=f"```{sonuc.get('BaslangicTarihi', '-')}```", inline=True)
            embed.add_field(name="SIGORTA TIPI", value=f"```{sonuc.get('SigortaTipi', '-')}```", inline=False)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="SONUC BULUNAMADI", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 6. Adres Sorgulama Modal
class AdresModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="ADRES SORGULAMA")
        
        self.tc = discord.ui.TextInput(label="TC Kimlik Numarasi", placeholder="11 haneli TC girin", min_length=11, max_length=11, required=True)
        self.add_item(self.tc)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_ADRES, {"tc": self.tc.value})
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            embed = discord.Embed(
                title="ADRES BILGILERI",
                description=f"TC: {self.tc.value}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="IL", value=f"```{sonuc.get('il', '-')}```", inline=True)
            embed.add_field(name="ILCE", value=f"```{sonuc.get('ilce', '-')}```", inline=True)
            embed.add_field(name="MAHALLE", value=f"```{sonuc.get('mahalle', '-')}```", inline=True)
            embed.add_field(name="ADRES", value=f"```{sonuc.get('adres', '-')}```", inline=False)
            embed.add_field(name="KAYIT TARIHI", value=f"```{sonuc.get('kayit_tarihi', '-')}```", inline=False)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="SONUC BULUNAMADI", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# 7. Sulale Sorgulama Modal
class SulaleModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="SULALE SORGULAMA")
        
        self.tc = discord.ui.TextInput(label="TC Kimlik Numarasi", placeholder="11 haneli TC girin", min_length=11, max_length=11, required=True)
        self.add_item(self.tc)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc, status = await api_get(API_SULALE, {"tc": self.tc.value})
        
        if sonuc is None:
            embed = discord.Embed(title="BAGLANTI HATASI", description=hata_mesaji_olustur(status), color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = sonuc.get("success")
        if success == "true" or success == True:
            embed = discord.Embed(
                title="SULALE AGACI",
                description=f"Merkez Kisi TC: {self.tc.value}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            
            embed.add_field(
                name="MERKEZ KISI",
                value=f"```Ad Soyad: {sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}\nTC: {self.tc.value}```",
                inline=False
            )
            
            if sonuc.get('ANNEADI'):
                embed.add_field(
                    name="ANNE",
                    value=f"```{sonuc.get('ANNEADI', '-')}\nTC: {sonuc.get('ANNETC', '-') if sonuc.get('ANNETC') else '-'}```",
                    inline=True
                )
            
            if sonuc.get('BABAADI'):
                embed.add_field(
                    name="BABA",
                    value=f"```{sonuc.get('BABAADI', '-')}\nTC: {sonuc.get('BABATC', '-') if sonuc.get('BABATC') else '-'}```",
                    inline=True
                )
            
            kardesler = sonuc.get('KARDESLER', [])
            if kardesler:
                kardes_listesi = ""
                for k in kardesler:
                    kardes_listesi += f"{k.get('ADI', '-')} {k.get('SOYADI', '-')} (TC: {k.get('TC', '-')})\n"
                embed.add_field(name=f"KARDESLER ({len(kardesler)} KISI)", value=f"```{kardes_listesi[:1000]}```", inline=False)
            
            cocuklar = sonuc.get('COCUKLAR', [])
            if cocuklar:
                cocuk_listesi = ""
                for c in cocuklar:
                    cocuk_listesi += f"{c.get('ADI', '-')} {c.get('SOYADI', '-')} (TC: {c.get('TC', '-')})\n"
                embed.add_field(name=f"COCUKLAR ({len(cocuklar)} KISI)", value=f"```{cocuk_listesi[:1000]}```", inline=False)
            
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name} | made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            hata_aciklamasi = hata_mesaji_olustur(status, sonuc.get('message'))
            embed = discord.Embed(title="SONUC BULUNAMADI", description=hata_aciklamasi, color=discord.Color.red())
            embed.set_footer(text="made by -santes")
            await interaction.followup.send(embed=embed, ephemeral=True)

# ==================== SLASH KOMUTLAR ====================

@bot.tree.command(name="tc", description="TC kimlik numarasi ile kisi bilgisi sorgula")
async def tc_slash(interaction: discord.Interaction):
    modal = TcModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="adsoyad", description="Ad soyad ile kisi ara")
async def adsoyad_slash(interaction: discord.Interaction):
    modal = AdSoyadModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="tcgsm", description="TC'den GSM numaralarini goster")
async def tcgsm_slash(interaction: discord.Interaction):
    modal = TcGsmModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="gsmtc", description="GSM'den TC kimlik sorgula")
async def gsmtc_slash(interaction: discord.Interaction):
    modal = GsmTcModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="isyeri", description="TC ile isyeri bilgisi sorgula")
async def isyeri_slash(interaction: discord.Interaction):
    modal = IsyeriModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="adres", description="TC ile adres bilgisi sorgula")
async def adres_slash(interaction: discord.Interaction):
    modal = AdresModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="sulale", description="TC ile sulale agaci sorgula")
async def sulale_slash(interaction: discord.Interaction):
    modal = SulaleModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="yardim", description="Yardim menusunu goster")
async def yardim_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="SORGULAMA BOTU",
        description="Asagidaki komutlari kullanarak sorgulama yapabilirsiniz",
        color=discord.Color.dark_theme()
    )
    embed.add_field(name="/tc", value="TC kimlik no ile kisi bilgisi sorgula", inline=False)
    embed.add_field(name="/adsoyad", value="Ad soyad ile kisi arama (Il ve ilce opsiyonel)", inline=False)
    embed.add_field(name="/tcgsm", value="TC'den GSM numaralarini goster", inline=False)
    embed.add_field(name="/gsmtc", value="GSM'den TC kimlik sorgula", inline=False)
    embed.add_field(name="/isyeri", value="Isyeri bilgisi sorgula", inline=False)
    embed.add_field(name="/adres", value="Adres bilgisi sorgula", inline=False)
    embed.add_field(name="/sulale", value="Sulale agaci sorgula", inline=False)
    embed.set_footer(text="made by -santes")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Prefix komutlar (alternatif)
@bot.command(name='yardim', aliases=['menu', 'help'])
async def yardim_prefix(ctx):
    embed = discord.Embed(
        title="SORGULAMA BOTU",
        description="Asagidaki komutlari kullanabilirsiniz:\n**Slash komutlar (/) daha iyi calisir!**",
        color=discord.Color.dark_theme()
    )
    embed.add_field(name="/tc", value="TC kimlik no ile kisi bilgisi sorgula", inline=False)
    embed.add_field(name="/adsoyad", value="Ad soyad ile kisi arama", inline=False)
    embed.add_field(name="/tcgsm", value="TC'den GSM numaralarini goster", inline=False)
    embed.add_field(name="/gsmtc", value="GSM'den TC kimlik sorgula", inline=False)
    embed.add_field(name="/isyeri", value="Isyeri bilgisi sorgula", inline=False)
    embed.add_field(name="/adres", value="Adres bilgisi sorgula", inline=False)
    embed.add_field(name="/sulale", value="Sulale agaci sorgula", inline=False)
    embed.set_footer(text="made by -santes")
    await ctx.send(embed=embed)

# Bot hazir oldugunda
@bot.event
async def on_ready():
    print("=" * 50)
    print(f'{bot.user} olarak giris yapildi!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Prefix: .')
    print("=" * 50)
    
    # Slash komutlarini sync et
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash komutu senkronize edildi!")
        for cmd in synced:
            print(f"  /{cmd.name}")
    except Exception as e:
        print(f"Slash komut senkronizasyon hatasi: {e}")
    
    print("=" * 50)

# Bot calistirma
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("BOT_TOKEN bulunamadi! Lutfen .env dosyanizi kontrol edin.")
