FROM python:3.6
RUN pip install discord.py
COPY . /
CMD ["python","-u", "bot.py"]
