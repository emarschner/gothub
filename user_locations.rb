require 'rubygems'
require 'json'
key = ARGV[0] || 'users'
data = JSON.parse(STDIN.read)
if data[key]
  data[key].each do |user|
    puts [user['login'], user['location']].join(': ') unless user['location'].nil? or user['location'].empty?
  end
end
