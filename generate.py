#!/usr/bin/python3

"""
Matches birth, death and marriage records and writes one HTML file per
family, including spouses, children and links to other families.
"""

from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape
import glob
import itertools
import json
import os
import re
import urllib.parse


OUTPUT_DIR = "html"

def getPersonRecordId(record):
  """Returns a fairly unique person record identifier.
  
  May not be absolutely unique.
  """
  return "{}_{}_{}_{}_{}".format(
      record['year'],
      record['record_number'],
      record['parish'],
      record['first_name'],
      record['last_name'])


def getMarriageRecordId(record):
  """Returns a fairly unique marriage record identifier.
  
  May not be absolutely unique.
  """
  return "{}_{}_{}_{}_{}_{}".format(
    record['year'],
    record['record_number'],
    record['husband_first_name'],
    record['husband_last_name'],
    record['wife_first_name'],
    record['wife_last_name'])


def splitParents(parents):
  """Splits the input string into at most 3 parts:
  - father's first name
  - mother's first name
  - mother's last name.
  
  The input is in the format:
    "{father_first_name},{mother_first_name} {mother_last_name}"
  """
  split = parents.split(',', 1)
  if len(split) == 1:
    father = ''
    mother = parents
  else:
    father = split[0].strip()
    mother = split[1].strip()
  motherSplit = mother.rsplit(' ', 1)
  if not father:
    return motherSplit
  return [father] + motherSplit


def normalizeName(name):
  """Transforms a name to deal with common misspellings."""
  # Only use the first of several names.
  oneName = name.split(' ', 1)[0]
  REPLACEMENTS = [
    ['y$', 'a'],  # Szczęsny = Szczęsna
    ['i$', 'a'],  # Nowicki = Nowicka
    ['ę', 'e'],
    ['ą', 'a'],
    ['ó', 'o'],
    ['ł', 'l'],
    ['ś', 's'],
    ['ż', 'z'],
    ['ź', 'z'],
    ['ć', 'c'],
    ['ń', 'n'],
    ['rz', 'z'],  # rz == ż
    ['en', 'e'],  # en == ę
    ['em', 'e'],  # em == ę
    ['on', 'a'],  # on == ą
    ['om', 'a'],  # om == ą
    ['u', 'o'],  # u == ó
    ['x', 'ks'],  # x == ks
  ]
  for repl in REPLACEMENTS:
    oneName = re.sub(repl[0], repl[1], oneName)

  return oneName


def createToken(names):
  normalized = [normalizeName(name) for name in names]
  return '_'.join(normalized)


def getPersonToken(record):
  """Identifies the person from a person record."""
  return createToken([
    record['first_name'],
    record['last_name'],
    record['father_first_name'],
    record['mother_first_name'],
    record['mother_last_name']])


def getWifeToken(record):
  """Identifies the wife."""
  return createToken([
      record['wife_first_name'],
      record['wife_last_name']] +
      splitParents(record['wife_parents']))


def getHusbandToken(record):
  """Identifies the husband."""
  return createToken([
      record['husband_first_name'],
      record['husband_last_name']] +
      splitParents(record['husband_parents']))


def getParentsToken(record):
  """Identifies parents by their names."""
  return createToken([
      record['last_name'],
      record['father_first_name'],
      record['mother_first_name'],
      record['mother_last_name']])


def getSpousesToken(record):
  """Identifies a marriage by the spouses' names."""
  return createToken([
      record['husband_last_name'],
      record['husband_first_name'],
      record['wife_first_name'],
      record['wife_last_name']])


def getHusbandParentsToken(record):
  """Identifies husband's parents."""
  return createToken(
      [record['husband_last_name']] + splitParents(record['husband_parents']))


def getWifeParentsToken(record):
  """Identifies wife's parents."""
  return createToken(
      [record['wife_last_name']] + splitParents(record['wife_parents']))


def genetekaPersonUrl(record):
  """Generates URL to geneteka for a birth or death record."""
  return (
    'http://www.geneteka.genealodzy.pl/index.php?'
    'op=gt&lang=pol&w={}&rid={}&'
    'search_lastname={}&search_name={}&'
    'search_lastname2={}&search_name2={}&'
    'from_date={}&to_date={}&exac=1'.format(
        record['voivodeship'],
        record['parish_id'],
        record['last_name'],
        record['first_name'],
        record['mother_last_name'],
        record['mother_first_name'],
        record['year'],
        record['year']))


def genetekaMarriageUrl(record):
  """Generate URL to geneteka for a marriage record."""
  return (
    'http://www.geneteka.genealodzy.pl/index.php?'
    'op=gt&lang=pol&bdm=S&w={}&rid={}&'
    'search_lastname={}&search_name={}&'
    'search_lastname2={}&search_name2={}&'
    'from_date={}&to_date={}&'
    'exac=1&pair=1&parents=1'.format(
        record['voivodeship'],
        record['parish_id'],
        record['husband_last_name'],
        record['husband_first_name'],
        record['wife_last_name'],
        record['wife_first_name'],
        record['year'],
        record['year']))


def loadData(fileName):
  """Loads data from the given file."""
  print('Loading ' + fileName)
  with open(fileName) as f:
    inputData = json.load(f)
  data = inputData['data']
  metadata = inputData['metadata']
  for record in data:
    record.update(metadata)
  return data


def loadAllFiles(fileWildcard):
  """Loads all files for the given wildcard."""
  fileNames = glob.glob(fileWildcard)
  data = [loadData(fileName) for fileName in fileNames]
  return list(itertools.chain(*data))


def loadRecords(data):
  records = defaultdict(list)
  parentsToRecords = defaultdict(list)
  for record in data:
    records[getPersonToken(record)].append(record)
    parentsToRecords[getParentsToken(record)].append(record)
  return records, parentsToRecords


def nonEmptyValuesCount(map):
  """Returns the number of non-empty values in a map."""
  return len([x for x in map.values() if x])


def makeFileName(name):
  """Makes a string serve better as a file name."""
  return (name
          .encode('ascii', 'replace')
          .decode('ascii')
          .replace('?', '_'))


def getFamilyLinks(records, mapping, marriageRecords):
  families = set()
  for r in records:
    for f in mapping[getPersonRecordId(r)]:
      families.add(f)
  return [
    {'link': makeFileName(family), 'record': marriageRecords[family]}
    for family in families]


def getParentsLink(record):
  """Return structure used to display a link."""
  return {
    'link': makeFileName(getMarriageRecordId(record)),
    'record': record,
  }


def parseUserName(name):
  """Converts a URL-encoded username to string with special characters.
  
  Usernames in genealodzy.pl may contain Polish characters.
  """
  return urllib.parse.unquote(name, 'iso-8859-2')


def main():
  birthData = loadAllFiles('data/*_B_*.json')
  deathData = loadAllFiles('data/*D_*.json')
  marriageData = loadAllFiles('data/*_S_*.json')

  print("Processing")

  birthRecords, parentsToBirthRecords = loadRecords(birthData)
  deathRecords, parentsToDeathRecords = loadRecords(deathData)

  childToFamily = defaultdict(list)
  wifeToFamily = defaultdict(list)
  husbandToFamily = defaultdict(list)

  husbandParentsToChildMarriage = defaultdict(list)
  wifeParentsToChildMarriage = defaultdict(list)

  marriageRecords = {}

  # Read marriage records.
  for record in marriageData:
    husbandParentsToChildMarriage[getHusbandParentsToken(record)].append(record)
    wifeParentsToChildMarriage[getWifeParentsToken(record)].append(record)

    marriageRecordId = getMarriageRecordId(record)
    marriageRecords[marriageRecordId] = record

    spousesId = getSpousesToken(record)
    for child in parentsToBirthRecords[spousesId]:
      childToFamily[getPersonRecordId(child)].append(marriageRecordId)
    for child in parentsToDeathRecords[spousesId]:
      childToFamily[getPersonRecordId(child)].append(marriageRecordId)

    for h in birthRecords[getHusbandToken(record)]:
      husbandToFamily[getPersonRecordId(h)].append(marriageRecordId)
    for w in birthRecords[getWifeToken(record)]:
      wifeToFamily[getPersonRecordId(w)].append(marriageRecordId)

  # Links wife's parents to their marriage record (all possible records).
  wifeParentsToParentMarriage = defaultdict(list)
  # Links husband's parents to their marriage record (all possible records).
  husbandParentsToParentMarriage = defaultdict(list)

  for record in marriageData:
    parentsId = getSpousesToken(record)
    for fam in husbandParentsToChildMarriage[parentsId]:
      husbandParentsToParentMarriage[getMarriageRecordId(fam)].append(record)
    for fam in wifeParentsToChildMarriage[parentsId]:
      wifeParentsToParentMarriage[getMarriageRecordId(fam)].append(record)

  env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
  )
  familyTmpl = env.get_template('family.html')

  somethingMatched = {}

  print("Writing output")
  for record in marriageData:
    parentsId = getSpousesToken(record)
    childBirths = parentsToBirthRecords[parentsId]
    childDeaths = parentsToDeathRecords[parentsId]

    marriageRecordId = getMarriageRecordId(record)

    wives = birthRecords[getWifeToken(record)]
    husbands = birthRecords[getHusbandToken(record)]

    # Collect child births and deaths.
    # Note that if there are 2 children with the same first name, they will
    # be grouped together in one element.
    childEvents = defaultdict(list)
    for child in childBirths:
      childId = createToken([child['first_name']])
      childEvents[childId].append(child)
    for child in childDeaths:
      childId = createToken([child['first_name']])
      childEvents[childId].append(child)

    children = [{
        'first_name': events[0]['first_name'],
        'last_name': events[0]['last_name'],
        'events': sorted(events, key = lambda e: e['year']),
        'wives': getFamilyLinks(events, husbandToFamily, marriageRecords),
        'husbands': getFamilyLinks(events, wifeToFamily, marriageRecords),
      } for events in childEvents.values()]
    # Sort children by first event (most likely birth).
    children = sorted(children, key = lambda c: c['events'][0]['year'])

    # Find children by looking at marriage records.
    parentsId = getSpousesToken(record)
    for fam in husbandParentsToChildMarriage[parentsId]:
      personId = createToken([fam['husband_first_name']])
      if personId not in childEvents:
        children.append({
          'first_name': fam['husband_first_name'],
          'last_name': fam['husband_last_name'],
          'events': [],
          'wives': [{
            'link': makeFileName(getMarriageRecordId(fam)),
            'record': fam,
          }]
        })

    for fam in wifeParentsToChildMarriage[parentsId]:
      personId = createToken([fam['wife_first_name']])
      if personId not in childEvents:
        children.append({
          'first_name': fam['wife_first_name'],
          'last_name': fam['wife_last_name'],
          'events': [],
          'husbands': [{
            'link': makeFileName(getMarriageRecordId(fam)),
            'record': fam,
          }]
        })

    wifeParents = (
        getFamilyLinks(wives, childToFamily, marriageRecords) +
        [getParentsLink(x)
         for x in wifeParentsToParentMarriage[marriageRecordId]])
    husbandParents = (
        getFamilyLinks(husbands, childToFamily, marriageRecords) +
        [getParentsLink(x)
         for x in husbandParentsToParentMarriage[marriageRecordId]])

    # Remove duplicates.
    wifeParents = list({x['link']: x for x in wifeParents}.values())
    husbandParents = list({x['link']: x for x in husbandParents}.values())

    somethingMatched[marriageRecordId] = (
      husbands or wives or children or wifeParents or husbandParents)

    page = familyTmpl.render({
      'record': record,
      'husband': husbands,
      'wife': wives,
      'children': children,
      'wife_parents': wifeParents,
      'husband_parents': husbandParents,
      'genetekaPersonUrl': genetekaPersonUrl,
      'genetekaMarriageUrl': genetekaMarriageUrl,
      'parseUserName': parseUserName,
    })

    outputDir = os.path.join(OUTPUT_DIR, record['parish_id'])
    if not os.path.exists(outputDir):
      os.makedirs(outputDir)

    outputFileName = os.path.join(
        outputDir, makeFileName(marriageRecordId) + '.html')
    with open(outputFileName, 'w') as f:
      f.write(page)

  print("Writing indexes")

  # Index for each parish.
  parishes = defaultdict(list)
  for record in marriageData:
    parishes[record['parish_id']].append(record)
  parishIndexTmpl = env.get_template('parish_index.html')
  for parishId, records in parishes.items():
    # Sort index by year and record number.
    sortedRecords = sorted(
      records,
      key = lambda r: '{:0>4}{:0>4}'.format(r['year'], r['record_number']))
    parishIndexPage = parishIndexTmpl.render({
      'records': sortedRecords,
      'something_matched': somethingMatched,
      'getMarriageRecordId': getMarriageRecordId,
      'makeFileName': makeFileName,
    })
    outputFileName = os.path.join(OUTPUT_DIR, parishId + '.html')
    with open(outputFileName, 'w') as f:
      f.write(parishIndexPage)

  # List of parishes.
  parishes = [{
    'parish_id': parishId,
    'parish_name': records[0]['parish'],
    # TODO: Translate voivodeship ID to full name (07mz -> mazowieckie)
    'voivodeship': records[0]['voivodeship'],
  } for parishId, records in parishes.items()]
  parishes = sorted(parishes, key = lambda p: p['parish_name'])
  indexTmpl = env.get_template('index.html')
  indexPage = indexTmpl.render({
    'parishes': parishes,
  })
  outputFileName = os.path.join(OUTPUT_DIR, 'index.html')
  with open(outputFileName, 'w') as f:
    f.write(indexPage)



  print("Marriages:", len(marriageData))
  print("Births:   ", len(birthData))
  print("Deaths:   ", len(deathData))
  print("Matches:")
  print("  children: ", nonEmptyValuesCount(childToFamily))
  print(
      "  parents:  ",
      nonEmptyValuesCount(husbandParentsToParentMarriage) +
      nonEmptyValuesCount(wifeParentsToParentMarriage))
  print(
      "  spouses:  ",
      nonEmptyValuesCount(husbandToFamily) +
      nonEmptyValuesCount(wifeToFamily))


if __name__ == "__main__":
  main()
