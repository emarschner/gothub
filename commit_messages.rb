require 'rubygems'
require 'json'
data = JSON.parse(STDIN.read)
if data['commits']
  data['commits'].each do |commit|
    puts [commit['id'], commit['message']].join(': ')
  end
end
