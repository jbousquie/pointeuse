#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-20-04

from app_pointeuse import app

if __name__ == "__main__":
    app.run()