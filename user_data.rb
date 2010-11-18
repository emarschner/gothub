require 'rubygems'
require 'json'
data = JSON.parse(STDIN.read)
type = data.keys[0]
if data[type]
  data[type].each do |user|
    if user.class == Hash
      puts [user['login'] || user['name'], user['location']].join(': ') unless user['location'].nil? or user['location'].empty?
    elsif user.class == String
      puts user
    end
  end
end
