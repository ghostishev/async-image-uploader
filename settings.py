PORT = 80
DEBUG = False

MYSQL_HOST = 'localhost'
MYSQL_DATABASE = 'images'
MYSQL_LOGIN = 'root'
MYSQL_PASSWORD = 'root'
SELF_HOST = 'http://localhost:8000'

try:
    from settings_local import *
except ImportError:
    pass
