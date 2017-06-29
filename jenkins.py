import discord
import requests
import sys
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

args = sys.argv
args.remove("jenkins.py")

status = args[0]

colour = discord.Colour(0)

if status == "successful":
    colour = colour.green()
elif status == "unstable":
    colour = colour.yellow()
elif status == "failure":
    colour = colour.red()

embed = discord.Embed(colour=colour)

author = os.environ.get("GIT_COMMITER_NAME", "")
author_url = os.environ.get("GIT_COMMITER_URL", "")
icon_url = "https://github.com/" + author + ".png"

embed.set_author(name=author, url=author_url, icon_url=icon_url)

embed.set_footer(text="Build was " + status + ".")

json = {
    "content": "Here.",
    "username": "Jenkins",
    "avatar_url": "http://jenkins.pandentia.cf/static/745f737f/images/headshot.png",
    "embeds": [embed.to_dict()]
}

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

print(json)

resp = requests.post(WEBHOOK_URL, json=json)
