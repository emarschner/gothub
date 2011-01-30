import json
import sys

data = json.loads(sys.stdin.read())
nodes = data['nodes']
links = data['links']

original_indexes = {}
averages = []
index = 0
for node in nodes:
  original_indexes[index] = node['nodeName']
  values = [ link['value'] for link in links if link['source'] == index ]
  average = sum(values) / len(values)
  averages.append([node['nodeName'], average])
  index += 1

new_indexes = {}
index = 0
nodes = data['nodes'] = []
for entry in sorted(averages, key=lambda entry: entry[1], reverse=True):
  new_indexes[entry[0]] = index
  nodes.append({'group': 1, 'nodeName': entry[0]})
  index += 1

for link in links:
  link['source'] = new_indexes[original_indexes[link['source']]]
  link['target'] = new_indexes[original_indexes[link['target']]]

print json.dumps(data)
