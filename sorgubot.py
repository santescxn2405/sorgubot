import discord
from discord.ext import commands
from discord import ui
import aiohttp
import asyncio
import os

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

# API istegi gonderme
async def api_get(url, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"API hatasi: {e}")
        return None

# ==================== MODAL SINIFLARI ====================

# 1. TC Sorgulama Modal
class TcModal(ui.Modal, title='TC KIMLIK SORGULAMA'):
    tc = ui.TextInput(label='TC Kimlik Numarasi', placeholder='11 haneli TC girin', min_length=11, max_length=11, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc = await api_get(API_TC, {"tc": self.tc.value})
        
        if sonuc and sonuc.get("success") == "true":
            embed = discord.Embed(title="KISI BILGILERI", color=discord.Color.gold(), timestamp=interaction.created_at)
            embed.add_field(name="AD SOYAD", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
            embed.add_field(name="TC KIMLIK", value=f"```{sonuc.get('TC', '-')}```", inline=True)
            embed.add_field(name="DOGUM TARIHI", value=f"```{sonuc.get('DOGUMTARIHI', '-')}```", inline=True)
            embed.add_field(name="NUFUS KAYDI", value=f"```{sonuc.get('NUFUSIL', '-')} / {sonuc.get('NUFUSILCE', '-')}```", inline=False)
            embed.add_field(name="ANNE", value=f"```{sonuc.get('ANNEADI', '-')}```", inline=True)
            embed.add_field(name="ANNE TC", value=f"```{sonuc.get('ANNETC', '-')}```", inline=True)
            embed.add_field(name="BABA", value=f"```{sonuc.get('BABAADI', '-')}```", inline=True)
            embed.add_field(name="BABA TC", value=f"```{sonuc.get('BABATC', '-')}```", inline=True)
            embed.add_field(name="UYRUK", value=f"```{sonuc.get('UYRUK', '-')}```", inline=True)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("SONUC BULUNAMADI: Belirtilen TC kimlik numarasina ait kayit bulunamadi.", ephemeral=True)

# 2. Ad Soyad Sorgulama Modal
class AdSoyadModal(ui.Modal, title='AD SOYAD SORGULAMA'):
    ad = ui.TextInput(label='Ad', placeholder='Ad girin', required=True)
    soyad = ui.TextInput(label='Soyad', placeholder='Soyad girin', required=True)
    il = ui.TextInput(label='Il', placeholder='Il girin (istege bagli)', required=False)
    ilce = ui.TextInput(label='Ilce', placeholder='Ilce girin (istege bagli)', required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        params = {"adi": self.ad.value, "soyadi": self.soyad.value}
        if self.il.value:
            params["il"] = self.il.value
        if self.ilce.value:
            params["ilce"] = self.ilce.value
        
        sonuc = await api_get(API_ADSOYAD, params)
        
        if sonuc and sonuc.get("success") == "true":
            kayitlar = sonuc.get("data", [])
            
            if len(kayitlar) == 0:
                await interaction.followup.send("SONUC BULUNAMADI: Belirtilen kriterlere uygun kayit bulunamadi.", ephemeral=True)
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
                embed.set_footer(text=f"Toplam {len(kayitlar)} kayittan ilk 15'i gosteriliyor | Sorgulayan: {interaction.user.name}")
            else:
                embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("HATA: API hatasi olustu veya kayit bulunamadi.", ephemeral=True)

# 3. TC'den GSM Sorgulama Modal
class TcGsmModal(ui.Modal, title='TC\'DEN GSM SORGULAMA'):
    tc = ui.TextInput(label='TC Kimlik Numarasi', placeholder='11 haneli TC girin', min_length=11, max_length=11, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc = await api_get(API_TCGSM, {"tc": self.tc.value})
        
        if sonuc and sonuc.get("success") == "true":
            telefonlar = sonuc.get("data", [])
            
            if len(telefonlar) == 0:
                await interaction.followup.send("SONUC BULUNAMADI: Bu TC'ye kayitli telefon numarasi bulunamadi.", ephemeral=True)
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
            
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("HATA: API hatasi olustu veya kayit bulunamadi.", ephemeral=True)

# 4. GSM'den TC Sorgulama Modal
class GsmTcModal(ui.Modal, title='GSM\'DEN TC SORGULAMA'):
    gsm = ui.TextInput(label='GSM Numarasi', placeholder='10 haneli GSM girin (5551234567)', required=True)
    
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
        
        sonuc = await api_get(API_GSMTC, {"gsm": gsm})
        
        if sonuc and sonuc.get("success") == "true":
            embed = discord.Embed(
                title="NUMARA SAHIBI",
                description=f"GSM: {gsm}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="AD SOYAD", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
            embed.add_field(name="TC KIMLIK", value=f"```{sonuc.get('TC', '-')}```", inline=True)
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("SONUC BULUNAMADI: Belirtilen GSM numarasina ait kayit bulunamadi.", ephemeral=True)

# 5. Isyeri Sorgulama Modal
class IsyeriModal(ui.Modal, title='ISYERI SORGULAMA'):
    tc = ui.TextInput(label='TC Kimlik Numarasi', placeholder='11 haneli TC girin', min_length=11, max_length=11, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc = await api_get(API_ISYERI, {"tc": self.tc.value})
        
        if sonuc and sonuc.get("success") == "true":
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
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("SONUC BULUNAMADI: Isyeri bilgisi bulunamadi.", ephemeral=True)

# 6. Adres Sorgulama Modal
class AdresModal(ui.Modal, title='ADRES SORGULAMA'):
    tc = ui.TextInput(label='TC Kimlik Numarasi', placeholder='11 haneli TC girin', min_length=11, max_length=11, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc = await api_get(API_ADRES, {"tc": self.tc.value})
        
        if sonuc and sonuc.get("success") == "true":
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
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("SONUC BULUNAMADI: Adres bilgisi bulunamadi.", ephemeral=True)

# 7. Sulale Sorgulama Modal
class SulaleModal(ui.Modal, title='SULALE SORGULAMA'):
    tc = ui.TextInput(label='TC Kimlik Numarasi', placeholder='11 haneli TC girin', min_length=11, max_length=11, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.tc.value.isdigit():
            await interaction.followup.send("HATA: TC numarasi sadece rakamlardan olusmalidir.", ephemeral=True)
            return
        
        sonuc = await api_get(API_SULALE, {"tc": self.tc.value})
        
        if sonuc and sonuc.get("success") == "true":
            embed = discord.Embed(
                title="SULALE AGACI",
                description=f"Merkez Kisi TC: {self.tc.value}",
                color=discord.Color.gold(),
                timestamp=interaction.created_at
            )
            
            embed.add_field(
                name="MERKEZ KISI",
                value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```\nTC: {self.tc.value}",
                inline=False
            )
            
            if sonuc.get('ANNEADI'):
                embed.add_field(
                    name="ANNE",
                    value=f"```{sonuc.get('ANNEADI', '-')}```\nTC: {sonuc.get('ANNETC', '-')}",
                    inline=True
                )
            
            if sonuc.get('BABAADI'):
                embed.add_field(
                    name="BABA",
                    value=f"```{sonuc.get('BABAADI', '-')}```\nTC: {sonuc.get('BABATC', '-')}",
                    inline=True
                )
            
            kardesler = sonuc.get('KARDESLER', [])
            if kardesler:
                kardes_listesi = "\n".join([f"{k.get('ADI', '-')} {k.get('SOYADI', '-')} (TC: {k.get('TC', '-')})" for k in kardesler[:5]])
                if len(kardesler) > 5:
                    kardes_listesi += f"\n...ve {len(kardesler)-5} kisi daha"
                embed.add_field(name="KARDESLER", value=f"```{kardes_listesi}```", inline=False)
            
            cocuklar = sonuc.get('COCUKLAR', [])
            if cocuklar:
                cocuk_listesi = "\n".join([f"{c.get('ADI', '-')} {c.get('SOYADI', '-')} (TC: {c.get('TC', '-')})" for c in cocuklar[:5]])
                if len(cocuklar) > 5:
                    cocuk_listesi += f"\n...ve {len(cocuklar)-5} kisi daha"
                embed.add_field(name="COCUKLAR", value=f"```{cocuk_listesi}```", inline=False)
            
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("SONUC BULUNAMADI: Sulale agaci bilgisi bulunamadi.", ephemeral=True)

# ==================== KOMUTLAR ====================

# Yardim Menusu
@bot.command(name='yardim', aliases=['menu', 'help'])
async def yardim(ctx):
    embed = discord.Embed(
        title="SORGULAMA BOTU",
        description="Asagidaki komutlari kullanarak sorgulama yapabilirsiniz",
        color=discord.Color.dark_theme()
    )
    embed.add_field(name=".tc", value="TC kimlik no ile kisi bilgisi sorgula", inline=False)
    embed.add_field(name=".adsoyad", value="Ad soyad ile kisi arama", inline=False)
    embed.add_field(name=".tcgsm", value="TC'den GSM numaralarini goster", inline=False)
    embed.add_field(name=".gsmtc", value="GSM'den TC kimlik sorgula", inline=False)
    embed.add_field(name=".isyeri", value="Isyeri bilgisi sorgula", inline=False)
    embed.add_field(name=".adres", value="Adres bilgisi sorgula", inline=False)
    embed.add_field(name=".sulale", value="Sulale agaci sorgula", inline=False)
    embed.set_footer(text="Tum sorgulamalar gizli olarak size ozel gonderilir")
    await ctx.send(embed=embed)

# TC Komutu
@bot.command(name='tc')
async def tc_command(ctx):
    modal = TcModal()
    await ctx.send_modal(modal)

# Ad Soyad Komutu
@bot.command(name='adsoyad')
async def adsoyad_command(ctx):
    modal = AdSoyadModal()
    await ctx.send_modal(modal)

# TC'den GSM Komutu
@bot.command(name='tcgsm', aliases=['tcdengsm'])
async def tcgsm_command(ctx):
    modal = TcGsmModal()
    await ctx.send_modal(modal)

# GSM'den TC Komutu
@bot.command(name='gsmtc', aliases=['gsmden'])
async def gsmtc_command(ctx):
    modal = GsmTcModal()
    await ctx.send_modal(modal)

# Isyeri Komutu
@bot.command(name='isyeri', aliases=['work'])
async def isyeri_command(ctx):
    modal = IsyeriModal()
    await ctx.send_modal(modal)

# Adres Komutu
@bot.command(name='adres', aliases=['address'])
async def adres_command(ctx):
    modal = AdresModal()
    await ctx.send_modal(modal)

# Sulale Komutu
@bot.command(name='sulale', aliases=['aile', 'family'])
async def sulale_command(ctx):
    modal = SulaleModal()
    await ctx.send_modal(modal)

# Bot hazir oldugunda
@bot.event
async def on_ready():
    print("=" * 50)
    print(f'{bot.user} olarak giris yapildi!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Prefix: .')
    print("=" * 50)

# Bot calistirma
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("BOT_TOKEN bulunamadi! Lutfen .env dosyanizi kontrol edin.")
