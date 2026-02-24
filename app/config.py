import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

    EMAIL_USER = os.getenv("EMAIL_USER", "jyothikrishnatunga@gmail.com")
    EMAIL_PASS = os.getenv("EMAIL_PASS", "atqn sdbk triq nokq")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root123")
    DB_NAME = os.getenv("DB_NAME", "website")
