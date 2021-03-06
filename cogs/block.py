import discord
from discord.ext import commands, bridge
from cogs import utils, configs


def setup(bot):
    bot.add_cog(BlockCommands(bot))


class BlockCommands(commands.Cog, name="Permissions"):
    """Commands for disallowing certain perms for certain things"""
    COG_EMOJI = "🔏"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, name="block")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def blacklist(self, bot, user: discord.Member, *, reason=None):
        """Block a user to deny them from using the bot"""
        if await BlockUtils.get_perm("blacklist", user):
            await bot.reply("The person is already blacklisted.")
        else:
            await BlockUtils.add_perm("blacklist", user)
            e = discord.Embed(
                description=f"{bot.author.mention} has blacklisted {user.mention} for: {reason}", color=0xFF6969)
            await utils.sendembed(bot, e, False)

    @commands.command(hidden=True, name="unblock")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def unblacklist(self, bot, user: discord.Member):
        """Unblock a user to allow them to use the bot"""
        if await BlockUtils.get_perm("blacklist", user) == False:
            await bot.reply("The person is already unblacklisted.")
        else:
            await BlockUtils.remove_perm("blacklist", user)
            e = discord.Embed(
                description=f"{bot.author.mention} has unblacklisted {user.mention}", color=0x66FF99)
            await utils.sendembed(bot, e, False)

    @bridge.bridge_command(name="introvert")
    @commands.guild_only()
    async def introvert(self, bot):
        """Toggle if people use fun commands like pet on you"""
        await BlockUtils.switch_perm(self, bot, "ping", "Fun Commands on user")

    @bridge.bridge_command(name="alerts")
    async def alerts(self, bot):
        """Toggle AFK messages"""
        await GlobalBlockUtils.switch_perm(self, bot, "afk_alert", "AFK Alerts")

    @bridge.bridge_command(name="dmalerts")
    async def dmalerts(self, bot):
        """Toggle AFK messages in DM instead"""
        if await utils.can_dm_user(bot.author):
            await GlobalBlockUtils.switch_perm(self, bot, "afk_alert_dm", "AFK Alerts in DMs instead")
        else:
            await utils.senderror(bot, "I can't DM you! Try unblocking me or enabling your DMs.")

    @bridge.bridge_command(name="wbalerts")
    async def wbalerts(self, bot):
        """Toggle Welcome Back message"""
        await GlobalBlockUtils.switch_perm(self, bot, "wb_alert", "Welcome Back message")

    @bridge.bridge_command(name="wbdmalerts")
    async def wbdmalerts(self, bot):
        """Toggle Welcome Back message in DM instead"""
        if await utils.can_dm_user(bot.author):
            await GlobalBlockUtils.switch_perm(self, bot, "wb_alert_dm", "Welcome Back message in DMs instead")
        else:
            await utils.senderror(bot, "I can't DM you! Try unblocking me or enabling your DMs.")

    @commands.command(hidden=True, name="give")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def give(self, bot, user: discord.Member):
        """Give a permission to a user (use -permslist)"""
        perm = await BlockUtils.check_perm_arg(self, bot)
        if await BlockUtils.get_perm(self, bot, perm, user):
            await utils.senderror(bot, f"Nothing was changed.")
        else:
            await BlockUtils.add_perm(self, bot, perm, user)
            e = discord.Embed(
                description=f"Gave {perm} to {user.mention}", color=0xFF6969)
            await utils.sendembed(bot, e, False)

    @commands.command(hidden=True, name="remove")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove(self, bot, user: discord.Member):
        """Remove a permission from a user (use -permslist)"""
        perm = await BlockUtils.check_perm_arg(self, bot)
        if await BlockUtils.get_perm(self, bot, perm, user) == False:
            await utils.senderror(bot, f"Nothing was changed.")
        else:
            await BlockUtils.remove_perm(self, bot, perm, user)
            e = discord.Embed(
                description=f"Removed {perm} from {user.mention}", color=0x66FF99)
            await utils.sendembed(bot, e, False)

    @commands.command(hidden=True, name="permslist")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def permslist(self, bot):
        """Lists all available permissions"""
        e = discord.Embed(
            description=f"All available permissions", color=0x66FF99)
        for perm, perm_desc in self.bot.perm_list.items():
            e.add_field(name=f"{perm}", value=f"{perm_desc}", inline=False)
        await utils.sendembed(bot, e, False)

    @commands.command(hidden=True, name="reset")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def reset(self, bot, user: discord.Member):
        """Reset a user's permissions in the bot"""
        perms = self.bot.perms
        if str(user.id) in perms[str(user.guild.id)]:
            perms[str(user.guild.id)].pop(str(user.id))
            yn = await BlockUtils.set_member_perms(self, bot, perms, user)
            if yn:
                await utils.sendembed(bot, e=discord.Embed(description=f"Successfully reset {user.mention}", color=0x66FF99))
            else:
                await utils.senderror(bot, f"Couldn't reset {user.mention}")
        else:
            await utils.senderror(bot, "User isn't in data")


class BlockUtils():
    def __init__(self, bot):
        self.bot = bot

    async def open_member_perms(self, bot, user):
        perms = self.bot.perms
        if str(user.id) in perms[str(user.guild.id)]:
            return False
        else:
            await BlockUtils.set_member_perms(self, bot, perms, user)

    async def open_perms(self, bot, user):
        await BlockUtils.open_member_perms(self, bot, user)
        return self.bot.perms

    async def set_member_perms(self, bot, perms, user):
        perms[str(user.guild.id)][str(user.id)] = {}
        for value in self.bot.perms_list:
            perms[str(user.guild.id)][str(user.id)][value] = False
        configs.save(self.bot.perms_path, "w", self.bot.perms)
        return True

    async def get_perm(self, bot, perm, user):
        perms = await BlockUtils.open_perms(self, bot, user)
        return perms[str(user.guild.id)][str(user.id)][perm]

    async def add_perm(self, bot, perm, user):
        perms = await BlockUtils.open_perms(self, bot, user)
        perms[str(user.guild.id)][str(user.id)][perm] = True
        configs.save(self.bot.perms_path, "w", self.bot.perms)

    async def remove_perm(self, bot, perm, user):
        perms = await BlockUtils.open_perms(self, bot, user)
        perms[str(user.guild.id)][str(user.id)][perm] = False
        configs.save(self.bot.perms_path, "w", self.bot.perms)

    async def check_perm_arg(self, bot):
        perms_list = self.bot.perms_list
        msg = bot.message.content.split(" ")[2]
        if msg in perms_list:
            return msg
        else:
            await utils.senderror(bot, f"{bot.author.mention}, I couldn't find that permission.")

    async def switch_perm(self, bot, perm, message):
        if await BlockUtils.get_perm(self, bot, perm, bot.author):
            await BlockUtils.remove_perm(self, bot, perm, bot.author)
            await utils.sendembed(bot, discord.Embed(description=f"✅ Enabled {message}", color=0x66FF99), False)
        else:
            await BlockUtils.add_perm(self, bot, perm, bot.author)
            await utils.sendembed(bot, discord.Embed(description=f"❌ Disabled {message}", color=0xFF6969), False)


class GlobalBlockUtils():
    def __init__(self, bot):
        self.bot = bot

    async def open_global_member_perms(self, bot, user):
        perms = self.bot.global_perms
        if str(user.id) in perms:
            return False
        else:
            await GlobalBlockUtils.set_global_member_perms(self, bot, perms, user)

    async def set_global_member_perms(self, bot, perms, user):
        perms[str(user.id)] = {}
        for value in self.bot.global_perms_list_true:
            perms[str(user.id)][value] = True
        for value in self.bot.global_perms_list_false:
            perms[str(user.id)][value] = False
        configs.save(self.bot.global_perms_path, "w", perms)
        return True

    async def get_global_perm(self, bot, perm, user):
        perms = await GlobalBlockUtils.open_global_perm(self, bot, user)
        return perms[str(user.id)][perm]

    async def add_global_perm(self, bot, perm, user):
        perms = await GlobalBlockUtils.open_global_perm(self, bot, user)
        perms[str(user.id)][perm] = True
        configs.save(self.bot.global_perms_path, "w", perms)

    async def remove_global_perm(self, bot, perm, user):
        perms = await GlobalBlockUtils.open_global_perm(self, bot, user)
        perms[str(user.id)][perm] = False
        configs.save(self.bot.global_perms_path, "w", perms)

    async def open_global_perm(self, bot, user):
        await GlobalBlockUtils.open_global_member_perms(self, bot, user)
        return self.bot.global_perms

    async def switch_perm(self, bot, perm, message):
        if await GlobalBlockUtils.get_global_perm(self, bot, perm, bot.author):
            await GlobalBlockUtils.remove_global_perm(self, bot, perm, bot.author)
            await utils.sendembed(bot, discord.Embed(description=f"❌ Disabled {message}", color=0xFF6969), False)
        else:
            await GlobalBlockUtils.add_global_perm(self, bot, perm, bot.author)
            await utils.sendembed(bot, discord.Embed(description=f"✅ Enabled {message}", color=0x66FF99), False)
