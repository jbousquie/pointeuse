#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04
# https://flask.palletsprojects.com/en/2.2.x/deploying/gunicorn/
# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3-fr

# https://stackoverflow.com/a/38223403/20111596

# pip install flask gunicorn 

import base64
import json
import time
import CasAuthenticator.cas_login
import CasAuthenticator.config
from flask import Flask, render_template, request


app = Flask(__name__)

BASEURL = 'https://filou.iut-rodez.fr/pointe/'

MAX_ATTEMPTS = 2
DELAY_INC = 0.5

@app.route('/generate_url', methods = ['POST'])
def generate_url():
    login = request.form.get('login')
    key = request.form.get('key')
    password = request.form.get('password')
    cryptokey = getCryptokey(login, key)
    enc_password = encode(cryptokey, password)
    generated_url = BASEURL + login + '/' + key + '/' + enc_password
    return render_template('index.html', generated_url=generated_url)

@app.route('/')
@app.route('/generate_url')
def index():
    generated_url = ''
    return render_template('index.html', generated_url=generated_url)

@app.route('/pointe/<login>/<key>/<encoded>')
def pointe(login, key, encoded):
    cryptokey = getCryptokey(login, key)
    password = decode(cryptokey, encoded)

    headers_punch = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
        }
    service = "https://ohris.ut-capitole.fr/fr/"
    action_url =  "https://ohris.ut-capitole.fr/fr/time/punch/add_virtual"

    msg = ''
    m = ''
    ca = CasAuthenticator.cas_login.CasAuthenticator()
    tgc = ca.get_tgc(login, password)
    if tgc == '':
        msg = "Erreur authentification CAS pour " + login
        return msg
    redirection_url = ca.get_redirection_url(service)

    # authentif service avec le ticket CAS
    sa =  CasAuthenticator.cas_login.ServiceAuthenticator(service)
    sa.getAuthenticatedService(redirection_url)
    if sa.status_code == 200:
        time.sleep(3.5)
        action = sa.execAction(action_url, headers_punch)
        if action.status_code == 200:
            json_msg = action.text
            try:
                obj_msg = json.loads(json_msg)
                if obj_msg['result']== "success":
                    m = 'Action réussie\n'
                enc_msg = obj_msg['message']
                msg = m + bytes(enc_msg, 'utf-8').decode()
            except ValueError as e:
                m = 'Erreur : décodage JSON impossible.\n'
                msg = m + json_msg 
        else:
            msg = 'Accès authentifié à Ohris OK, mais impossible de pointer'
    else:
        msg = 'Authentification CAS réussie, mais impossible d\'obtenir la page Ohris authentifée'
    
    print(msg)
    return msg 


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

def getCryptokey(login, key):
    mix = key + login
    return mix[0:8]

if __name__ == '__main__':
      app.run(host='0.0.0.0')



