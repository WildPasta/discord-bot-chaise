FROM python:3.9

LABEL version="1.8.1"
LABEL repository="https://github.com/WildPasta/discord_bot_chaise"
LABEL maintainer="WildPasta <chauve.richard@protonmail.com>"

ENV DIR=/home/discord_bot_chaise/
WORKDIR $DIR
ADD *.sql *.py $DIR
ADD requirements.txt $DIR

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "bot_chaise.py"]
