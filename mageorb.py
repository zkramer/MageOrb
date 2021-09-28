import os
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
from discord.ext.commands import CommandNotFound
TOKEN = os.getenv('DISCORD_TOKEN')

#Handles command prefix and setup for games running on multiple channels and servers simultaneously
client = commands.Bot(command_prefix="!", help_command=None)
gameinstances = {}

#Print Help Message
async def helpmsg(ctx):
    await ctx.message.delete()
    embed1 = discord.Embed()
    embed1.title = "Help"
    embed1.description = "Mage Orb Bot Version 1.2\nMage Orb Game by Donathin Frye: Twitter - @DonathinFrye\nMage Orb Bot by Ithaea\n\nCurrent Commands:\n!help - Display this menu\n!matrix - Display win/loss matrix\n!rules - Display the rules of Mage Orb\n!concede - Concede the current game you are playing in\n\n!mageorb - Start a new game\n-----Required Arguments: @PLAYER1 @PLAYER2\n-----Optional Arguments: P1SPELLSLOTS P2SPELLSLOTS ROUNDS\n --------------------------\n    Example 1: !mageorb @DonathinFrye @Ithaea - will start a game with default spell slots and rounds between @DonathinFrye and @Ithaea\n\n Example 2: !mageorb @DonathinFrye @Ithaea 4 4 8 - will start a game between the same players listed but each player will have 4 spell slots and the game will last 8 rounds. \n\n Spell Slot Default for each player: 3 \n Round Default: 7"
    await ctx.send(embed=embed1)


@client.command()
#Print Rules of the Game
async def rules(ctx):
    await ctx.message.delete()
    embed = discord.Embed()
    embed.title = "Rules"
    embed.description = "The full rules for Mage Orb are located [here](https://docs.google.com/document/d/1r6DRZ_08xzNlj2U4-KOsioO2oAhPzEWKum1GGSxeIiw/edit?usp=sharing).\n\nEach Rune beats 2 Runes, ties itself and loses to 2 other Runes\n⚔ beats 🔥 💀\n🛡️ beats ⚔ 🪞\n🔥 beats 🛡️ 💀\n🪞 beats ⚔ 🔥\n💀 beats 🛡️ 🪞\nThe full win/loss matrix is available at !matrix\n\nIf you beat your opponent's Rune you can lock one of their Runes\nIf you lose, they lock one of yours\nIf you tie with ⚔, 💀, or 🔥 you both lock a Rune of your opponents\nIf you tie with 🛡️ or 🪞 you both get to unlock one of your locked Runes\n\nYou can spend a spell slot to play any of your locked Runes but not the Rune you played last round\n\nYou can also spend a spell slot to unlock one of your Runes permanently after defeating an opponent's Rune! (This does not apply to ties)\n\nThe game ends when one player is out of unlocked Runes or the game reaches it's round limit (default 7 rounds)"
    await ctx.send(embed=embed)


@client.command()
async def help(ctx):
    await helpmsg(ctx)


@client.command()
#Print Quick Reference Matrix
async def matrix(ctx):
    await ctx.message.delete()
    await ctx.send(file=discord.File('matrix.png'))


@client.event
#Incorrect Command Error Handling
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await helpmsg(ctx)
    raise error


@client.command()
#Start a New Game
async def mageorb(ctx, p1: discord.Member = client.user, p2: discord.Member = client.user, p1spsl : int = 3, p2spsl : int = 3, rounds : int = 7):
    chid = str(ctx.message.channel.id)
    gameRunning = False
    await ctx.message.delete()
    for each in gameinstances:
        if p1 == await gameinstances[each].getp1() or p1 == await gameinstances[each].getp2() or p2 == await gameinstances[each].getp1() or p2 == await gameinstances[each].getp2():
            gameRunning = True
    if chid in gameinstances:
        await ctx.send("There is already a game being played in this channel!")
    elif gameRunning:
        await ctx.send("Each player can only play in 1 game at a time!")
    else:
        gameinstances[chid] = moGame()
        await gameinstances[chid].run(ctx.message.channel.id, p1, p2, p1spsl, p2spsl, rounds)


@client.command()
#Concedes current game and cleans up
async def concede(ctx):
    chid = str(ctx.message.channel.id)
    await ctx.message.delete()
    if chid in gameinstances:
        p1 = await gameinstances[chid].getp1()
        p2 = await gameinstances[chid].getp2()
        if ctx.author == p1:
            await gameinstances[chid].clear(100)
            await gameinstances[chid].endgame()
            await ctx.send("<@" + str(p1.id) + "> has conceded! <@" + str(p2.id) + "> Wins!")
        elif ctx.author == p2:
            await gameinstances[chid].clear(100)
            await gameinstances[chid].endgame()
            await ctx.send("<@" + str(p2.id) + "> has conceded! <@" + str(p1.id) + "> Wins!")
        else:
            await ctx.send("You are not playing in the current game!")
    else:
        await ctx.send("There is no game running in this channel!")


class moGame:
    #New Game Setup
    p1 = discord.Member
    p2 = discord.Member
    chnl = discord.channel
    p1Runes = []
    p2Runes = []
    p1spsl = 0
    p2spsl = 0
    rounds = 0
    turn = discord.Member
    turncount = 0
    p1Lock = False
    p2Lock = False
    p1Unlock = False
    p2Unlock = False
    p1LastRune = ""
    p2LastRune = ""
    p1Turn = False
    p2Turn = False
    p1LockedRunes = []
    p2LockedRunes = []
    first = 0
    sumdes = ""
    roundes = ""

    async def getp1(self):
        return self.p1

    async def getp2(self):
        return self.p2

    async def run(self, channel, player1, player2, p1spsl, p2spsl, rounds):
        self.chnl = client.get_channel(channel)
        self.p1 = player1
        self.p2 = player2
        self.p1Runes = ["⚔", "🛡️", "💀", "🪞", "🔥"]
        self.p2Runes = ["⚔", "🛡️", "💀", "🪞", "🔥"]
        self.p1LockedRunes = []
        self.p2LockedRunes = []
        self.p1Lock = False
        self.p2Lock = False
        self.p1Unlock = False
        self.p2Unlock = False
        self.p1Turn = False
        self.p2Turn = False
        self.p1LastRune = ""
        self.p2LastRune = ""
        self.sumdes = ""
        self.roundes = ""
        self.turncount = 0
        self.turn = discord.Member
        self.p1spsl = p1spsl
        self.p2spsl = p2spsl
        self.rounds = rounds
        await self.clear(100)
        num = random.randint(1, 2)
        self.first = num
        embed = discord.Embed()
        embed.description = "<@" + str(player1.id) + "> has these runes " + " ".join(self.p1Runes) + " and " + str(
            p1spsl) + " spell slots remaining! \n \n <@" + str(player2.id) + "> has these runes " + " ".join(self.p2Runes) + " and " + str(
            p2spsl) + " spell slots remaining!"
        if num == 1:
            self.turn = player1
        else:
            self.turn = player2
        await self.chnl.send(embed=embed)
        await self.cast()
    #Print start of Game and add Reactions
    async def react(self):
        if self.p1 == self.turn:
            msg = await self.chnl.send("Attuned Runes: " + " ".join(self.p1Runes))
            for each in self.p1Runes:
                if each not in self.p1LastRune:
                    await msg.add_reaction(each)
            if len(self.p1Runes) < 5 and self.p1spsl > 0:
                msg = await self.chnl.send("Sealed Runes: " + " ".join(self.p1LockedRunes) + "\nSpell Slots Remaining: " + str(self.p1spsl))
                for each in self.p1LockedRunes:
                    if each not in self.p1LastRune:
                        await msg.add_reaction(each)
        else:
            msg = await self.chnl.send("Attuned Runes: " + " ".join(self.p2Runes))
            for each in self.p2Runes:
                if each not in self.p2LastRune:
                    await msg.add_reaction(each)
            if len(self.p2Runes) < 5 and self.p2spsl > 0:
                msg = await self.chnl.send("Sealed Runes: " + " ".join(self.p2LockedRunes) + "\nSpell Slots Remaining: " + str(self.p2spsl))
                for each in self.p2LockedRunes:
                    if each not in self.p2LastRune:
                        await msg.add_reaction(each)

    async def cast(self):
        #Handle Turns and Reaction Selection
        if self.turncount == 0:
            await self.chnl.send("<@" + str(self.turn.id) + "> cast your first Rune!")
        else:
            await self.chnl.send(embed=self.sumdes)
            await self.chnl.send("<@" + str(self.turn.id) + "> cast your next Rune!")
        await self.react()

        def check(reaction, m):
            if self.turn == self.p1:
                return m.id == self.turn.id and str(reaction.emoji) != self.p1LastRune and (str(reaction.emoji) == '⚔' or str(reaction.emoji) == '🛡️' or str(reaction.emoji) == '💀' or str(reaction.emoji) == '🪞' or str(reaction.emoji) == '🔥')
            else:
                return m.id == self.turn.id and str(reaction.emoji) != self.p2LastRune and (str(reaction.emoji) == '⚔' or str(reaction.emoji) == '🛡️' or str(reaction.emoji) == '💀' or str(reaction.emoji) == '🪞' or str(reaction.emoji) == '🔥')
        react, user = await client.wait_for('reaction_add', check=check)
        await react.message.delete()
        await self.clear(100)
        if self.turn == self.p1:
            self.p1Turn = True
            self.p1LastRune = str(react.emoji)
            if self.p1LastRune not in self.p1Runes:
                self.p1spsl -= 1
            if not self.p2Turn:
                self.turn = self.p2
                await self.cast()
            else:
                await self.resolve()
        else:
            self.p2Turn = True
            self.p2LastRune = str(react.emoji)
            if self.p2LastRune not in self.p2Runes:
                self.p2spsl -= 1
            if not self.p1Turn:
                self.turn = self.p1
                await self.cast()
            else:
                await self.resolve()

    async def resolve(self):
        #Logic to determine result
        if self.p1LastRune == "⚔":
            if self.p2LastRune == "💀" or self.p2LastRune == "🔥":
                self.p1Lock = True
            elif self.p2LastRune == "🛡️" or self.p2LastRune == "🪞":
                self.p2Lock = True
            else:
                self.p2Lock = True
                self.p1Lock = True
        elif self.p1LastRune == "🛡️":
            if self.p2LastRune == "⚔" or self.p2LastRune == "🪞":
                self.p1Lock = True
            elif self.p2LastRune == "🔥" or self.p2LastRune == "💀":
                self.p2Lock = True
            else:
                self.p2Unlock = True
                self.p1Unlock = True
        elif self.p1LastRune == "💀":
            if self.p2LastRune == "🛡️" or self.p2LastRune == "🪞":
                self.p1Lock = True
            elif self.p2LastRune == "⚔" or self.p2LastRune == "🔥":
                self.p2Lock = True
            else:
                self.p2Lock = True
                self.p1Lock = True
        elif self.p1LastRune == "🪞":
            if self.p2LastRune == "⚔" or self.p2LastRune == "🔥":
                self.p1Lock = True
            elif self.p2LastRune == "🛡️" or self.p2LastRune == "💀":
                self.p2Lock = True
            else:
                self.p2Unlock = True
                self.p1Unlock = True
        elif self.p1LastRune == "🔥":
            if self.p2LastRune == "🛡️" or self.p2LastRune == "💀":
                self.p1Lock = True
            elif self.p2LastRune == "⚔" or self.p2LastRune == "🪞":
                self.p2Lock = True
            else:
                self.p2Lock = True
                self.p1Lock = True
        # Display result and call lock or unlock
        embed = discord.Embed()
        embed.title = "Round " + str(self.turncount + 1) + " Results!!"
        embed.description = "<@" + str(self.p1.id) + "> casted the " + self.p1LastRune + " Rune!\n<@" + str(self.p2.id) + "> casted the " + self.p2LastRune + " Rune!\n\n<@" + str(self.p1.id) + "> has these runes " + " ".join(self.p1Runes) + " and " + str(
            self.p1spsl) + " spell slots remaining! \n \n <@" + str(self.p2.id) + "> has these runes " + " ".join(self.p2Runes) + " and " + str(
            self.p2spsl) + " spell slots remaining!"
        self.roundes = embed
        if self.p1Lock and self.p2Lock:
            await self.chnl.send(embed=embed)
            await self.chnl.send("Both players have played the " + self.p1LastRune + " Rune! \nYou may both lock one of your opponent's Runes!")
            await self.lock()
        elif self.p1Unlock and self.p2Unlock:
            await self.chnl.send(embed=embed)
            await self.chnl.send("Both players have played the " + self.p1LastRune + " Rune! \nYou may both unlock one of your Runes!")
            await self.unlock()
        elif self.p1Lock:
            embed.description = "<@" + str(self.p1.id) + ">'s " + self.p1LastRune + " Rune beats <@" + str(self.p2.id) + ">'s " + self.p2LastRune + " Rune!"
            await self.chnl.send(embed=embed)
            self.roundes = embed
            await self.lock()
        elif self.p2Lock:
            embed.description = "<@" + str(self.p2.id) + ">'s " + self.p2LastRune + " Rune beats <@" + str(
                self.p1.id) + ">'s " + self.p1LastRune + " Rune!"
            await self.chnl.send(embed=embed)
            self.roundes = embed
            await self.lock()

    async def lock(self):
        #Locks an Opponent's Rune and Handles end of Round Cleanup and Setup
        if self.p1Lock and self.p2Lock:
            msg = await self.chnl.send("You have these runes available: " + " ".join(self.p1Runes) + "\n<@" + str(self.p1.id) + "> choose one of your Opponent's Runes to Lock!")
            for each in self.p2Runes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p1.id and str(reaction.emoji) in self.p2Runes
            react, user = await client.wait_for('reaction_add', check=check)
            await react.message.delete()
            await self.clear(100)
            self.p1Lock = False
            for each in self.p2Runes:
                if str(react.emoji) == each:
                    self.p2Runes.remove(each)
                    self.p2LockedRunes.append(each)

            await self.chnl.send(embed=self.roundes)
            msg = await self.chnl.send("You have these runes available: " + " ".join(self.p2Runes) + "\n<@" + str(self.p2.id) + "> choose one of your Opponent's Runes to Lock!")
            for each in self.p1Runes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p2.id and str(reaction.emoji) in self.p1Runes
            react1, user = await client.wait_for('reaction_add', check=check)
            await react1.message.delete()
            await self.clear(100)
            await self.chnl.send("<@" + str(self.p1.id) + "> has locked <@" + str(self.p2.id) + ">'s " + str(react.emoji) + " Rune!")
            await self.chnl.send("<@" + str(self.p2.id) + "> has locked <@" + str(self.p1.id) + ">'s " + str(react1.emoji) + " Rune!")
            self.p2Lock = False
            for each in self.p1Runes:
                if str(react.emoji) == each:
                    self.p1Runes.remove(each)
                    self.p1LockedRunes.append(each)
            await self.isgameover()
        elif self.p1Lock:
            if len(self.p1Runes) < 5 and self.p1spsl > 0:
                mg = await self.chnl.send(
                    "<@" + str(self.p1.id) + "> would you like to spend a spell slot to unlock one of your runes?")
                await mg.add_reaction("👍")
                await mg.add_reaction("👎")

                def check(reaction, m):
                    return m.id == self.p1.id and (str(reaction.emoji) == "👎" or str(reaction.emoji) == "👍")
                react, user = await client.wait_for('reaction_add', check=check)
                await self.clear(100)
                if str(react.emoji) == "👍":
                    self.p1spsl -= 1
                    self.p1Unlock = True
                    await self.unlock()
                    await self.chnl.send(embed=self.roundes)
            msg = await self.chnl.send("You have these runes available: " + " ".join(self.p1Runes) + "\n<@" + str(self.p1.id) + "> choose one of your Opponent's Runes to Lock!")
            for each in self.p2Runes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p1.id and str(reaction.emoji) in self.p2Runes

            react, user = await client.wait_for('reaction_add', check=check)
            await self.clear(100)
            await self.chnl.send(
                "<@" + str(self.p1.id) + "> has locked <@" + str(self.p2.id) + ">'s " + str(react.emoji) + " Rune!")
            self.p1Lock = False
            for each in self.p2Runes:
                if str(react.emoji) == each:
                    self.p2Runes.remove(each)
                    self.p2LockedRunes.append(each)
            await self.isgameover()
        else:
            if len(self.p2Runes) < 5 and self.p2spsl > 0:
                mg = await self.chnl.send(
                    "<@" + str(self.p2.id) + "> would you like to spend a spell slot to unlock one of your runes?")
                await mg.add_reaction("👍")
                await mg.add_reaction("👎")

                def check(reaction, m):
                    return m.id == self.p2.id and (str(reaction.emoji) == "👎" or str(reaction.emoji) == "👍")

                react, user = await client.wait_for('reaction_add', check=check)
                await self.clear(100)
                if str(react.emoji) == "👍":
                    self.p2spsl -= 1
                    self.p2Unlock = True
                    await self.unlock()
                    await self.chnl.send(embed=self.roundes)
            msg = await self.chnl.send("You have these runes available: " + " ".join(self.p2Runes) + "\n<@" + str(self.p2.id) + "> choose one of your Opponent's Runes to Lock!")
            for each in self.p1Runes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p2.id and str(reaction.emoji) in self.p1Runes

            react, user = await client.wait_for('reaction_add', check=check)
            await self.clear(100)
            await self.chnl.send(
                "<@" + str(self.p2.id) + "> has locked <@" + str(self.p1.id) + ">'s " + str(react.emoji) + " Rune!")
            self.p2Lock = False
            for each in self.p1Runes:
                if str(react.emoji) == each:
                    self.p1Runes.remove(each)
                    self.p1LockedRunes.append(each)
            await self.isgameover()

    async def unlock(self):
        #Same as lock except unlocks one of winning player's Runes
        if self.p1Unlock and self.p2Unlock:
            if len(self.p1Runes) == 5:
                await self.chnl.send("<@" + str(self.p1.id) + "> you have no locked Runes!")
                self.p1Unlock = False
            else:
                self.p2Unlock = False
                await self.unlock()
            if len(self.p2Runes) == 5:
                await self.chnl.send("<@" + str(self.p2.id) + "> you have no locked Runes!")
                self.p2Unlock = False
            else:
                await self.chnl.send(embed=self.roundes)
                self.p2Unlock = True
                self.p1Unlock = False
                await self.unlock()
            await self.isgameover()
        elif self.p1Unlock:
            await self.chnl.send(embed=self.roundes)
            msg = await self.chnl.send("Your opponent has these runes available: " + " ".join(self.p2Runes) + "\n<@" + str(self.p1.id) + "> please choose one of your Runes to Unlock!")
            for each in self.p1LockedRunes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p1.id and str(reaction.emoji) in self.p1LockedRunes
            react, user = await client.wait_for('reaction_add', check=check)
            await react.message.delete()
            await self.clear(100)
            await self.chnl.send(
                "<@" + str(self.p1.id) + "> has unlocked their " + str(react.emoji) + " Rune!")
            self.p1Unlock = False
            for each in self.p1LockedRunes:
                if str(react.emoji) == each:
                    self.p1Runes.append(each)
                    self.p1LockedRunes.remove(each)
        else:
            await self.chnl.send(embed=self.roundes)
            msg = await self.chnl.send("Your opponent has these runes available: " + " ".join(self.p1Runes) + "\n<@" + str(self.p2.id) + "> please choose one of your Runes to Unlock!")
            for each in self.p2LockedRunes:
                await msg.add_reaction(each)

            def check(reaction, m):
                return m.id == self.p2.id and str(reaction.emoji) in self.p2LockedRunes

            react, user = await client.wait_for('reaction_add', check=check)
            await react.message.delete()
            await self.clear(100)
            await self.chnl.send(
                "<@" + str(self.p2.id) + "> has unlocked their " + str(react.emoji) + " Rune!")
            self.p2Unlock = False
            for each in self.p2LockedRunes:
                if str(react.emoji) == each:
                    self.p2Runes.append(each)
                    self.p2LockedRunes.remove(each)

    async def isgameover(self):
        #Determines if the Game has reached an end state and if so calls end of game and declares winner
        self.turncount += 1
        if len(self.p1Runes) == 0 or (len(self.p1Runes) == 1 and self.p1spsl < 1 and self.p1LastRune in self.p1Runes):
            await self.clear(100)
            await self.chnl.send("<@" + str(self.p1.id) + "> is out of castable Runes! <@" + str(self.p2.id) + "> Wins!!!")
            await self.endgame()
        elif len(self.p2Runes) == 0 or (len(self.p2Runes) == 1 and self.p2spsl < 1 and self.p2LastRune in self.p2Runes):
            await self.clear(100)
            await self.chnl.send(
                "<@" + str(self.p2.id) + "> is out of castable Runes! <@" + str(self.p1.id) + "> Wins!!!")
            await self.endgame()
        elif self.turncount >= self.rounds:
            await self.clear(100)
            await self.chnl.send("All " + str(self.rounds) + " have finished!!!!")
            if len(self.p1Runes) > len(self.p2Runes):
                await self.chnl.send("<@" + str(self.p1.id) + "> has more Runes left!\n<@" + str(self.p1.id) + "> has defeated <@" + str(self.p2.id) + ">!!!")
                await self.endgame()
            elif len(self.p2Runes) > len(self.p1Runes):
                await self.chnl.send("<@" + str(self.p2.id) + "> has more Runes left!\n<@" + str(self.p2.id) + "> has defeated <@" + str(self.p1.id) + ">!!!")
                await self.endgame()
            else:
                await self.chnl.send("<@" + str(self.p1.id) + "> and <@" + str(self.p2.id) + "> have the same number of Runes Remaining!\nIt's a Draw!!")
                await self.endgame()
        else:
            self.p1Turn = False
            self.p2Turn = False
            if self.first == 1:
                self.turn = self.p2
                self.first = 2
            else:
                self.turn = self.p1
                self.first = 1
            embed = discord.Embed()
            embed.title = "Round " + str(self.turncount + 1) + " of " + str(self.rounds) + "!!"
            embed.description = "<@" + str(self.p1.id) + "> has these runes " + " ".join(self.p1Runes) + " and " + str(
                self.p1spsl) + " spell slots remaining! \n \n <@" + str(self.p2.id) + "> has these runes " + " ".join(
                self.p2Runes) + " and " + str(
                self.p2spsl) + " spell slots remaining! \n \n Last Round <@" + str(self.p1.id) + "> cast the " + self.p1LastRune + " Rune and <@" + str(self.p2.id) + "> cast the " + self.p2LastRune + " Rune!"
            self.sumdes = embed
            await self.cast()

    async def clear(self, limit):
        #Clears messages that aren't end of game results
        def is_me(m):
            return m.author == client.user and "win" not in m.content.lower() and "defeated" not in m.content.lower() and "draw" not in m.content.lower()
        await self.chnl.purge(limit=limit, check=is_me)

    async def endgame(self):
        #Cleans up after a game ends
        del self.p1
        del self.p2
        del self.p1Runes
        del self.p2Runes
        del self.p1spsl
        del self.p2spsl
        del self.rounds
        del self.turn
        del self.turncount
        del self.p1Lock
        del self.p2Lock
        del self.p1Unlock
        del self.p2Unlock
        del self.p1LastRune
        del self.p2LastRune
        del self.p1Turn
        del self.p2Turn
        del self.p1LockedRunes
        del self.p2LockedRunes
        del self.first
        del self.sumdes
        del self.roundes
        channel = str(self.chnl.id)
        del self.chnl
        del gameinstances[channel]


client.run(TOKEN)