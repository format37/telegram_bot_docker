# Telegram bots python docker server
The server, for a list of telegram bots, with aiohttp and webhooks
#### installation
* git clone
* cd
* Link your domain name to ip of yor machine
* Make a cert files, as described in server/server.py and put them to server/ path
* Fill the token and ports in docker-compose.yml
* run:
```
sh compose.sh
```