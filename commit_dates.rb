require 'rubygems'
require 'json'
data = JSON.parse(ARGF.read)
if data['commits']
  data['commits'].each do |commit|
    puts "#{commit['id']}: #{commit['committed_date']} #{commit['authored_date']}"
  end
end
