require 'rubygems'
require 'json'
data = JSON.parse(ARGF.read)
if data['repositories']
  data['repositories'].each do |repo|
    puts [repo['owner'], repo['name']].join('/')
  end
end
