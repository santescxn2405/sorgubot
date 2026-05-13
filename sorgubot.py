import discord
from discord.ext import commands
import aiohttp
import asyncio

# Bot token'ınızı buraya yazın
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = "https://arastir.vip/api"

# Bot intent'leri ayarla
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

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
        title="🔍 Sorgulama Botu",
        description="Aşağıdaki komutları kullanarak sorgulama yapabilirsiniz:",
        color=discord.Color.blue()
    )
    embed.add_field(name=".tc", value="🔍 TC kimlik no ile kişi bilgisi sorgula", inline=False)
    embed.add_field(name=".adsoyad", value="👤 Ad soyad ile kişi arama", inline=False)
    embed.add_field(name=".tcgsm", value="📱 TC'den GSM numaralarını göster", inline=False)
    embed.add_field(name=".gsmtc", value="📞 GSM'den TC kimlik sorgula", inline=False)
    embed.add_field(name=".isyeri", value="🏢 İşyeri bilgisi sorgula", inline=False)
    embed.add_field(name=".adres", value="🏠 Adres bilgisi sorgula", inline=False)
    embed.add_field(name=".sulale", value="👨‍👩‍👧‍👦 Sulale ağacı sorgula", inline=False)
    embed.add_field(name=".yardim", value="❓ Yardım menüsü", inline=False)
    embed.set_footer(text="Sorgulamalar gizli tutulur, güvenle kullanabilirsiniz.")
    return embed

# .yardim komutu
@bot.command(name='yardim', aliases=['help', 'menu'])
async def yardim(ctx):
    await ctx.send(embed=ana_menu_embed())

# .tc komutu
@bot.command(name='tc')
async def tc_sorgu(ctx, tc: str = None):
    if tc is None:
        await ctx.send("❌ Lütfen TC kimlik numarasını girin.\nKullanım: `.tc 12345678901`")
        return
    
    # TC kontrolü
    if not tc.isdigit() or len(tc) != 11:
        await ctx.send("❌ Hatalı format! TC numarası 11 haneli olmalıdır.")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("tc.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(title="✅ Kişi Bilgileri", color=discord.Color.green())
        embed.add_field(name="👤 Ad Soyad", value=f"{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}", inline=False)
        embed.add_field(name="🆔 TC", value=sonuc.get('TC', '-'), inline=False)
        embed.add_field(name="🎂 Doğum Tarihi", value=sonuc.get('DOGUMTARIHI', '-'), inline=False)
        embed.add_field(name="📍 Nüfus", value=f"{sonuc.get('NUFUSIL', '-')} / {sonuc.get('NUFUSILCE', '-')}", inline=False)
        embed.add_field(name="👩 Anne Adı", value=f"{sonuc.get('ANNEADI', '-')} (TC: {sonuc.get('ANNETC', '-')})", inline=False)
        embed.add_field(name="👨 Baba Adı", value=f"{sonuc.get('BABAADI', '-')} (TC: {sonuc.get('BABATC', '-')})", inline=False)
        embed.add_field(name="🌍 Uyruk", value=sonuc.get('UYRUK', '-'), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı.")

# .adsoyad komutu
@bot.command(name='adsoyad')
async def adsoyad_sorgu(ctx, ad: str = None, soyad: str = None, il: str = None, ilce: str = None):
    if ad is None or soyad is None:
        await ctx.send("❌ Lütfen ad ve soyad girin.\nKullanım: `.adsoyad Ahmet Yılmaz`\nVeya: `.adsoyad Ahmet Yılmaz İstanbul`\nVeya: `.adsoyad Ahmet Yılmaz İstanbul Kadıköy`")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    params = {"adi": ad, "soyadi": soyad}
    if il:
        params["il"] = il
    if ilce:
        params["ilce"] = ilce
    
    sonuc = await api_get("adsoyad.php", params)
    
    if sonuc and sonuc.get("success") == "true":
        kayitlar = sonuc.get("data", [])
        
        if len(kayitlar) == 0:
            await ctx.send("❌ Kayıt bulunamadı.")
            return
        
        embed = discord.Embed(
            title=f"✅ {len(kayitlar)} Kayıt Bulundu",
            description=f"Aranan: {ad} {soyad}" + (f" - {il} {ilce}" if il else ""),
            color=discord.Color.green()
        )
        
        # İlk 15 kaydı göster
        for i, k in enumerate(kayitlar[:15], 1):
            embed.add_field(
                name=f"{i}. {k.get('ADI', '-')} {k.get('SOYADI', '-')}",
                value=f"🆔 TC: {k.get('TC', '-')}\n📍 {k.get('NUFUSIL', '-')} / {k.get('NUFUSILCE', '-')}",
                inline=False
            )
        
        if len(kayitlar) > 15:
            embed.set_footer(text=f"Toplam {len(kayitlar)} kayıttan ilk 15'i gösteriliyor.")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı veya API hatası oluştu.")

# .tcgsm komutu
@bot.command(name='tcgsm', aliases=['tcdengsm'])
async def tcgsm_sorgu(ctx, tc: str = None):
    if tc is None:
        await ctx.send("❌ Lütfen TC kimlik numarasını girin.\nKullanım: `.tcgsm 12345678901`")
        return
    
    if not tc.isdigit() or len(tc) != 11:
        await ctx.send("❌ Hatalı format! TC numarası 11 haneli olmalıdır.")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("tel.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        telefonlar = sonuc.get("data", [])
        
        if len(telefonlar) == 0:
            await ctx.send("❌ Bu TC'ye kayıtlı telefon numarası bulunamadı.")
            return
        
        embed = discord.Embed(
            title=f"📱 TC'ye Kayıtlı Telefonlar",
            description=f"TC: {tc}",
            color=discord.Color.green()
        )
        
        for i, tel in enumerate(telefonlar, 1):
            embed.add_field(
                name=f"Telefon {i}",
                value=f"📞 {tel.get('GSM', '-')}\n🏢 Operatör: {tel.get('OPERATOR', '-')}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı veya API hatası oluştu.")

# .gsmtc komutu
@bot.command(name='gsmtc', aliases=['gsmden']
async def gsmtc_sorgu(ctx, gsm: str = None):
    if gsm is None:
        await ctx.send("❌ Lütfen GSM numarasını girin.\nKullanım: `.gsmtc 5551234567`")
        return
    
    # Sadece rakamları al
    gsm = ''.join(filter(str.isdigit, gsm))
    
    if len(gsm) == 10:
        pass  # Tamam
    elif len(gsm) == 11 and gsm.startswith('0'):
        gsm = gsm[1:]  # Baştaki 0'ı kaldır
    elif len(gsm) == 12 and gsm.startswith('90'):
        gsm = gsm[2:]  # 90'ı kaldır
    else:
        await ctx.send("❌ Hatalı format! GSM 10 haneli olmalıdır (örn: 5551234567)")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("gsmtc.php", {"gsm": gsm})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="✅ Numara Sahibi",
            description=f"📞 GSM: {gsm}",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Ad Soyad", value=f"{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}", inline=False)
        embed.add_field(name="🆔 TC", value=sonuc.get('TC', '-'), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı.")

# .isyeri komutu
@bot.command(name='isyeri', aliases=['work'])
async def isyeri_sorgu(ctx, tc: str = None):
    if tc is None:
        await ctx.send("❌ Lütfen TC kimlik numarasını girin.\nKullanım: `.isyeri 12345678901`")
        return
    
    if not tc.isdigit() or len(tc) != 11:
        await ctx.send("❌ Hatalı format! TC numarası 11 haneli olmalıdır.")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("isyeri.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="🏢 İşyeri Bilgileri",
            description=f"TC: {tc}",
            color=discord.Color.green()
        )
        embed.add_field(name="🏢 Firma Adı", value=sonuc.get('FirmaAdi', '-'), inline=False)
        embed.add_field(name="💼 Departman", value=sonuc.get('Departman', '-'), inline=False)
        embed.add_field(name="📅 Başlangıç Tarihi", value=sonuc.get('BaslangicTarihi', '-'), inline=False)
        embed.add_field(name="💰 Sigorta Tipi", value=sonuc.get('SigortaTipi', '-'), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı.")

# .adres komutu
@bot.command(name='adres', aliases=['address'])
async def adres_sorgu(ctx, tc: str = None):
    if tc is None:
        await ctx.send("❌ Lütfen TC kimlik numarasını girin.\nKullanım: `.adres 12345678901`")
        return
    
    if not tc.isdigit() or len(tc) != 11:
        await ctx.send("❌ Hatalı format! TC numarası 11 haneli olmalıdır.")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("adres.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="🏠 Adres Bilgileri",
            description=f"TC: {tc}",
            color=discord.Color.green()
        )
        embed.add_field(name="🏘 İl", value=sonuc.get('il', '-'), inline=True)
        embed.add_field(name="🏡 İlçe", value=sonuc.get('ilce', '-'), inline=True)
        embed.add_field(name="📍 Mahalle", value=sonuc.get('mahalle', '-'), inline=True)
        embed.add_field(name="📮 Adres", value=sonuc.get('adres', '-'), inline=False)
        embed.add_field(name="📅 Kayıt Tarihi", value=sonuc.get('kayit_tarihi', '-'), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı.")

# .sulale komutu
@bot.command(name='sulale', aliases=['aile', 'family'])
async def sulale_sorgu(ctx, tc: str = None):
    if tc is None:
        await ctx.send("❌ Lütfen TC kimlik numarasını girin.\nKullanım: `.sulale 12345678901`")
        return
    
    if not tc.isdigit() or len(tc) != 11:
        await ctx.send("❌ Hatalı format! TC numarası 11 haneli olmalıdır.")
        return
    
    await ctx.send("🔍 Sorgulanıyor, lütfen bekleyin...")
    
    sonuc = await api_get("sulale.php", {"tc": tc})
    
    if sonuc and sonuc.get("success") == "true":
        embed = discord.Embed(
            title="👨‍👩‍👧‍👦 Sulale Ağacı",
            description=f"Merkez Kişi TC: {tc}",
            color=discord.Color.green()
        )
        
        # Merkez kişi
        embed.add_field(
            name="📌 Merkez Kişi",
            value=f"{sonuc.get('ADI', '-')} {sonuc.get('SOYADI', '-')}\n🆔 {tc}",
            inline=False
        )
        
        # Anne
        if sonuc.get('ANNEADI'):
            embed.add_field(
                name="👩 Anne",
                value=f"{sonuc.get('ANNEADI', '-')} (TC: {sonuc.get('ANNETC', '-')})",
                inline=True
            )
        
        # Baba
        if sonuc.get('BABAADI'):
            embed.add_field(
                name="👨 Baba",
                value=f"{sonuc.get('BABAADI', '-')} (TC: {sonuc.get('BABATC', '-')})",
                inline=True
            )
        
        # Kardeşler
        kardesler = sonuc.get('KARDESLER', [])
        if kardesler:
            kardes_listesi = "\n".join([f"• {k.get('ADI', '-')} {k.get('SOYADI', '-')} (TC: {k.get('TC', '-')})" for k in kardesler[:5]])
            if len(kardesler) > 5:
                kardes_listesi += f"\n...ve {len(kardesler)-5} kişi daha"
            embed.add_field(name="👥 Kardeşler", value=kardes_listesi, inline=False)
        
        # Çocuklar
        cocuklar = sonuc.get('COCUKLAR', [])
        if cocuklar:
            cocuk_listesi = "\n".join([f"• {c.get('ADI', '-')} {c.get('SOYADI', '-')} (TC: {c.get('TC', '-')})" for c in cocuklar[:5]])
            if len(cocuklar) > 5:
                cocuk_listesi += f"\n...ve {len(cocuklar)-5} kişi daha"
            embed.add_field(name="👶 Çocuklar", value=cocuk_listesi, inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Kayıt bulunamadı.")

# Bot hazır olduğunda
@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")
    print(f"Bot ID: {bot.user.id}")
    print(f"Prefix: .")
    await bot.change_presence(activity=discord.Game(name=".yardim | Sorgulama Botu"))

# Bot çalıştırma
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
