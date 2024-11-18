import os
import time
from datetime import datetime, timezone

from flask import Flask, abort, json, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# selenium options
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--headless')

app = Flask(__name__)

@app.route("/datetime", methods=["GET"])
def get_datetime():
  curr_date = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
  curr_time = datetime.now(timezone.utc).strftime("%H:%M:%S")
  return jsonify({"date": curr_date, "time": curr_time})

@app.route("/calculator", methods=["POST"])
def calculate():
  try:
    data = json.loads(request.data) 
    if data["operator"] == "add":
      return jsonify(result=data["num1"] + data["num2"])
    elif data["operator"] == "subtract":
      return jsonify(result=data["num1"] - data["num2"])
    elif data["operator"] == "multiply":
      return jsonify(result=data["num1"] * data["num2"])
    elif data["operator"] == "divide":
      return jsonify(result=data["num1"] / data["num2"])
    else:
      abort(400, description="Invalid operator: " + data["operator"])
  except KeyError as e:
    abort(400, description="Missing value in request body: " + str(e))
  except Exception as e:
    abort(400, description="Error: " + str(e))

@app.route("/websearch", methods=["POST"])
def google_search():
  try:
    data = json.loads(request.data) 
    global driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com/")
    search_bar = driver.find_element(By.NAME, "q")
    search_bar.send_keys(data["query"])
    search_bar.send_keys(Keys.RETURN)
    time.sleep(1)

    search_results = driver.find_elements(By.CSS_SELECTOR, "div.kno-rdesc span span")
    if len(search_results) > 0:  # check if google quick answer box exists
      return jsonify(result=search_results[0].text)
    else:  # otherwise, find list of search results
      search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
      for result in search_results:
        try:  # first sentence of last span element in result
          first_result = result.find_elements(By.CSS_SELECTOR, "div.VwiC3b span")
          return jsonify(result=first_result[-1].text.split("...")[0])
        except IndexError:  # if no span element in result, go to next result
          pass
      return jsonify(result="No search results found")
  except KeyError as e:
    abort(400, description="Missing value in request body: " + str(e))
  except Exception as e:
    abort(400, description="Error: " + str(e))

@app.route("/", methods=["GET"])
def home():
  return "I'm alive"

def kill_vnc():
  # quit selenium and kill the vnc
  driver.quit()
  os.system("pkill -1 Xvnc")

def run():
  app.run(host="127.0.0.1", port=3000)

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)