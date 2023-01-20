"""
# bot_chaise.py v 1.7
# Written by WildPasta and NicoFgrx
# Purpose: roast people not present in class
"""

# Imports
import discord
import logging
import os
import re
import sys
import sqlite3

import module_db

from random import randint, choice
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

version = "1.7"
database="database.db"

def main():
    # Set up the logger
    logger = setup_logger()

    # Load the environment variables
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    discord_application_id = os.getenv('APPLICATION_ID')

    # Load the discord intents
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    # Set up the command prefix of the bot
    bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        print(f'Chaise v{version} bot has connected to Discord!')
        logger.info(f'Chaise v{version} bot has connected to Discord!')

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            logger.debug(f'{ctx.message.author} requested an early punchline')

            em = discord.Embed(title=f"Punchline en cours de rechargement!",description=f"Réessaye dans {error.retry_after:.2f}s.")
            await ctx.send(embed=em, delete_after=20.0)
            
    @bot.command(name="chaise")
    @commands.cooldown(1, 900, commands.BucketType.user)
    async def chaise(ctx, arg):
        dbSocket = sqlite3.connect(database)
        # Easter egg
        roll = randint(0, 100)
        easter_egg = False
        if roll <= 10:
            easter_egg = True
            response = "Combo x3 :eyes:"
            await ctx.send(response)
            for i in range(2):
                rand_sentence_label = module_db.sql_get_random_sentence()
                response = rand_sentence_label.replace('<pseudo>', arg)
                await ctx.send(response)

        # Check if a Discord ID is mentioned
        if re.match("\<\@\d+\>", arg):
            if not module_db.sql_new_chaise(arg, discord_application_id, easter_egg):
                response = "Et non, parce que ce mec n'est PAS FUN."
                await ctx.send(response)
                return 1

        logger.info(f'{ctx.message.author} request chaise for user {arg}')

        rand_sentence_label = module_db.sql_get_random_sentence()
        response = rand_sentence_label.replace('<pseudo>', arg)
        await ctx.send(response)

    @bot.command(name="top")
    async def top(ctx):
        logger.info(f'{ctx.message.author} request the top')
        result = module_db.sql_get_all_chaises()

        em = discord.Embed(title=f"Le top des chaises")
        for data in result:
            pseudo, chaised = data
            em.add_field(name=f"{chaised} chaises !", value=pseudo, inline=True)

        await ctx.send(embed=em)

    @bot.command(name="version")
    async def cmdVersion(ctx, arg=''):
        logger.debug(f'{ctx.message.author} request the version')
        await ctx.send(f'Actuellement en version {version}. Merci de ne plus me demander, c\'est que je me fais vieux...')

    @bot.command(name="history")
    async def history(ctx, arg=''):
        logger.info(f'{ctx.message.author} request the history')

        # Check if a Discord ID is mentioned
        if re.match("\<\@\d+\>", arg):
            limit = 3
            result = module_db.sql_get_history_by_id(arg, limit)
        else:
            limit = 5
            result = module_db.sql_get_history(limit)
 
        em = discord.Embed(title=f"Les dernières chaises")

        # If not history
        if len(result) > 0:
            for data in result:
                pseudo, date = data
                em.add_field(name=date, value=pseudo, inline=False)
            await ctx.send(embed=em)
        else:
            await ctx.send(f"Je suis FORMEL, il n'y a AUCUN historique pour {arg}")

    @bot.command(name="reset")
    async def reset(ctx):
        """
        Reset the chaise count in the database
        """
        
        if not author_is_admin(ctx.message.author):
            logger.info(f'{ctx.message.author} does not have required permission to request a reset')
            await ctx.send("Ptdr t ki ? Demande à un admin gamin !")
            return 0

        logger.info(f'{ctx.message.author} request a reset')

        dbSocket = sqlite3.connect(database)

        cursor = dbSocket.cursor()
        req = "UPDATE USERS SET chaised = 0"
        cursor.execute(req)
        dbSocket.commit()

        req = "DELETE FROM HISTORY WHERE 1"
        cursor.execute(req)
        dbSocket.commit()
        cursor.close()

        await ctx.send("Resetting database")

    @bot.command(name="unchaise")
    async def unchaise(ctx, arg):
        """
        Call sql_del_chaise function in module_db.py file
        Decrease chaised adn delete the last entry form history table
        """

        logger.info(f'<@{ctx.message.author.id}> request to unchaise {arg}')
        
        # Checking if the message contain a @user
        if re.match("\<\@\d+\>", arg):

            # Unchaise only if the user mentioned is not the one who send the message
            if int(re.findall(r"\d+", arg)[0]) != ctx.message.author.id:
                result = module_db.sql_del_chaise(arg, discord_application_id)
                
                if not result:
                    response = "T'essaies de me douiller là ?"
                    logger.debug(f'Can\'t unchaise {arg} because he has no history')
                else :
                    response = "Mouais, ça ira pour cette fois <pseudo>..."
                    response = response.replace('<pseudo>', arg)

            else:
                logger.info(f'{ctx.message.author} tried to unchaise himself, requested denied !')
                response = "Pas si vite, on demande aux copains si on peut faire ça !"
        else:
            logger.debug('Unchaise_request : Not valid discord id, request denied')
            response = "T'essaies de me douiller là ?"

        await ctx.send(response)

    @bot.command(name="add")
    async def add(ctx, arg):
        """
        Call the sql_insert_sentence function module
        Add the sentence in the sql PUNCH table
        """

        logger.info(f'{ctx.message.author} asked to add a sentence: {arg}')
        response = module_db.sql_insert_sentence(arg)
        await ctx.reply(response)

    @bot.command(name="adduser")
    async def adduser(ctx, arg):
        """
        Call the sql_adduser function module
        Add the discord id of the user in the USERS table
        """

        logger.info(f'{ctx.message.author} asked to add a user: {arg}')

        if not author_is_admin(ctx.message.author):
            logger.debug('Can\'t add a user because {ctx.message.author} is not admin')
            await ctx.send("Ptdr t ki ? Demande à un admin gamin !")
            return 1
        
        # If Discord ID is mentionned
        if not re.match("\<\@\d+\>", arg):
            logger.debug('Adduser syntax is not correct')
            await ctx.send("Usage : !adduser @NickName")
            return 1

        response = module_db.sql_adduser(arg, discord_application_id)
        await ctx.reply(response)
        return 0

    @bot.command(name="deluser")
    async def deluser(ctx, arg):
        """
        Call the sql_deluser function module
        Del the discord id of the user in the USERS table
        """

        logger.info(f'{ctx.message.author} asked to delete a user : {arg}')

        if not author_is_admin(ctx.message.author):
            logger.debug(f'Can\'t delete a user because {ctx.message.author} is not admin')
            await ctx.send("Ptdr t ki ? Demande à un admin gamin !")
            return 1

        # If Discord ID is mentionned
        if not re.match("\<\@\d+\>", arg):
            logger.debug('Deluser syntax is not correct')
            await ctx.send("Usage : !deluser @NickName")
            return 1

        response = module_db.sql_deluser(arg)
        await ctx.reply(response)
        return 0

    @bot.command(name="list")
    async def list(ctx):
        """
        Retrieve the sentences stored in database using module
        Print the retrieved sentences
        """

        logger.info(f'{ctx.message.author} asked to see sentences list')
        sentences = module_db.sql_get_sentences()

        # Check if there is sentence in database
        if len(sentences) == 0:
            logger.debug('List of sentences requested but database is empty')
            await ctx.send("Faut remplir la base ! Y'a rien là !")

        # If sentences are found, loop through them and print
        elif len(sentences) > 0:
            em = discord.Embed(title=f"Les punchlines ")
            for data in sentences:
                id, label = data
                em.add_field(name=id, value=label, inline=False)
            await ctx.send(embed=em)


    @bot.command(name="delete")
    async def delete(ctx, arg):
        """
        Verify that the user gives an int ID
        Delete the selected sentence from database 
        """

        logger.info(f'{ctx.message.author} asked to delete a sentence number {arg}')

        if not author_is_admin(ctx.message.author):
            logger.debug(f'Can\'t delete a sentence because {ctx.message.author} is not admin')
            await ctx.send("Ptdr t ki ? Demande à un admin gamin !")
            return 1
    
        if not arg.isnumeric():
            logger.debug('Can\'t delete a sentence because ID is not an int')
            await ctx.send("T'essaies de me douiller là ?")

        elif arg.isnumeric():
            response = module_db.sql_delete_sentence_by_id(int(arg))
            await ctx.send(response)
    
    @bot.command(name="help")
    async def help(ctx):
        """
        Send the command and their description
        """
        em = discord.Embed(title=f"Help command")

        logger.debug(f"{ctx.message.author} request help")
        
        em.add_field(name="!chaise @someone", value="Chaise someone that arrived late", inline=False)
        em.add_field(name="!unchaise @someone", value="Remove a chaise of someone", inline=False)
        em.add_field(name='!add "foo <pseudo> bar"', value="Add a sentence in the database", inline=False)
        em.add_field(name="!top", value="Display the leaderboard", inline=False)
        em.add_field(name="!version", value="Display the version", inline=False)
        em.add_field(name="!history", value="Show the last chaise, when someone is tagged, show the user history", inline=False)
        em.add_field(name="!list", value="List all the sentences in the database with their ID", inline=False)
        em.add_field(name="!delete sentence_id", value="Delete a sentence based on its ID", inline=False)
        em.add_field(name="!adduser @someone", value="Adding someone to the chaise game", inline=False)
        em.add_field(name="!deluser @someone", value="Deleting a user from the chaise game", inline=False)
        em.add_field(name="!reset", value="Reset the chaise count of everyone", inline=False)

        await ctx.send(embed=em)
    
    def author_is_admin(author):
        author_roles = [role.name for role in author.roles]
        if 'bot-admin' in author_roles:
            return True
        return False

    # Loop the bot
    bot.run(DISCORD_TOKEN)


def setup_logger():
    # Initialize logger
    logger = logging.getLogger(__name__)

    # Set up logger debug level
    logger.setLevel(logging.DEBUG)
    
    # Set up the format of the log file
    formatter = logging.Formatter('%(asctime)s %(name)s - %(levelname)s - %(message)s')

    # Set up file 
    file_handler = logging.FileHandler(('bot_chaise.log'))
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger    

if __name__ == "__main__":
    if not os.path.exists(database):
        module_db.sql_create_database()
    sys.exit(main())
