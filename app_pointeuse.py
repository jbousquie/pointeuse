#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04
# https://flask.palletsprojects.com/en/2.2.x/deploying/gunicorn/
# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3-fr

# https://stackoverflow.com/a/38223403/20111596

# pip install flask gunicorn 

import base64
from flask import Flask, render_template, request
app = Flask(__name__)

BASEURL = 'http://filou.iut-rodez.fr/pointe/'
CRYPTOKEY = 'ohris31'


@app.route('/generate_url', methods = ['POST'])
def generate_url():
    cryptokey = CRYPTOKEY
    login = request.form.get('login')
    password = request.form.get('password')
    #enc_login = encode(cryptokey, login)
    enc_password = encode(cryptokey, password)
    generated_url = BASEURL + login + '/' + enc_password
    return render_template('index.html', generated_url=generated_url)

@app.route('/')
def index():
    generated_url = ''
    return render_template('index.html', generated_url=generated_url)


def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()

def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
