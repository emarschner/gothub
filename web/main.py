import web
import logging
#import model
#import markdown
import pymongo
from pymongo.objectid import ObjectId
import json
from datetime import datetime
logging.basicConfig(level=logging.INFO)

conn = pymongo.Connection()

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
		results = [res for res in conn.processed.commits.find(query)]
		return json.dumps(results, cls=DateEncoder)
		

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
