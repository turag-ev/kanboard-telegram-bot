# Base image: Debian with current python 3 version installed
FROM python:3

# Run command in container to install dependencies
RUN pip install kanboard python-telegram-bot requests

# Current directory: Everything from now on happens there
WORKDIR /usr/src/app
# Copy python application into container (remember workdir!)
COPY . .

# Change config file path
RUN sed -i 's/^configFile.*$/configFile="\/var\/bot-data\/config.json"/g' bot.py

# Default command on container startup
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "./bot.py"]
