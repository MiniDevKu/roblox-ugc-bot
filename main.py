import discord
from discord import app_commands
import requests
import os
import re
import zipfile
import shutil
import io

# --- GÜVENLİ AYARLAR (Burayı Değiştirmene Gerek Kalmadı) ---
# Render/Railway üzerindeki 'Variables' kısmından bilgileri çeker
TOKEN = os.getenv('TOKEN') 
ROBLOX_COOKIE = os.getenv('ROBLOX_COOKIE') 

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

def create_rbxm_content(asset_id, mesh_id, tex_id):
    """Roblox Studio'nun tanıyacağı XML formatında model dosyası oluşturur"""
    return f"""<roblox version="4">
    <Item class="MeshPart" referent="RBX0">
        <Properties>
            <string name="Name">UGC_Model_{asset_id}</string>
            <Content name="MeshId"><url>rbxassetid://{mesh_id}</url></Content>
            <Content name="TextureID"><url>rbxassetid://{tex_id}</url></Content>
            <Vector3 name="Size"><X>1</X><Y>1</Y><Z>1</Z></Vector3>
        </Properties>
    </Item>
</roblox>"""

@bot.tree.command(name="assets", description="UGC verilerini indirir")
@app_commands.describe(id="UGC Asset ID")
async def assets(interaction: discord.Interaction, id: str):
    await interaction.response.defer()
    
    # Cookie kontrolü
    headers = {'Cookie': f'.ROBLOSECURITY={ROBLOX_COOKIE}'}
    temp_dir = f"temp_{id}"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)

    try:
        res = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={id}", headers=headers)
        ids = list(set(re.findall(r'rbxassetid://(\d+)', str(res.content))))
        
        mesh_id = ""
        tex_id = ""

        for sid in ids:
            sub_res = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={sid}", headers=headers)
            if b"PNG" in sub_res.content[:10] or b"JFIF" in sub_res.content[:10]:
                tex_id = sid
                with open(f"{temp_dir}/texture_{sid}.png", "wb") as f: f.write(sub_res.content)
            else:
                mesh_id = sid
                with open(f"{temp_dir}/mesh_{sid}.mesh", "wb") as f: f.write(sub_res.content)

        # .rbxm dosyasını oluştur
        rbxm_data = create_rbxm_content(id, mesh_id, tex_id)
        with open(f"{temp_dir}/model_{id}.rbxm", "w", encoding="utf-8") as f:
            f.write(rbxm_data)

        # ZIP yap ve gönder
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            for f in os.listdir(temp_dir):
                z.write(os.path.join(temp_dir, f), f)
        zip_buffer.seek(0)
        
        await interaction.followup.send(content=f"✅ **{id}** Başarıyla Hazırlandı!", file=discord.File(fp=zip_buffer, filename=f"UGC_{id}.zip"))
        
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        await interaction.followup.send(f"⚠️ Hata: {e}")

bot.run(TOKEN)