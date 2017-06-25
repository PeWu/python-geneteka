#!/usr/bin/python3

"""
Fetches data from the geneteka database (http://geneteka.genealodzy.pl)
"""

import math
import os
import requests
import sys
import time


OUTPUT_DIR = 'data_raw'


def getJson(voivodeship, recordType, parishId, page):
  """Fetches a page of results and writes the JSON results to a file."""
  url = (
      'http://www.geneteka.genealodzy.pl/api/getAct.php?'
      'bdm={}&w={}&rid={}&length=50&start={}'.format(
          recordType, voivodeship, parishId, page * 50))
  headers = {
    'Referer': 'http://www.geneteka.genealodzy.pl/index.php',
    'X-Requested-With': 'XMLHttpRequest',
  }
  response = requests.get(url, headers = headers)
  fileName = OUTPUT_DIR + '/{}_{}_{}_{}.json'.format(
      voivodeship, recordType, parishId, page)
  with open(fileName, 'w') as f:
    f.write(response.text)
  return response.json()


def fetchAll(voivodeship, recordType, parishId):
  """Fetches all pages for the given parish and record type."""
  print('Getting {}_{}_{} page 1/?'.format(
      voivodeship, recordType, parishId))
  result = getJson(voivodeship, recordType, parishId, 0)
  total = result['recordsTotal']
  totalPages = int(math.ceil(1.0 * int(total) / 50))
  for i in range(1, totalPages):
    print('Getting {}_{}_{} page {}/{}'.format(
        voivodeship, recordType, parishId, i + 1, totalPages))
    # Sleep not to overload the server with continuous load.
    time.sleep(2)
    getJson(voivodeship, recordType, parishId, i)


def main():
  if len(sys.argv) != 4:
    print('Usage: fetch.py <voivodeship_id> <record_type> <parish_id>')
    print('Example (Klembów births):')
    print('  fetch.py 07mz B 944')
    return

  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
  fetchAll(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
  main()
