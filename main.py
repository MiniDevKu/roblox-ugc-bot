import discord
from discord import app_commands
import requests
import os
import re
import zipfile
import shutil
import io

# --- AYARLAR ---
TOKEN = "MTQ2MzY3MjgzNzE0MjQ3ODkwOQ.GT-UWI.rdXb0rECN2mcTg_NMirbgdj6dYpJuSG08O25OQ" 
ROBLOX_COOKIE = "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_CAEaAhADIhwKBGR1aWQSFDEzNDQ1MzUwMjA1OTQ5MjI2NjkxKAM.ZiPL12ZZ6B1I4eoqncF5cvMWHO-ZOQvv8Au6X70AgLl7gvdGkfm4pwdiwJTnNh91mbBsc3z3tjs6SLFwsjf45d-Uu6a3WKsGT1U93KLqgzF7VopmJmwExXKTGISgGYIGHQ0aLZrGv1kiVCVMbjErPzy2tbtLIBwwBhoXX4kkKto9faewgl8ZsOpa5dVcY0I1HiKFl3cmw6sok_b2Z2b2FiLjjwcBAi_XrIDne0EpXxcef8FuYInvL8ffA_u35JHTi_cxGtdGv68bDLOB2ZbPh7SV7v4258hL5aiEk7gHZfH2ci2oWEF2PokITMZLKCmqlvbDXLWFFFHzbgNjyFJMZRcogkLyks7wlYc16OP8YdBrB_SiZR1mLUApK6CU1V2UrjWpBRQn35AzLi_7t-Lp08keKHYhC3cTH9dkzG7iRb37-2CUivoG6Wan3M4wBBacjQuEnUKs9Fl6M07YGl3xJfF9YhiBrwHd-H8XxKHQVWGqDUNlY1XcCCOSFHchCVoyUYFTFCOw-GKUg8J8gsUzwaBdQrfszul-u45yIhXVO5KzT31VbMr5l73ErZxb8aHNMP2QZ5t658xbVh8f1zYwh7vx1KUMRVy9srn5kMqtYVrKe5YDvO_HDu0y8_X1JmjrcJZxbDXZRStFnLlD9JA8F0c9xrc67Oi5Wd7D-YNx5Q9NbdVrgzYdTR-lCVbkT-EVaxUBPmtYPbrjlBJ_6mYzvlIa79_mHGbeLpcJp7lkzSfNJZxjMJyNVlmesyTfLS5J5tFwAg" 

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