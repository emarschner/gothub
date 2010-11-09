require 'rubygems'
require 'json'
data = JSON.parse(ARGF.read)
if data['commits']
  data['commits'].each do |commit|
    puts "#{commit['id']}: #{commit['author']['email']} #{commit['author']['login']}"
  end
end
