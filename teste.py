import json
with open('./rsicd/dataset_rsicd.json') as f:
  a = json.load(f)

for img in a['images']:
  if img['filename'] in ['beach_39.jpg', 'river_42.jpg']:
    print(img['filename'])
    for sentence in img['sentences']:
      print(sentence['raw'])
