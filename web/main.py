import web
import model
import markdown
import pymongo
import json

conn = pymongo.Connection()

urls = (
    '/', 'Index',
    '/stats', 'Stats',
    '/(.*)', 'Index',
)


### Templates
t_globals = {
    'datestr': web.datestr,
    'markdown': markdown.markdown,
}
render = web.template.render('templates', base='base', globals=t_globals)


class Index:

    def GET(self):
        """ Show page """
        return "Hello, World!"


class Stats:

    def GET(self, url):
       	# db -> collections
		dbs = {
		       'raw' : ['commits', 'repos', 'users'],
		       'queue' : ['commits', 'repos', 'users'],
		       'processed' : ['commits']
		}
		retVal = ""
		for db, collections in dbs.iteritems():
		    for collection in collections:
		        count = conn[db][collection].count()
		        retVal += "%s.%s: %i" % (db, collection, count)
		return retVal


app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()