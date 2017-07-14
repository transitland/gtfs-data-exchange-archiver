import subprocess
import urllib
import urllib2
import json
import os
import argparse

def makedirs(path):
  if os.path.exists(path):
    return
  os.makedirs(path)

def get_agencies(filename='agencies.json', cache=False):
  """Get list of agencies."""
  url = 'http://www.gtfs-data-exchange.com/api/agencies'
  if os.path.exists(filename) and cache:
    print "Cached agencies..."
    with open(filename) as f:
      data = json.load(f)
  else:
    print "Getting agencies:", url
    response = urllib2.urlopen(url)
    data = json.load(response)
    with open('agencies.json', 'w') as f:
      json.dump(data, f)
  return data

def get_agency(agency, filename=None, cache=False):
  """Get detailed information about an agency's feeds."""
  filename = filename or os.path.join(agency, '%s.json'%agency)
  url = 'http://www.gtfs-data-exchange.com/api/agency?agency=%s'%agency
  if os.path.exists(filename) and cache:
    print "Cached agency:", agency
    with open(filename) as f:
      data = json.load(f)
  else:
    print "Fetching agency:", url
    response = urllib2.urlopen(url)
    data  = json.load(response)
    makedirs(agency)
    with open(filename, 'w') as f:
      json.dump(data, f)
  return data

def get_gtfs(agency, fetch):
  """Download a single feed from an agency."""
  if not fetch.get('filename') or not fetch.get('file_url'):
    print "Feed reference incomplete!:", fetch
    return
  makedirs(agency)
  filename = os.path.join(agency, fetch['filename'])
  if os.path.exists(filename) and os.stat(filename).st_size == fetch['size']:
    print "Existing, skipping:", fetch['file_url']
  else:
    print "Downloading:", fetch['file_url']
    urllib.urlretrieve(fetch['file_url'], filename)
    print "Done"

def check_agency(agency):
  """Check that an agency has a valid set of GTFS feeds."""
  return ('data' in agency) and ('datafiles' in agency['data']) and (agency['data']['datafiles'])

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='GTFS Data Exchange Download')
  parser.add_argument('--current', help='Only fetch most recent feed', action='store_true')
  parser.add_argument('--cache', help='Enable cached API responses.', action='store_true')
  parser.add_argument('--debug', help='Debug', action='store_true')
  parser.add_argument('agencies', metavar='N', type=str, nargs='+', help='agency ids')
  args = parser.parse_args()

  agencies = get_agencies(cache=args.cache)
  agencies['data'] = filter(lambda x:x.get('is_official'), agencies['data'])
  agencies['data'] = sorted(agencies['data'], key=lambda x:x.get('dataexchange_id'))
  for agency in agencies['data']:
    dxid = agency.get('dataexchange_id')
    if args.agencies and dxid not in args.agencies:
      continue

    agency_data = get_agency(dxid, cache=args.cache)
    if check_agency(agency_data):
      # Sort by date added.
      datafiles = sorted(agency_data['data']['datafiles'], key=lambda x:x.get('date_added'))
      # Download all GTFS feeds.
      if args.current:
        datafiles = datafiles[-1:]
      for fetch in datafiles:
        get_gtfs(dxid, fetch)
      # Remove current current.zip symlink.
      try:
        os.unlink(os.path.join(dxid, 'current.zip'))
      except:
        pass
      # Create new current.zip symlink.
      last = datafiles[-1]
      # Don't want to use chdir, grumble..
      subprocess.check_output(['ln','-s',last['filename'], 'current.zip'], cwd=os.path.join(dxid))
