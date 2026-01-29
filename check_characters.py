import json

with open('movie_event_json/Dukudu-movie_character_introductions.json') as f:
    data = json.load(f)

print('='*70)
print('CHARACTER INTRODUCTION ANALYSIS')
print('='*70)
print(f'Total Unique Characters: {len(data["character_introductions"])}')
print()
print('First 10 Character Introductions:')
print('-'*70)
for i, intro in enumerate(data['character_introductions'][:10], 1):
    name = intro['character_name']
    time = intro['introduction_time_formatted']
    scene = intro['scene_id']
    print(f'{i:2d}. {name:25s} @ {time:12s} in {scene}')

print()
print('All Characters (Complete List):')
print('-'*70)
for i, intro in enumerate(data['character_introductions'], 1):
    name = intro['character_name']
    time = intro['introduction_time_formatted']
    print(f'{i:2d}. {name:25s} @ {time}')
