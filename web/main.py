import web
import logging
#import model
#import markdown
import pymongo
from pymongo.objectid import ObjectId
import json
from datetime import datetime
from sets import Set
logging.basicConfig(level=logging.INFO)

conn = pymongo.Connection()
db = conn.processed

urls = (
    '/', 'Index',
    '/stats', 'Stats',
    '/test', 'Test',
    '/query', 'Query',
)


render = web.template.render('templates/')


class DateEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime):
      return "new Date('%s')" % obj.ctime()
    elif isinstance(obj, ObjectId):
      return str(obj)
    else:
      return json.JSONEncoder.default(self, obj)


class Index:

    def GET(self):
        """ Show page """
        return "Hello, World!"

class Test:
    def GET(self):
        params = web.input()
        if params.has_key('name'):
            return "<h1>" + params.name + "</h1>"
        else:
            return "<h1> no name </h1>"

class Query:
  def GET(self):
    params = web.input()
    query = {}
    #logging.info(params.keys())
    if params.has_key('project'):
      query['project'] = params.project
    if params.has_key('lat_min') and params.has_key('lat_max'):
      query['lat'] = {"$gt" : float(params.lat_min), "$lt" : float(params.lat_max)}
    if params.has_key('long_max') and params.has_key('long_min'):
      query['long'] = {"$gt" : float(params.long_min), "$lt" : float(params.long_max)}
    if params.has_key('date_start') and params.has_key('date_end'):
      date_start = params.date_start.split('/')
      date_end = params.date_end.split('/')
      query['date'] = {"$gt" : datetime(int(date_start[2]), int(date_start[0]), int(date_start[1])), 
              "$lt" : datetime(int(date_end[2]), int(date_end[0]), int(date_end[1])) }
    #logging.info(query)
    cursor = db.commits.find(query)
    if params.has_key('sort') and params.sort == "1":
      cursor = cursor.sort("date", 1)
    results = {'links': [], 'locations': [], 'stats': {}}
    seen = set()
    locations = {}
    commit_count = 0
    author_count = 0
    for c in cursor:
      if (not c['sha1'] in seen) and c.has_key('lat') and c.has_key('long'):
        commit_count += 1
        geo = (c['lat'], c['long'])
        author = c['author']
        location = ''
        if 'location' in c:
          location = c['location']
        else:
          location = None

        if geo not in locations:
          locations[geo] = {'_locations': []}

        if author not in locations[geo]:
          if location: locations[geo]['_locations'].append(location)
          locations[geo][author] = True
          author_count += 1

        for p_sha1 in c['parents']:
          p = db.commits.find_one({'sha1': p_sha1})
          if p and p.has_key('lat') and p.has_key('long'):
            results['links'].append([c, p])
        seen.add(c['sha1'])

    for key, val in locations.iteritems():
      hash = {'lat': key[0], 'long': key[1]}
      hash['loc_count'] = max(len(val) - 1, 0)
      hash['authors'] = [e for e in val.keys() if e != '_locations']
      hash['locations'] = [loc for loc in Set(([e for e in val['_locations']]))]
      results['locations'].append(hash)

    results['stats']['commit_count'] = commit_count
    results['stats']['author_count'] = author_count

    return "jsonpcallback("+json.dumps(results, cls=DateEncoder)+")"

class Stats:
    def GET(self):
      # db -> collections
      dbs = {
            'raw' : ['commits', 'repos', 'users'],
            'queue' : ['commits', 'repos', 'users'],
            'processed' : ['commits']
      }
      return render.stats(conn,dbs)


app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
