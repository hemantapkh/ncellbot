# Due to a bug in appleboy/ssh-action@master, some commands shows error and fails to execute.
# So, running a bash file instead of commands

echo $1 > /opt/ncell/ncellbot/config.json  && pkill -f telegrambot.py ; source /opt/ncell/ncellenv/bin/activate && screen -dm python3 /opt/ncell/ncellbot/telegrambot.py