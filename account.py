#
#
#
import json
from pathlib import Path
from save_path import SAVE_DIR

ACCOUNT_FILE =  SAVE_DIR / 'accounts.json'

def load_account():
    try:
        with open(ACCOUNT_FILE, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        ACCOUNT_FILE.write_text('{}', encoding='utf-8')
        return {}

def save_accounts(data):
    with open(ACCOUNT_FILE, 'w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

import hashlib
    
def verify_password(name, password):
    accounts = load_account()
    if name not in accounts.keys():
        return False   
    return accounts[name]['password'] == hashlib.sha256(password.encode()).hexdigest()

def register(name, password, points):
    accounts = load_account()
    
    accounts[name] = {'password': hashlib.sha256(password.encode()).hexdigest(),
                      'points': points,
                      'inventory':[]
                      }
    save_accounts(accounts)

def add_points(name, points):
    accounts = load_account()
    accounts[name]['points'] += points
    save_accounts(accounts)

def update_inventory(name, item):
    accounts = load_account()
    accounts[name]['inventory'].append(item)
    save_accounts(accounts)





        
    