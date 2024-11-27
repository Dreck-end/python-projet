import telebot
import os
import time
import random
import threading

# Informations sensibles
token = "7352479184:AAE7hk7VJq322guiC2ckYSw2H9mPgzrZmGk"  # Remplacez par le jeton de votre bot
owner_id = int("5172989618")  # ID du propriétaire (remplacez par le vôtre)

# Variables de gestion des groupes et identifiants
group_ids = {}  # Dictionnaire pour stocker les informations des groupes (ID réel : nom)
group_messages = {}  # Dictionnaire pour stocker les messages spécifiques à chaque groupe
current_group_id = None  # ID du groupe sélectionné pour configuration
current_message = ""  # Message à publier
publish_interval = 7200  # Intervalle de publication par défaut en secondes (2 heures)
threads = {}  # Threads de publication par groupe

bot = telebot.TeleBot(token)
bot.send_message(owner_id, 'Le bot a redémarré')

# Fonction pour envoyer un fichier (photo ou document) dans un groupe
def send(group_id):
    """
    Envoie une photo et un document dans un groupe spécifique.
    """
    file_name = f'temp/{os.listdir("temp")[0]}'
    try:
        with open(file_name, 'rb') as photo:
            bot.send_photo(group_id, photo)
        with open(file_name, 'rb') as photo:
            bot.send_document(group_id, photo)
        os.remove(file_name)
        return True
    except Exception as e:
        bot.send_message(owner_id, f"Erreur d'envoi :\n\n{e}", disable_notification=True)
        return False

# Fonction pour récupérer un message aléatoire
def get_random_message():
    try:
        with open("messages.txt", "r", encoding="utf-8") as file:
            messages = [line.strip() for line in file if line.strip()]
        return random.choice(messages) if messages else "Aucun message défini."
    except FileNotFoundError:
        return "Fichier 'messages.txt' introuvable. Veuillez le créer et ajouter des messages."

# Gestion des nouveaux groupes où le bot est ajouté
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_group(message):
    new_members = message.new_chat_members
    for new_member in new_members:
        if new_member.id == bot.get_me().id:  # Vérifier si le bot est ajouté
            group_name = message.chat.title
            group_id = message.chat.id  # Utiliser l'ID réel du groupe
            if group_id not in group_ids:
                group_ids[group_id] = group_name  # Associe l'ID du groupe au nom du groupe
                bot.send_message(owner_id, f"Le bot a été ajouté au groupe : {group_name}.\nIdentifiant du groupe (Telegram) : {group_id}")
            else:
                bot.send_message(owner_id, f"Le bot est déjà enregistré dans le groupe : {group_name}.")

# Commande pour afficher la liste des groupes et leurs identifiants
@bot.message_handler(commands=['list'])
def list_groups(message):
    if str(message.chat.id) == str(owner_id):
        if group_ids:
            group_list = "\n".join([f"{group_name} (ID: {group_id})" for group_id, group_name in group_ids.items()])
            bot.send_message(owner_id, f"Voici la liste des groupes où le bot est présent :\n{group_list}")
        else:
            bot.send_message(owner_id, "Le bot n'est dans aucun groupe pour le moment.")

# Commande pour afficher la liste des groupes et leurs identifiants pour auto_publish
@bot.message_handler(commands=['auto_publish'])
def show_group_list(message):
    if str(message.chat.id) == str(owner_id):
        if group_ids:
            group_list = "\n".join([f"ID {group_id}: {group_name}" for group_id, group_name in group_ids.items()])
            bot.send_message(owner_id, f"Voici la liste des groupes où le bot est présent :\n{group_list}")
            bot.send_message(owner_id, "Veuillez maintenant envoyer l'ID du groupe où vous souhaitez publier.")
        else:
            bot.send_message(owner_id, "Le bot n'est dans aucun groupe pour le moment.")

# Recevoir l'ID du groupe et demander le message à publier
@bot.message_handler(func=lambda message: current_group_id is None and str(message.chat.id) == str(owner_id))
def receive_group_id(message):
    global current_group_id
    try:
        group_id = int(message.text.strip())
        if group_id in group_ids:
            current_group_id = group_id
            group_name = group_ids[group_id]
            bot.send_message(owner_id, f"Vous avez sélectionné le groupe '{group_name}' (ID: {group_id}).")
            bot.send_message(owner_id, "Veuillez maintenant envoyer le message que vous souhaitez publier dans ce groupe.")
        else:
            bot.send_message(owner_id, "ID de groupe invalide. Veuillez envoyer un ID valide.")
    except ValueError:
        bot.send_message(owner_id, "Veuillez envoyer un ID de groupe valide.")

# Recevoir le message à publier et demander l'intervalle
@bot.message_handler(func=lambda message: current_group_id is not None and current_message == "")
def receive_message_to_publish(message):
    global current_message
    current_message = message.text.strip()
    group_messages[current_group_id] = current_message  # Associe le message au groupe
    bot.send_message(owner_id, "Message enregistré. Veuillez maintenant spécifier l'intervalle de publication (en minutes).")

# Recevoir l'intervalle de publication et démarrer la tâche
@bot.message_handler(func=lambda message: current_message != "" and current_group_id is not None)
def receive_publish_interval(message):
    global publish_interval, current_group_id, current_message
    try:
        interval_minutes = int(message.text.strip())
        publish_interval = interval_minutes * 60

        # Démarrer la publication automatique pour le groupe
        if current_group_id not in threads:
            threads[current_group_id] = threading.Thread(
                target=auto_publish, args=(current_group_id,), daemon=True
            )
            threads[current_group_id].start()
            bot.send_message(owner_id, f"Publication automatique activée pour le groupe {group_ids[current_group_id]} toutes les {interval_minutes} minutes.")
        else:
            bot.send_message(owner_id, "La publication automatique est déjà activée pour ce groupe.")

        # Réinitialiser les variables temporaires
        current_group_id = None
        current_message = ""
    except ValueError:
        bot.send_message(owner_id, "Intervalle invalide. Veuillez réessayer.")

# Fonction de publication automatique
def auto_publish(group_id):
    while True:
        time.sleep(publish_interval)
        if group_id in group_messages:
            bot.send_message(group_id, group_messages[group_id])

if __name__ == '__main__':
    bot.polling(none_stop=True)
