"""
# module_db.py v 1.7
# Written by WildPasta and NicoFgrx
# Purpose: Interact with chaise database
"""

# Imports
import bot_chaise

import datetime
import os
import re
import sqlite3

from random import randint

database="database.db"
logger = bot_chaise.setup_logger()


# USERS TABLE METHODS

def sql_adduser(id, discord_application_id):
    """
    Check if a valid discord id is provided
    Add it to the database if it does not exist
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    # Check if a Discord ID is mentioned
    if re.match("\<\@\d+\>", id):

        if id == f"<@{discord_application_id}>":
            return "T'essaies de me faire jouer à ton jeu de merde ?"

        try:

            chaised = sql_count_history(id)

            req = "INSERT INTO USERS VALUES ((?), (?), '')"
            data = [id, chaised]
            cursor.execute(req, data)
            dbSocket.commit()
            cursor.close()
            if chaised != 0: # if history not 0
                sql_new_chaise(id, 0, False)
                sql_new_chaise(id, 0, False)
                return "Quel plaisir de te revoir... Tiens, un petit cadeau pour ton retour :hap:"
            return "L'utilisateur a été ajouté !"
        except sqlite3.IntegrityError:
            return "L'utilisateur existe déjà !"
        except Exception as e:
            logger.info(f'Error when inserting user in database {e}')
            return "Attention je suis cassé..."
    else:
        return "Pour ajouter une personne, utiliser !adduser @NickName"

def sql_deluser(id):
    """
    Check if a valid discord id is provided
    Del it to the database with all his history
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()
    
    # Check if a Discord ID is mentioned
    if re.match("\<\@\d+\>", id):
        try:
            req = "DELETE FROM USERS WHERE id_discord=(?)"
            data = [id]
            cursor.execute(req, data)
            dbSocket.commit()
            cursor.close()
            return "L'utilisateur a été supprimé !"
        except Exception as e:
            print("ERROR : ", e)
            return "Attention je suis cassé..."
    else:
        return "Pour supprimer une personne, utiliser !deluser @NickName"

def sql_new_chaise(id,discord_application_id, easter_egg):
    """
    Check if a valid discord id is provided
    Increase number of chaised columns
    return values : 
        0 if insert chaised ok
        1 if user not in game
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    # Check if a Discord ID is mentioned
    if re.match("\<\@\d+\>", id):

        # check if users exists in USERS
        req = "SELECT id_discord FROM USERS WHERE id_discord = (?)"
        data = [str(id)]

        cursor.execute(req, data)
        dbSocket.commit()

        result = cursor.fetchone()

        logger.debug("result: {result}")

        if result == None:
            return False # if user not in game

        # If there was a combo, add three chaise
        if easter_egg == True:
            req = "UPDATE USERS SET chaised = chaised + 3 WHERE id_discord = (?)"
            easter_egg = False
        # If there was no combo, add one chaise
        else:
            req = "UPDATE USERS SET chaised = chaised + 1 WHERE id_discord = (?)"
        data = [str(id)]
        cursor.execute(req,data)
        cursor.close()
        dbSocket.commit()

        # Insert in history
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor = dbSocket.cursor()
        req = "INSERT INTO HISTORY (date, id_discord) VALUES ((?), (?))"
        data = [date, str(id)]
        cursor.execute(req,data)
        cursor.close()
        dbSocket.commit()

        return True

def sql_del_chaise(id, discord_application_id):
    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    # Retrieve the chaise count for a user
    req = "SELECT chaised FROM USERS WHERE id_discord = (?)"
    data = [str(id)]
    
    cursor.execute(req, data)
    dbSocket.commit()

    nb_chaise = cursor.fetchone()[0]

    # Check if chaise count is 0
    if nb_chaise == 0:
        return False

    # Decrease chaise count by 1
    req = "UPDATE USERS SET chaised = chaised - 1 WHERE id_discord = (?)"
    data = [str(id)]
    cursor.execute(req, data)
    dbSocket.commit()

    # Get the last chaise of the user
    req = "SELECT id_history FROM HISTORY WHERE id_discord = (?) ORDER BY date DESC LIMIT 1"
    cursor.execute(req, data)
    dbSocket.commit()

    # Delete the last chaise from users history
    id_history = cursor.fetchone()[0]
    req = "DELETE FROM HISTORY WHERE id_history = (?)"
    data = [id_history]
    
    # Send the request and close the cursor
    cursor.execute(req, data)
    dbSocket.commit()   
    cursor.close()

    return True

def sql_get_all_chaises():
    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()
    req = "SELECT id_discord, chaised FROM USERS ORDER BY chaised DESC"
    cursor.execute(req)
    dbSocket.commit()
    result = cursor.fetchall()
    cursor.close()  

    return result  


def sql_count_history(id):

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    # count how many row in history the user have
    req = "SELECT COUNT(id_history) FROM HISTORY WHERE id_discord=(?)"
    data = [id]

    cursor.execute(req, data)
    dbSocket.commit()

    result = cursor.fetchone()[0]

    # if user has history
    if result != 0:
        return result
    
    return 0


# PUNCH TABLE METHODS
def sql_delete_sentence_by_id(id):
    """
    Retrieve the sentences ID
    Delete the selected ID
    Return a status message
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    # Check ID is in database
    req = "SELECT id FROM PUNCH"
    cursor.execute(req)
    dbSocket.commit()
    data = cursor.fetchall()

    if (id,) not in data:
        return "Invalid ID"


    req = "SELECT label FROM PUNCH WHERE id = (?)"
    data = [id]

    cursor.execute(req, data)
    dbSocket.commit()

    sentence = cursor.fetchone()[0]

    # delete in sentences.sql
    to_delete = 'INSERT INTO PUNCH (label) VALUES("{}");'.format(sentence)
    logger.debug("sentence to delete: {to_delete}")

    with open("sentences.sql", "r") as f:
        lines = f.readlines()
    with open("sentences.sql", "w") as f:
        for line in lines:
            if line.strip("\n") != to_delete:
                f.write(line)

    
    # delete in database
    req = "DELETE FROM PUNCH WHERE id == (?)"
    data = [id]

    cursor.execute(req, data)
    dbSocket.commit()

    # Print a response
    return "La phrase {} a été supprimée de la base :)".format(id)


def sql_get_random_sentence():
    """
    Generate a random integer
    Fetch a random sentence
    Return the text of the sentence
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    req_nb_sentence = "SELECT COUNT(id) FROM PUNCH"        
    cursor.execute(req_nb_sentence)
    dbSocket.commit()
    nb_sentence = cursor.fetchone()[0]

    logger.debug("get random sentence: {nb_sentence}")

    # Get a random sentence
    rand_sentence_id = randint(1, nb_sentence)

    req_rand_sentence = "SELECT label FROM PUNCH WHERE id = (?)"    
    data = [rand_sentence_id]    
    cursor.execute(req_rand_sentence, data)
    dbSocket.commit()
    rand_sentence_label = cursor.fetchone()[0]
    cursor.close()

    return rand_sentence_label

def sql_insert_sentence(custom_sentence):
    """
    Check if the given sentence is valid
    Insert the sentence in SQL database
    """

    # Check if the sentence is valid
    if "<pseudo>" not in custom_sentence:
        return "Il te manque <pseudo> dans ta phrase, ou peut-être as-tu oublié les \" !"

    # Insertion en base de données
    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    req = "INSERT INTO PUNCH (label) VALUES( (?) )"
    data = [custom_sentence]

    cursor.execute(req, data)
    dbSocket.commit()
    cursor.close()

    # Ajoute la phrase dans le fichier SQL pour reconstruire la base en cas de corruption/suppression
    line = '\nINSERT INTO PUNCH (label) VALUES("{}");'

    with open("sentences.sql", 'a') as file:
        file.write(line.format(custom_sentence))

    return 'Lezzgo ! Ta phrase : "{}" vient de s\'ajouter dans la base !'.format(custom_sentence)


def sql_get_sentences():
    """
    Retrieve a sentence with a given ID from the database
    """

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    req  = "SELECT id, label FROM PUNCH"
    
    cursor.execute(req)
    dbSocket.commit()
    data = cursor.fetchall()

    return data

# HISTORY Table Methods
def sql_get_history(limit):
    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    req = "SELECT id_discord, date FROM HISTORY ORDER BY date DESC LIMIT (?)"
    data = [limit]
    cursor.execute(req, data)
    dbSocket.commit()
    result = cursor.fetchall()
    cursor.close()

    return result

def sql_get_history_by_id(id, limit):
    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    req = "SELECT id_discord, date FROM HISTORY WHERE id_discord = (?) ORDER BY date DESC LIMIT (?)" 
    data = [str(id), limit]
    cursor.execute(req, data)
    dbSocket.commit()
    result = cursor.fetchall()
    cursor.close()

    return result


# MISC

def sql_create_database():
    """
    Build a database using the SQL file
    """

    tables_sql = "create.sql"
    sentences_sql = "sentences.sql"

    # check if files exists
    if not os.path.exists(tables_sql) and not os.path.exists(sentences_sql):
        logger.debug("missing .sql files")
        exit(1)

    dbSocket = sqlite3.connect(database)
    cursor = dbSocket.cursor()

    logger.debug("SQL files are OK")

    with open(tables_sql, 'r') as file:
        req = ""
        for line in file:
            req += line
        cursor.executescript(req)
        dbSocket.commit()

    logger.debug("Tables are created")

    with open(sentences_sql, 'r') as file:
        req = ""
        for line in file:
            req += line
        cursor.executescript(req)
        dbSocket.commit()

    logger.debug("Inserted sentences values")

    cursor.close()
