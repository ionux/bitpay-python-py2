import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'bitpay')))
from splinter import Browser
import time
import six
import json
from bitpay_client import Client
import bitpay_key_utils as key_utils

ROOT_ADDRESS = os.environ['RCROOTADDRESS']
USER_NAME = os.environ['RCTESTUSER']
PASSWORD = os.environ['RCTESTPASSWORD']
PEM = '-----BEGIN EC PRIVATE KEY-----\nMHQCAQEEICg7E4NN53YkaWuAwpoqjfAofjzKI7Jq1f532dX+0O6QoAcGBSuBBAAK\noUQDQgAEjZcNa6Kdz6GQwXcUD9iJ+t1tJZCx7hpqBuJV2/IrQBfue8jh8H7Q/4vX\nfAArmNMaGotTpjdnymWlMfszzXJhlw==\n-----END EC PRIVATE KEY-----\n'
client = Client()
invoice = None
exception = None

@given(u'the user pairs with BitPay with a valid pairing code')
def step_impl(context):
  claim_code = get_claim_code_from_server()
  global client
  client = Client(api_uri=ROOT_ADDRESS, insecure=True, pem=PEM)
  client.pair_pos_client(claim_code)
  assert client.tokens['pos']

@then(u'the user is paired with BitPay')
def step_impl(context):
  assert client.verify_tokens()

@given(u'the user fails to pair with a semantically {valid} code {code}')
def step_impl(context, code, valid):
  time.sleep(0.5)
  try: 
    client.pair_pos_client(code)
  except Exception as error:
    global exception
    exception = error

@when(u'the user fails to pair with BitPay because of an incorrect port')
def step_impl(context):
  time.sleep(0.5)
  badAddress = ROOT_ADDRESS.split(":")
  badAddress = badAddress[0] + ":" + badAddress[1] + ":999"
  newclient = Client(api_uri=badAddress, insecure=True)
  try:
    newclient.pair_pos_client("1a2C3d4")
    raise "That should totally not have worked"
  except Exception as error:
    global exception
    exception = error

@then(u'they will receive a {error} matching {message}')
def step_impl(context, error, message):
  assert exception.__class__.__name__ == error and exception.args[0] == message

@given(u'the user is authenticated with BitPay')
def step_impl(context):
  global client
  client = client_from_stored_values()
  assert client.verify_tokens()

@when(u'the user creates an invoice for {amount:f} {currency} with float input')
def step_impl(context, amount, currency):
  create_invoice(amount, currency)

@when(u'the user creates an invoice for {amount:d} {currency} with integer input')
def step_impl(context, amount, currency):
  create_invoice(amount, currency)

@when(u'the user creates an invoice for {amount} {currency} with string input')
def step_impl(context, amount, currency):
  if amount == '""':
    amount = ""
  if currency == '""':
    currency == ""
  create_invoice(amount, currency)

@then(u'they should recieve an invoice in response for {amount:g} {currency}')
def step_impl(context, amount, currency):
  global invoice
  assert invoice['price'] == amount and invoice['currency'] == currency

def create_invoice(amount, currency):
  global client
  global invoice
  try:
    token = client.tokens['pos']
    invoice = client.create_invoice({"price": amount, "currency": currency, "token": token })
  except Exception as error:
    global exception
    print(error.__class__.__name__)
    print(error.args[0])
    exception = error

def client_from_stored_values():
  for f in ["local.pem", "tokens.json"]:
    try:
      open("temp/" + f)
      exists = True
    except:
      exists = False
      break
  if exists:
    f = open("temp/local.pem", 'r')
    pem = f.read()
    f = open("temp/tokens.json", 'r')
    token = f.read()
    token = json.loads(token)
    client = Client(api_uri=ROOT_ADDRESS, insecure=True, pem=pem, tokens=token)
  else:
    claim_code = get_claim_code_from_server()
    pem = key_utils.generate_pem()
    client = Client(api_uri=ROOT_ADDRESS, insecure=True, pem=pem)
    token = json.dumps(client.pair_pos_client(claim_code))
    if not os.path.exists("temp"):
      os.makedirs("temp")
    f = open("temp/local.pem", 'w')
    f.write(pem)
    f = open("temp/tokens.json", 'w')
    f.write(token)
  return client

def get_claim_code_from_server():
  browser = Browser('phantomjs', service_args=['--ignore-ssl-errors=true'])
  browser.visit(ROOT_ADDRESS + "/merchant-login")
  browser.fill_form({"email": USER_NAME, "password": PASSWORD})
  browser.find_by_id("loginButton")[0].click()
  time.sleep(1)
  browser.visit(ROOT_ADDRESS + "/api-tokens")
  browser.find_by_css(".token-access-new-button").find_by_css(".btn").find_by_css(".icon-plus")[0].click()
  browser.find_by_id("token-new-form").find_by_css(".btn")[0].click()
  return browser.find_by_css(".token-claimcode")[0].html
  

