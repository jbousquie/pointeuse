#!/usr/bin/python3
# -*- coding: utf-8 -*-

# APP 3 stand-alone


import base64
import json
import time
import sys
import requests
from datetime import timedelta
from bs4 import BeautifulSoup
from pprint import pp
from flask import Flask, render_template, request, make_response

sys.stdout.reconfigure(encoding='utf-8')


CAS_URL = 'https://sso.ut-capitole.fr/cas/login'
#REFERER = 'https://cas.ut-capitole.fr/cas/login'
REFERER = 'https://sso.ut-capitole.fr/'
ORIGIN = 'https://sso.ut-capitole.fr'

HOST = 'sso.ut-capitole.fr'
COOKIE_TGC = 'CASTGC='


GET_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br', 
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7', 
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': HOST
}

SERVICE_GET_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br', 
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7', 
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'orhis.ut-capitole.fr'
}



CAS_POST_HEADERS = {
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br', 
    'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3', 
    'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': HOST,
    'Origin': ORIGIN,
    'Referer': REFERER,
    }

SERVICE_POST_HEADERS = {
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br', 
    'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3', 
    'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0',
    'Connection': 'keep-alive',
    }

proxy = { 
    'http': 'http://cache.iut-rodez.fr:8080', 
    'https': 'http://cache.iut-rodez.fr:8080' 
    }



class ServiceAuthenticator:

    # constructeur
    def __init__(self, service):

        # Service parameters
        self.service = service
        self.service_session = requests.Session()
        self.service_headers = SERVICE_POST_HEADERS
        self.authenticated_response = ''
        self.status_code = 0

        # CAS parameters
        self.cas_session = self.service_session
        self.tgc = ''
        self.get_headers = GET_HEADERS
        self.post_headers = CAS_POST_HEADERS


    # Exécute l'action (GET) dans le service authentifié par CAS. Retourne l'objet Response à la requête https://service/action
    def execAction(self, action_url, action_headers):
        service_headers = self.service_headers
        
        # ajout des headers passés en paramètres au header initial
        for key in action_headers:
            service_headers[key] = action_headers[key]
            
        service_session = self.service_session
        action = service_session.get(action_url, headers=service_headers, allow_redirects=False, proxies=proxy)
        return action


    # Envoi requête formatée comme un browser
    def formattedGet(self, service, redirect):
        u = requests.utils.urlparse(service)
        service_headers = SERVICE_GET_HEADERS
        service_headers['Host'] = u.netloc
        service_headers['Referer'] = u.netloc
        service_session = self.service_session
        g_service = service_session.get(service, headers=service_headers, allow_redirects=redirect, proxies=proxy)
        return g_service


    # Méthodes pour CAS
    # Retourne la réponse à l'envoi du formulaire de saisie de crédentials.
    # Ce formulaire est dans le text de la réponse du paramètre g passé à auth_cas
    # g : réponse à la demande de chargement du formulaire d'authentification CAS
    def auth_cas(self, login, password, g):
  
        # récupération du formulaire fm1
        html_response = g.text
        data_soup = BeautifulSoup(html_response, 'lxml')
        form_tag = data_soup.find(id='fm1')
        form_action = form_tag.get('action')

        # récupération de tous les balises input hidden du formulaire et ajout des crédentials
        fields = {'username': login, 'password': password, 'submit': 'SE CONNECTER'}
        input_tags = form_tag.find_all('input', attrs={'type':'hidden'})
        for input_tag in input_tags:
            name = input_tag.get('name')
            value = input_tag.get('value')
            fields[name] = value

        # requête POST d'envoi des credentials
        post_url = ORIGIN + form_action
        post_headers = self.post_headers
        p = self.cas_session.post(post_url, data=fields, headers=post_headers, allow_redirects=False, proxies=proxy)
        return p




app = Flask(__name__)

BASEURL = 'https://filou.iut-rodez.fr/pointe/'


# Appli Web
@app.route('/generate_url', methods = ['POST'])
def generate_url():
    login = request.form.get('login')
    key = request.form.get('key')
    password = request.form.get('password')
    cryptokey = getCryptokey(login, key)
    enc_password = encode(cryptokey, password)
    generated_url = BASEURL + login + '/' + key + '/' + enc_password
    resp = make_response(render_template('index.html', generated_url=generated_url))
    resp.set_cookie('url', generated_url, max_age=timedelta(days=400))
    return resp

@app.route('/')
@app.route('/generate_url')
def index():
    generated_url = ''
    return render_template('index.html', generated_url=generated_url)

@app.route('/test')
def test():
    return render_template('test.txt')



@app.route('/pointe/<login>/<key>/<encoded>')
def pointe(login, key, encoded):
    cryptokey = getCryptokey(login, key)
    password = decode(cryptokey, encoded)

    headers_punch = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br', 
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7', 
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
        'Referer': 'https://ohris.ut-capitole.fr/fr/',
        'Host': 'ohris.ut-capitole.fr',
        'Connection': 'keep-alive'
        }
    service = "https://ohris.ut-capitole.fr/fr/"
    action_url =  "https://ohris.ut-capitole.fr/fr/time/punch/add_virtual"

    msg = ''
    m = ''
    sa = ServiceAuthenticator(service)
    # requête initiale pour obtenir la session Ohris et éviter des bugs de redirection chez Ohris
    ini_get = sa.formattedGet(service, True)     
    if ini_get.status_code != 200:
        msg = 'Ohris non redirigé sur CAS\n\n' + ini_get.url + '\nstatus ' + str(ini_get.status_code)
        print(msg)
        return msg
    print('Page d\'accueil Ohris redirige sur CAS : OK')

    # authentification CAS à partir de la réponse précédente
    # on attend un code de redirection 302 vers Ohris
    auth_cas = sa.auth_cas(login, password, ini_get)
    if auth_cas.status_code != 302:
        msg = 'Échec authentification CAS'
        print(msg)
        return msg
    print('Authentification CAS : OK')

    # Envoi du ST-CAS vers Orhis et obtention de la page d'accueil
    # time.sleep(1.5)
    st_tkt_url = auth_cas.headers['Location']           # extraction de l'URL de redirection contenant le ST
    auth_service = sa.formattedGet(st_tkt_url, True)          # requête vers Ohris avec le ST
    if auth_service.status_code != 200:
        msg = 'Échec d\'accès à la page authentifiée d\'Ohris'
        print(msg)
        return msg
    print('Page Ohris authentifiée CAS : OK')

    # envoi de la requête de pointage
    time.sleep(1)
    action = sa.execAction(action_url, headers_punch)
    msg = 'Authentification Ohris réussie, mais échec pointage'
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
    print(msg)
    return msg 


# Encodage
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