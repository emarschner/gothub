require 'rubygems'
require 'csv'

username = ARGV[0]
reponame = ARGV[1]
branchname = ARGV[2]
commit = ARGV[3]

RUN_DIR = File.dirname(__FILE__)

def user2geocode(username)
  File.read("#{RUN_DIR}/log/user/geocode/#{username}")
end

def commit2geocode(commit)
  user2geocode(File.read("#{RUN_DIR}/log/user/email/#{File.read(File.read("#{RUN_DIR}/log/commits/author/#{commit}").split('/')[-1])}"))
end

buf = ''
row = []
row << commit
row << reponame
row << branchname
row << username
row << commit2geocode(commit)
row << File.read("#{RUN_DIR}/log/user/email/#{username}")
parents = File.readlines("#{RUN_DIR}/log/commits/parent/#{commit}")
row << parents.join(' ')
row << parents.map {|parent| commit2geocode(parent) }.join(' ')
row << 
data = CSV.generate_row(row, row.size, buf)
puts "Commit analyzed: #{data}"
p buf
