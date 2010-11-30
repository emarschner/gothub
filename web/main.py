import web
#import model
#import markdown
import pymongo
import json

conn = pymongo.Connection()

urls = (
    '/', 'Index',
    '/stats', 'Stats',
    '/test', 'Test',
)


render = web.template.render('templates/')


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
