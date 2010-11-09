require 'rubygems'
require 'json'
data = JSON.parse(ARGF.read)
if data['collaborators']
  data['collaborators'].each do |username|
    puts username
  end
end
