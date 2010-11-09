require 'rubygems'
require 'json'
data = JSON.parse(ARGF.read)
if data['commits']
  data['commits'].each do |commit|
    puts "#{commit['id']}: #{commit['parents'].map{|parent| parent['id']}.join(' ')}"
  end
end
