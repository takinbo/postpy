#!/usr/bin/env python
import sys
import re
from datetime import datetime
import csv
from BeautifulSoup import BeautifulSoup
import urllib2
from urllib import urlencode
from time import sleep

states = ['Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 
  'Bayelsa', 'Benue', 'Borno', 'Cross River', 'Delta', 'Ebonyi',
  'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo', 'Jigawa', 
  'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos', 
  'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau',
  'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara']

ua_header = {'User-Agent': 'Postpy/1.0 (takinbo at python dot org dot ng)' }

DEBUG = True

def debug(msg):
  if DEBUG: print msg.strip()

def parseLocations(html):
  soup = BeautifulSoup(html)
  locations = []
  if len(soup.select) > 1:
    for i in range(1, len(soup.select)):
      locations.append(soup.select.contents[i].text.strip())
  return locations

def parsePostcodes(html):
  soup = BeautifulSoup(html)
  results = None
  regexp = re.compile(r'Area:\s*(?P<area>.*)Postcode:\s*(?P<postcode>\d+)')
  try:
    search = regexp.search(soup.div.div.p.text)
    if search:
      results = {}
      results['area'] = search.group('area').strip()
      results['postcode'] = search.group('postcode').strip()
      results['streets'] = []
      
      # parse out the streets
      for street in soup.div.div.div.ul.findAll('li'):
        results['streets'].append(street.text.strip())
  except AttributeError:
    pass
  return results

def parseRuralPostcodes(html):
  soup = BeautifulSoup(html)
  results = None
  regexp = re.compile(r'District:\s*(?P<district>.*)Postcode:\s*(?P<postcode>\d+)')
  try:
    search = regexp.search(soup.div.div.p.text)
    if search:
      results = {}
      results['district'] = search.group('district').strip()
      results['postcode'] = search.group('postcode').strip()
      results['towns'] = []
      
      # parse out the streets
      for street in soup.div.div.div.ul.findAll('li'):
        results['towns'].append(street.text.strip())
  except AttributeError:
    pass
  return results

def getLocations(url, **kwargs):
  data = urlencode(kwargs)
  requrl = "%s?%s" % (url.strip("?"), data)
  req = urllib2.Request(requrl, headers=ua_header)
  return urllib2.urlopen(req).read()

# URBAN Locations
def getTowns(state):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxUrbanTown.php"
  return getLocations(url, state=state)

def getAreas(state, town):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxUrbanArea.php"
  return getLocations(url, state=state, town=town)

def getStreets(state, town, area):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxUrbanStreet.php"
  return getLocations(url, state=state, town=town, area=area)

def getPostcodeLocations(state, town, area, street):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxGetUrbanPostcode.php"
  return getLocations(url, state=state, town=town, area=area, street=street)

# RURAL Locations
def getLGAs(state):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxLGA.php"
  return getLocations(url, state=state)
  
def getDistricts(lga):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxDistrict.php"
  return getLocations(url, lga=lga)

def getRuralTowns(state, lga, district):
  url = "http://www.nigeriapostcodes.com/controllers/AjaxRuralTown.php"
  return getLocations(url, state=state, district=district, lga=lga)

def getRuralPostcodeLocations(state, lga, district, town):
  url = 'http://www.nigeriapostcodes.com/controllers/AjaxGetRuralPostcode.php'
  return getLocations(url, state=state, lga=lga, district=district, town=town)

if __name__ == '__main__':
  option = sys.argv[1] if len(sys.argv) > 1 else None
  start = datetime.now()  

  if (option == 'u'):
    postcodeWriter = csv.writer(open('postcodes.csv', 'w'))
    postcodeWriter.writerow(['postcode', 'street', 'area', 'town', 'state'])
    
    try:    
      # for each state, retrieve the towns
      for state in states:
        debug("Processing state: %s" % state)
        towns = parseLocations(getTowns(state))
        debug("...found %d towns." % len(towns))
        
        # now retrieve the areas in the town
        for town in towns:  
          areas = parseLocations(getAreas(state, town))
          debug("......found %d areas." % len(areas))
          
          # retrieve streets in the area
          for area in areas:
            streets = parseLocations(getStreets(state, town, area))
            debug('.........found %d streets.' % len(streets))
            
            # now get postcodes for listed streets, there might be some duplication
            for street in streets:
              postcodes = parsePostcodes(getPostcodeLocations(state, town, area, street))
              if postcodes:
                result_postcode = postcodes['postcode']
                result_area = postcodes['area']
                for result_street in postcodes['streets']:
                  postcodeWriter.writerow([result_postcode, result_street, result_area, town, state])
              sleep(1)
          
    except KeyboardInterrupt:
      pass
      
  elif option == 'r': #rural postcodes
    postcodeWriter = csv.writer(open('postcodes_rural.csv', 'w'))
    postcodeWriter.writerow(['postcode', 'town', 'district', 'lga', 'state'])
    
    try:    
      # for each state, retrieve the lgas
      for state in states:
        debug("Processing state: %s" % state)
        lgas = parseLocations(getLGAs(state))
        debug("...found %d lgas." % len(lgas))
        
        # now retrieve the districts in the lga
        for lga in lgas:  
          districts = parseLocations(getDistricts(lga))
          debug("......found %d districts." % len(districts))
          
          # retrieve towns in the district
          for district in districts:
            towns = parseLocations(getRuralTowns(state, lga, district))
            debug('.........found %d towns.' % len(towns))
            
            # now get postcodes for listed towns, there might be some duplication
            for town in towns:
              postcodes = parseRuralPostcodes(getRuralPostcodeLocations(state, lga, district, town))
              if postcodes:
                result_postcode = postcodes['postcode']
                result_district = postcodes['district']
                for result_town in postcodes['towns']:
                  postcodeWriter.writerow([result_postcode, result_town, result_district, lga, state])
              sleep(1)
          
    except KeyboardInterrupt:
      pass
      
  else:
    print 'Invocation: %s [u, r]' % sys.argv[0]
  
  stop = datetime.now()
  
  debug("Time elapsed: %s" % (stop - start))

