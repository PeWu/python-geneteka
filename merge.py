#!/usr/bin/python3

"""
Merges raw data from geneteka into larger json files.
"""

from collections import defaultdict
import html
import json
import os
import re


INPUT_DIR = 'data_raw'
OUTPUT_DIR = 'data'


def extractNotes(value):
  match = re.search(r'i.png" title="([^"]*)"', value)
  if match:
    return (value.split('<', 1)[0].strip(), match.group(1))
  return (value.strip(), None)


def convertPersonRecord(record):
  # Unparsed column with various information.
  stuff = record[9]

  lastName, lastNameNotes = extractNotes(record[3])
  motherLastName, motherLastNameNotes = extractNotes(record[6])

  output = {
    'year': record[0].strip(),
    'record_number': record[1].strip(),
    'first_name': record[2].strip(),
    'last_name': lastName,
    'father_first_name': record[4].strip(),
    'mother_first_name': record[5].strip(),
    'mother_last_name': motherLastName,
    'parish': record[7].strip(),
    'place': record[8].strip(),
    'stuff': stuff,
  }

  # Last name notes.
  if lastNameNotes:
    output['last_name_notes'] = lastNameNotes
  if motherLastNameNotes:
    output['mother_last_name_notes'] = motherLastNameNotes

  # List of notes.
  match = re.search(r'i.png" title="([^"]*)"', stuff)
  if match:
    output['notes'] = html.unescape(match.group(1)).strip().split('\r')

  # Where archives are kept.
  match = re.search(r'z.png" title="([^"]*)"', stuff)
  if match:
    output['archives'] = html.unescape(match.group(1)).strip()

  # URL to the place the archives are kept.
  match = re.search(r'href="([^"]*)" target', stuff)
  if match:
    output['archives_url'] = match.group(1)

  # URL to metryki.genealodzy.pl where scans can be found.
  match = re.search(r'href="([^"]*)">[^>]*s.png', stuff)
  if match:
    output['metryki_url'] = html.unescape(match.group(1))

  # User that entered this record to the database.
  match = re.search(r'uname=([^"]*)"', stuff)
  if match:
    output['user_entered'] = match.group(1)

  return output


def convertMarriageRecord(record):
  # Unparsed column with various information.
  stuff = record[9]

  husbandLastName, husbandLastNameNotes = extractNotes(record[3])
  wifeLastName, wifeLastNameNotes = extractNotes(record[6])

  output = {
    'year': record[0].strip(),
    'record_number': record[1].strip(),
    'husband_first_name': record[2].strip(),
    'husband_last_name': husbandLastName,
    'husband_parents': record[4].strip(),
    'wife_first_name': record[5].strip(),
    'wife_last_name': wifeLastName,
    'wife_parents': record[7].strip(),
    'parish': record[8].strip(),
    'stuff': stuff,
  }

  # Last name notes.
  if husbandLastNameNotes:
    output['nazwisko_meza_uwagi'] = husbandLastNameNotes
  if wifeLastNameNotes:
    output['nazwisko_zony_uwagi'] = wifeLastNameNotes

  # List of notes.
  match = re.search(r'i.png" title="([^"]*)"', stuff)
  if match:
    output['notes'] = html.unescape(match.group(1)).strip().split('\r')

  # Where archives are kept.
  match = re.search(r'z.png" title="([^"]*)"', stuff)
  if match:
    output['archives'] = html.unescape(match.group(1)).strip()

  # URL to the place the archives are kept.
  match = re.search(r'href="([^"]*)" target', stuff)
  if match:
    output['archives_url'] = match.group(1)

  # URL to metryki.genealodzy.pl where scans can be found.
  match = re.search(r'href="([^"]*)">[^>]*s.png', stuff)
  if match:
    output['metryki_url'] = match.group(1)

  # User that entered this record to the database.
  match = re.search(r'uname=([^"]*)"', stuff)
  if match:
    output['user_entered'] = match.group(1)

  return output


def main():
  # Map from prefix to list of records.
  data = defaultdict(list)

  # Read all files from INPUT_DIR.
  for fileName in os.listdir(INPUT_DIR):
    prefix = re.search('[^_]+_._[^_]+', fileName).group(0)
    with open(os.path.join(INPUT_DIR, fileName)) as file:
      content = json.load(file)
      data[prefix] += content['data']

  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

  # Parse records and write one parish per file.
  for key, value in data.items():
    voivodeship, recordType, parishId = key.split('_')
    if recordType == 'S':
      converter = convertMarriageRecord
    else:
      converter = convertPersonRecord
    value[:] = [converter(x) for x in value]

    print("Writing %s" % key)
    metadata = {
      'voivodeship': voivodeship,
      'record_type': recordType,
      'parish_id': parishId,
    }
    outputFile = os.path.join(OUTPUT_DIR, key + '.json')
    with open(outputFile, 'w') as file:
      outputData = {
        'data': value,
        'metadata': metadata,
      }
      json.dump(outputData, file)


if __name__ == "__main__":
  main()
