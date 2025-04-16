import configparser
import os

# Create a config parser object to read the configuration file
config = configparser.ConfigParser()

# Read the configuration from 'config.ini' file
config.read('config.ini')

# OpenAI API configuration
OPENAI_API_KEY = config['Openai']['openai_key']  # Fetch API key for OpenAI
MODEL = config['Openai']['model']  # Fetch the model name (e.g., 'gpt-3.5-turbo')

# Database configuration
SERVER = config['Database']['server']  # Database server address
DATABASE_NAME = config['Database']['db']  # Name of the database
USERNAME = config['Database']['user']  # Database username
PASSWORD = config['Database']['pwd']  # Database password

# Security settings (for token validation, etc.)
SECRET_KEY = config['Security']['secret_key']  # Secret key for security
ALGORITHM = config['Security']['algorithm']  # Algorithm used for encoding/decoding tokens
