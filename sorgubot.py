import discord
from discord.ext import commands
import aiohttp
import asyncio
import os

# Bot token'ınızı buraya yazın
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = "https://arastir.vip/api"

# Bot intent'leri ayarla
intents = discord.Intents.default()
intents.message_content = True
# Varsayılan help komutunu kaldır
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# API isteği gönderme
async def api_get(endpoint, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/{endpoint}", params=params, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"API hatası: {e}")
        return None

# Ana menü embed
def ana_menu_embed():
    embed = discord.Embed(
        title="**SORGULAMA BOTU**",
        description="**Aşağıdaki komutları kullanarak sorgulama yapabilirsiniz**",
        color=discord.Color.dark_theme()
    )
    embed.add_field(name="**.tc**", value="`TC kimlik no ile kişi bilgisi sorgula`", inline=False)
    embed.add_field(name="**.adsoyad**", value="`Ad soyad ile kişi arama`", inline=False)
    embed.add_field(name="**.tcgsm**", value="`TC'den GSM numaralarını göster`", inline=False)
    embed.add_field(name="**.gsmtc**", value="`GSM'den TC kimlik sorgula`", inline=False)
    embed.add_field(name="**.isyeri**", value="`İşyeri bilgisi sorgula`", inline=False)
    embed.add_field(name="**.adres**", value="`Adres bilgisi sorgula`", inline=False)
    embed.add_field(name="**.sulale**", value="`Sulale ağacı sorgula`", inline=False)
    embed.add_field(name="**.yardim**", value="`Yardım menüsü`", inline=False)
    embed.set_footer(text="Sorgulamalar gizli tutulur")
    return embed

# .yardim komutu (help alias'ini kaldırdık)
@bot.command(name='yardim', aliases=['menu'])
async def yardim(ctx):
    await ctx.send(embed=ana_menu_embed())

# .tc komutu
@bot.command(name='tc')
async def tc_sorgu(ctx, tc: str = None):
    if tc is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen TC kimlik numarasını girin**\n```.tc 12345678901```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if not tc.isdigit() or len(tc) != 11:
        embed = discord.Embed(
            title="**HATA**",
            description="**TC numarası 11 haneli olmalıdır**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("tc.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="**KİŞİ BİLGİLERİ**",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="**AD SOYAD**", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
        embed.add_field(name="**TC KİMLİK**", value=f"```{sonuc.get('TC', '-')}```", inline=True)
        embed.add_field(name="**DOĞUM TARİHİ**", value=f"```{sonuc.get('DOGUMTARIHI', '-')}```", inline=True)
        embed.add_field(name="**NÜFUS KAYDI**", value=f"```{sonuc.get('NUFUSIL', '-')} / {sonuc.get('NUFUSILCE', '-')}```", inline=False)
        embed.add_field(name="**ANNE BİLGİSİ**", value=f"```{sonuc.get('ANNEADI', '-')} (TC: {sonuc.get('ANNETC', '-')})```", inline=True)
        embed.add_field(name="**BABA BİLGİSİ**", value=f"```{sonuc.get('BABAADI', '-')} (TC: {sonuc.get('BABATC', '-')})```", inline=True)
        embed.add_field(name="**UYRUK**", value=f"```{sonuc.get('UYRUK', '-')}```", inline=True)
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**SONUÇ BULUNAMADI**",
            description="**Belirtilen TC kimlik numarasına ait kayıt bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .adsoyad komutu
@bot.command(name='adsoyad')
async def adsoyad_sorgu(ctx, ad: str = None, soyad: str = None, il: str = None, ilce: str = None):
    if ad is None or soyad is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen ad ve soyad girin**\n```.adsoyad Ahmet Yılmaz```\n```.adsoyad Ahmet Yılmaz İstanbul```\n```.adsoyad Ahmet Yılmaz İstanbul Kadıköy```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    params = {"adi": ad, "soyadi": soyad}
    if il:
        params["il"] = il
    if ilce:
        params["ilce"] = ilce
    
    sonuc = await api_get("adsoyad.php", params)
    
    if sonuc and sonuc.get("success") == "true":
        kayitlar = sonuc.get("data", [])
        
        if len(kayitlar) == 0:
            embed = discord.Embed(
                title="**SONUÇ BULUNAMADI**",
                description="**Belirtilen kriterlere uygun kayıt bulunamadı**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"**ARAMA SONUÇLARI**",
            description=f"**{len(kayitlar)} kayıt bulundu**\n`{ad} {soyad}`" + (f" - `{il} {ilce}`" if il else ""),
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        
        for i, k in enumerate(kayitlar[:15], 1):
            embed.add_field(
                name=f"**{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}**",
                value=f"`TC: {k.get('TC', '-')}`\n`{k.get('NUFUSIL', '-')} / {k.get('NUFUSILCE', '-')}`",
                inline=False
            )
        
        if len(kayitlar) > 15:
            embed.set_footer(text=f"Toplam {len(kayitlar)} kayıttan ilk 15'i gösteriliyor | Sorgulayan: {ctx.author.name}")
        else:
            embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**HATA**",
            description="**API hatası oluştu veya kayıt bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .tcgsm komutu
@bot.command(name='tcgsm', aliases=['tcdengsm'])
async def tcgsm_sorgu(ctx, tc: str = None):
    if tc is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen TC kimlik numarasını girin**\n```.tcgsm 12345678901```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if not tc.isdigit() or len(tc) != 11:
        embed = discord.Embed(
            title="**HATA**",
            description="**TC numarası 11 haneli olmalıdır**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("tel.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        telefonlar = sonuc.get("data", [])
        
        if len(telefonlar) == 0:
            embed = discord.Embed(
                title="**SONUÇ BULUNAMADI**",
                description="**Bu TC'ye kayıtlı telefon numarası bulunamadı**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"**TELEFON NUMARALARI**",
            description=f"`TC: {tc}`",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        
        for i, tel in enumerate(telefonlar, 1):
            embed.add_field(
                name=f"**NUMARA {i}**",
                value=f"`{tel.get('GSM', '-')}`\n`Operatör: {tel.get('OPERATOR', '-')}`",
                inline=False
            )
        
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**HATA**",
            description="**API hatası oluştu veya kayıt bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .gsmtc komutu
@bot.command(name='gsmtc', aliases=['gsmden'])
async def gsmtc_sorgu(ctx, gsm: str = None):
    if gsm is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen GSM numarasını girin**\n```.gsmtc 5551234567```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    gsm = ''.join(filter(str.isdigit, gsm))
    
    if len(gsm) == 10:
        pass
    elif len(gsm) == 11 and gsm.startswith('0'):
        gsm = gsm[1:]
    elif len(gsm) == 12 and gsm.startswith('90'):
        gsm = gsm[2:]
    else:
        embed = discord.Embed(
            title="**HATA**",
            description="**GSM 10 haneli olmalıdır**\n`Örnek: 5551234567`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("gsmtc.php", {"gsm": gsm})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="**NUMARA SAHİBİ**",
            description=f"`GSM: {gsm}`",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="**AD SOYAD**", value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```", inline=False)
        embed.add_field(name="**TC KİMLİK**", value=f"```{sonuc.get('TC', '-')}```", inline=True)
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**SONUÇ BULUNAMADI**",
            description="**Belirtilen GSM numarasına ait kayıt bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .isyeri komutu
@bot.command(name='isyeri', aliases=['work'])
async def isyeri_sorgu(ctx, tc: str = None):
    if tc is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen TC kimlik numarasını girin**\n```.isyeri 12345678901```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if not tc.isdigit() or len(tc) != 11:
        embed = discord.Embed(
            title="**HATA**",
            description="**TC numarası 11 haneli olmalıdır**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("isyeri.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="**İŞYERİ BİLGİLERİ**",
            description=f"`TC: {tc}`",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="**FİRMA ADI**", value=f"```{sonuc.get('FirmaAdi', '-')}```", inline=False)
        embed.add_field(name="**DEPARTMAN**", value=f"```{sonuc.get('Departman', '-')}```", inline=True)
        embed.add_field(name="**BAŞLANGIÇ TARİHİ**", value=f"```{sonuc.get('BaslangicTarihi', '-')}```", inline=True)
        embed.add_field(name="**SİGORTA TİPİ**", value=f"```{sonuc.get('SigortaTipi', '-')}```", inline=False)
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**SONUÇ BULUNAMADI**",
            description="**İşyeri bilgisi bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .adres komutu
@bot.command(name='adres', aliases=['address'])
async def adres_sorgu(ctx, tc: str = None):
    if tc is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen TC kimlik numarasını girin**\n```.adres 12345678901```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if not tc.isdigit() or len(tc) != 11:
        embed = discord.Embed(
            title="**HATA**",
            description="**TC numarası 11 haneli olmalıdır**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("adres.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="**ADRES BİLGİLERİ**",
            description=f"`TC: {tc}`",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="**İL**", value=f"```{sonuc.get('il', '-')}```", inline=True)
        embed.add_field(name="**İLÇE**", value=f"```{sonuc.get('ilce', '-')}```", inline=True)
        embed.add_field(name="**MAHALLE**", value=f"```{sonuc.get('mahalle', '-')}```", inline=True)
        embed.add_field(name="**ADRES**", value=f"```{sonuc.get('adres', '-')}```", inline=False)
        embed.add_field(name="**KAYIT TARİHİ**", value=f"```{sonuc.get('kayit_tarihi', '-')}```", inline=False)
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**SONUÇ BULUNAMADI**",
            description="**Adres bilgisi bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# .sulale komutu
@bot.command(name='sulale', aliases=['aile', 'family'])
async def sulale_sorgu(ctx, tc: str = None):
    if tc is None:
        embed = discord.Embed(
            title="**HATA**",
            description="**Lütfen TC kimlik numarasını girin**\n```.sulale 12345678901```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if not tc.isdigit() or len(tc) != 11:
        embed = discord.Embed(
            title="**HATA**",
            description="**TC numarası 11 haneli olmalıdır**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    embed_wait = discord.Embed(
        title="**SORGULANIYOR**",
        description="**Lütfen bekleyin...**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_wait)
    
    sonuc = await api_get("sulale.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="**SULALE AĞACI**",
            description=f"`Merkez Kişi TC: {tc}`",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        
        embed.add_field(
            name="**MERKEZ KİŞİ**",
            value=f"```{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}```\n`TC: {tc}`",
            inline=False
        )
        
        if sonuc.get('ANNEADI'):
            embed.add_field(
                name="**ANNE**",
                value=f"```{sonuc.get('ANNEADI', '-')}```\n`TC: {sonuc.get('ANNETC', '-')}`",
                inline=True
            )
        
        if sonuc.get('BABAADI'):
            embed.add_field(
                name="**BABA**",
                value=f"```{sonuc.get('BABAADI', '-')}```\n`TC: {sonuc.get('BABATC', '-')}`",
                inline=True
            )
        
        kardesler = sonuc.get('KARDESLER', [])
        if kardesler:
            kardes_listesi = "\n".join([f"`{k.get('ADI', '-')} {k.get('SOYADI', '-')}` (TC: `{k.get('TC', '-')}`)" for k in kardesler[:5]])
            if len(kardesler) > 5:
                kardes_listesi += f"\n*...ve {len(kardesler)-5} kişi daha*"
            embed.add_field(name="**KARDEŞLER**", value=kardes_listesi, inline=False)
        
        cocuklar = sonuc.get('COCUKLAR', [])
        if cocuklar:
            cocuk_listesi = "\n".join([f"`{c.get('ADI', '-')} {c.get('SOYADI', '-')}` (TC: `{c.get('TC', '-')}`)" for c in cocuklar[:5]])
            if len(cocuklar) > 5:
                cocuk_listesi += f"\n*...ve {len(cocuklar)-5} kişi daha*"
            embed.add_field(name="**ÇOCUKLAR**", value=cocuk_listesi, inline=False)
        
        embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="**SONUÇ BULUNAMADI**",
            description="**Sulale ağacı bilgisi bulunamadı**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Bot hazır olduğunda
@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")
    print(f"Bot ID: {bot.user.id}")
    print(f"Prefix: .")
    await bot.change_presence(activity=discord.Game(name=".yardim | Sorgulama Botu"))

# Bot çalıştırma
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("BOT_TOKEN bulunamadı! Lütfen .env dosyanızı kontrol edin.")
