import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgres://kxkiemgvbsmlyj:4f46995629632baf75e29ea130554cc7ca014b56063a580acb9779aaa166af92@ec2-3-87-180-131.compute-1.amazonaws.com:5432/d84jodtt3hs0v3'
SQLALCHEMY_TRACK_MODIFICATIONS  = False
