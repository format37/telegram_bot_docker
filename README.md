# Telegram bots python docker server
Docker server, for a list of telegram bots, with aiohttp and webhooks
#### installation
* Run
```
git clone https://github.com/format37/telegram_bot_docker.git
cd telegram_bot_docker
```
* Link your domain name to ip of yor machine
* Make a cert files, as described in server/server.py and put them to server/ path
* Fill the token and ports in docker-compose.yml
* Run
```
sh compose.sh
```