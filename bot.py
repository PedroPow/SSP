import discord
from discord.ext import commands
import time
import os

TOKEN = os.getenv("TOKEN")


CANAL_PAINEL = 1474952840928821258
CANAL_SUPERIORES = 1474983585751629998
CARGO_SUPERIOR = 1449998328334123208
CARGO_AUTORIZADO_SOLICITAR = 1449998328334123208
CARGO_SEM_SSP = 1469536548579049622  # ID do cargo SEM SSP


TEMPO_COOLDOWN = 150

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

cooldown = {}
memoria_convites = {}
pedidos_resolvidos = set()


class ModalConvite(discord.ui.Modal):

    def __init__(self, membro, superior_id, mensagem):
        super().__init__(title="Enviar convite")

        self.membro = membro
        self.superior_id = superior_id
        self.mensagem = mensagem

        texto_salvo = memoria_convites.get(superior_id, "")

        self.convite = discord.ui.TextInput(
            label="Convite / Instruções",
            style=discord.TextStyle.paragraph,
            default=texto_salvo,
            required=True
        )

        self.add_item(self.convite)

    async def on_submit(self, interaction: discord.Interaction):

        if self.mensagem.id in pedidos_resolvidos:
            await interaction.response.send_message(
                "❌ Este pedido já foi resolvido por outro superior.",
                ephemeral=True
            )
            return

        pedidos_resolvidos.add(self.mensagem.id)

        memoria_convites[self.superior_id] = self.convite.value

        embed_dm = discord.Embed(
            title="📩 Convite SSP",
            description="Seu pedido foi aprovado.",
            color=discord.Color.green()
        )

        embed_dm.add_field(
            name="Convite",
            value=self.convite.value,
            inline=False
        )

        # IMAGE DM
        embed_dm.set_image(
            url="https://cdn.discordapp.com/attachments/1444735189765849320/1474956398235353108/Logo_SSP.png?ex=699bbbb0&is=699a6a30&hm=1eeec138e00dd1d9601818ee33752f5d3613ca805716d3548bce8d198118dc0a&"
        )

        try:
            await self.membro.send(embed=embed_dm)
        except:
            pass

        embed = self.mensagem.embeds[0]

        embed.color = discord.Color.green()

        embed.set_field_at(
            2,
            name="Status",
            value="🟢 Aprovado",
            inline=False
        )

        embed.add_field(
            name="Aprovado por",
            value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
            inline=False
        )

        embed.add_field(
            name="Horário",
            value=f"<t:{int(time.time())}:F>",
            inline=False
        )

        await self.mensagem.edit(embed=embed, view=None)

        await interaction.response.send_message(
            "Convite enviado e solicitação finalizada.",
            ephemeral=True
        )


class PainelAvaliacao(discord.ui.View):
    def __init__(self, membro_id):
        super().__init__(timeout=None)
        self.membro_id = membro_id

    @discord.ui.button(
        label="Enviar Convite",
        style=discord.ButtonStyle.success
    )
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.message.id in pedidos_resolvidos:
            await interaction.response.send_message(
                "Pedido já finalizado.",
                ephemeral=True
            )
            return

        cargo = interaction.guild.get_role(CARGO_SUPERIOR)

        if cargo not in interaction.user.roles:
            await interaction.response.send_message(
                "Sem permissão.",
                ephemeral=True
            )
            return

        membro = interaction.guild.get_member(self.membro_id)

        await interaction.response.send_modal(
            ModalConvite(membro, interaction.user.id, interaction.message)
        )

    @discord.ui.button(
        label="Recusar Convite",
        style=discord.ButtonStyle.danger
    )
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.message.id in pedidos_resolvidos:
            await interaction.response.send_message(
                "❌ Pedido já finalizado.",
                ephemeral=True
            )
            return

        cargo = interaction.guild.get_role(CARGO_SUPERIOR)

        if cargo not in interaction.user.roles:
            await interaction.response.send_message(
                "Sem permissão.",
                ephemeral=True
            )
            return

        pedidos_resolvidos.add(interaction.message.id)

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        embed.set_field_at(
            2,
            name="Status",
            value="🔴 Recusado",
            inline=False
        )

        embed.add_field(
            name="Recusado por",
            value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
            inline=False
        )

        embed.add_field(
            name="Horário",
            value=f"<t:{int(time.time())}:F>",
            inline=False
        )

        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(
            "Solicitação recusada.",
            ephemeral=True
        )


class SelecionarMembroRemoverSSP(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

        select = discord.ui.UserSelect(
            placeholder="Selecione o membro para remover o cargo SEM SSP",
            min_values=1,
            max_values=1
        )

        select.callback = self.callback_select
        self.add_item(select)

    async def callback_select(self, interaction: discord.Interaction):

        cargo_superior = interaction.guild.get_role(CARGO_SUPERIOR)

        if cargo_superior not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Apenas superiores podem usar isso.",
                ephemeral=True
            )
            return

        membro = interaction.guild.get_member(interaction.data["values"][0])
        cargo_sem_ssp = interaction.guild.get_role(CARGO_SEM_SSP)

        if cargo_sem_ssp not in membro.roles:
            await interaction.response.send_message(
                "Esse membro não possui o cargo SEM SSP.",
                ephemeral=True
            )
            return

        await membro.remove_roles(cargo_sem_ssp)

        canal_log = bot.get_channel(CANAL_SUPERIORES)

        embed_log = discord.Embed(
            title="Regularização SSP",
            color=discord.Color.green()
        )

        embed_log.add_field(
            name="Membro",
            value=f"{membro.mention}\nID: `{membro.id}`",
            inline=False
        )

        embed_log.add_field(
            name="Regularizado por",
            value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
            inline=False
        )

        embed_log.add_field(
            name="Ação",
            value="Cargo **SEM SSP** removido",
            inline=False
        )

        embed_log.add_field(
            name="Horário",
            value=f"<t:{int(time.time())}:F>",
            inline=False
        )

        embed_log.set_footer(text="Sistema SSP")

        await canal_log.send(embed=embed_log)

        await interaction.response.send_message(
            f"✅ Cargo removido de {membro.mention}.",
            ephemeral=True
        )

class PainelROTA(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Regularizar SSP",
        style=discord.ButtonStyle.primary,
        custom_id="botao_regularizar_ssp"
    )
    async def regularizar_ssp(self, interaction: discord.Interaction, button: discord.ui.Button):

        cargo_superior = interaction.guild.get_role(CARGO_SUPERIOR)

        if cargo_superior not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Apenas superiores podem usar esse botão.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Selecione o membro para remover o cargo **SEM SSP**:",
            view=SelecionarMembroRemoverSSP(),
            ephemeral=True
        )        

    @discord.ui.button(
        label="Solicitar Convite",
        style=discord.ButtonStyle.gray,
        custom_id="botao_rota"
    )
    async def solicitar(self, interaction: discord.Interaction, button: discord.ui.Button):

        cargo_autorizado = interaction.guild.get_role(CARGO_AUTORIZADO_SOLICITAR)

        # BLOQUEIO DE CARGO
        if cargo_autorizado not in interaction.user.roles:
            await interaction.response.send_message(
                f"❌ Apenas membros com o cargo {cargo_autorizado.mention} podem solicitar convite.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        agora = time.time()

        if user_id in cooldown:
            tempo_restante = cooldown[user_id] - agora
            if tempo_restante > 0:
                await interaction.response.send_message(
                    "Aguarde antes de solicitar novamente.",
                    ephemeral=True
                )
                return

        cooldown[user_id] = agora + TEMPO_COOLDOWN

        canal = bot.get_channel(CANAL_SUPERIORES)
        cargo = interaction.guild.get_role(CARGO_SUPERIOR)

        embed = discord.Embed(
            title="Solicitação Convite",
            description=f"{interaction.user.mention} solicitou convite.",
            color=0xf1c40f
        )

        embed.add_field(
            name="Usuário",
            value=interaction.user.mention
        )

        embed.add_field(
            name="ID",
            value=interaction.user.id
        )

        embed.add_field(
            name="Status",
            value="🟡 Pendente",
            inline=False
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1444735189765849320/1474956398235353108/Logo_SSP.png?ex=699bbbb0&is=699a6a30&hm=1eeec138e00dd1d9601818ee33752f5d3613ca805716d3548bce8d198118dc0a&")
        embed.set_footer(text="Sistema de convite SSP")

        view = PainelAvaliacao(interaction.user.id)

        await canal.send(
            content=cargo.mention,
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            "Solicitação enviada para o Recursos Humanos.",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

    bot.add_view(PainelROTA())

    canal = bot.get_channel(CANAL_PAINEL)

    embed = discord.Embed(
        title="Solicitar Convite - SSP",
        description=(
            "Clique no botão abaixo para iniciar sua solicitação.\n\n"
            "Regras:\n\n"
            "• Apenas nomes **REGISTRAVEIS**\n"
            "• Após a solicitação **AGUARDE**\n"
            "• Apenas maiores de 18 anos\n\n"
            "Qualquer duvida chamar <#1343398653133590642>\n\n"
            "_Dignidade acima de tudo_\n\n"
            "_A Rota é reservada aos heróis_\n"
        ),
        color=discord.Color.dark_gray()
    )

    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1444735189765849320/1474956398235353108/Logo_SSP.png?ex=699bbbb0&is=699a6a30&hm=1eeec138e00dd1d9601818ee33752f5d3613ca805716d3548bce8d198118dc0a&"
    )

    await canal.purge(limit=5)
    await canal.send(embed=embed, view=PainelROTA())



# ============================
# RUN
# ============================
if not TOKEN:
    print("ERRO: TOKEN não definido.")
else:
    bot.run(TOKEN)