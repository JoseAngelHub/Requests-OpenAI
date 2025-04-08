import configparser
import os

config = configparser.ConfigParser()

config.read('config.ini')

#openai apikey
OPENAI_API_KEY = config['Openai']['openai_key']
MODEL = config['Openai']['model']

# sql config
SERVER = config['Database']['server']
DATABASE_NAME = config['Database']['db']
USERNAME = config['Database']['user']
PASSWORD = config['Database']['pwd']
SECRET_KEY = config['Security']['secret_key']