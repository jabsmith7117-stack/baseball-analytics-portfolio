"""Index all 2026 MLB appearances, including players below scouting cutoffs.

Run from the project root after updating the raw Statcast file. The index is
informational; it does not imply a qualified scouting profile or prediction.
"""
import json
import ssl
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
import pandas as pd

RAW = Path('data/statcast_2023_2026_full.csv')
OUT = Path('data/appearance_index_2026.csv')
COLS = ['game_year', 'game_date', 'batter', 'pitcher', 'player_name',
        'woba_denom', 'pitch_type', 'home_team', 'away_team', 'inning_topbot']


def names_from_mlb(ids):
    results = {}
    context = ssl.create_default_context(cafile=certifi.where())
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        url = 'https://statsapi.mlb.com/api/v1/people?' + urlencode({'personIds': ','.join(map(str, batch))})
        with urlopen(Request(url, headers={'User-Agent': 'baseball-portfolio/1.0'}),
                     timeout=30, context=context) as response:
            people = json.load(response).get('people', [])
        results.update({int(person['id']): person['fullName'] for person in people})
    return results


def main():
    hitters = defaultdict(lambda: {'pitches': 0, 'pa': 0, 'last_game': '', 'team': ''})
    pitchers = defaultdict(lambda: {'pitches': 0, 'pa': 0, 'last_game': '', 'team': '', 'name': ''})
    for chunk in pd.read_csv(RAW, usecols=COLS, chunksize=150_000, low_memory=False):
        chunk = chunk[chunk.game_year.eq(2026)].copy()
        if chunk.empty:
            continue
        batting_team = chunk.away_team.where(chunk.inning_topbot.eq('Top'), chunk.home_team)
        pitching_team = chunk.home_team.where(chunk.inning_topbot.eq('Top'), chunk.away_team)
        chunk['_bat_team'] = batting_team
        chunk['_pit_team'] = pitching_team
        chunk['_pa'] = chunk.woba_denom.notna().astype(int)
        chunk['_pitch'] = chunk.pitch_type.notna().astype(int)
        for player_id, group in chunk.groupby('batter'):
            item = hitters[int(player_id)]
            item['pitches'] += len(group)
            item['pa'] += int(group['_pa'].sum())
            recent = group.sort_values('game_date').iloc[-1]
            if recent.game_date >= item['last_game']:
                item['last_game'] = recent.game_date
                item['team'] = recent['_bat_team']
        for player_id, group in chunk.groupby('pitcher'):
            item = pitchers[int(player_id)]
            item['pitches'] += int(group['_pitch'].sum())
            item['pa'] += int(group['_pa'].sum())
            recent = group.sort_values('game_date').iloc[-1]
            if recent.game_date >= item['last_game']:
                item['last_game'] = recent.game_date
                item['team'] = recent['_pit_team']
                item['name'] = recent.player_name
    hitter_core = pd.read_csv('data/hitter_core_stats.csv', usecols=['batter', 'batter_name'])
    pitcher_core = pd.read_csv('data/pitcher_core_stats.csv', usecols=['pitcher'])
    hitter_names = dict(zip(hitter_core.batter.astype(int), hitter_core.batter_name))
    qualified_hitters = set(hitter_names)
    qualified_pitchers = set(pitcher_core.pitcher.astype(int))
    missing_names = sorted(set(hitters) - set(hitter_names))
    hitter_names.update(names_from_mlb(missing_names))
    rows = []
    for player_id, item in hitters.items():
        rows.append({'player_id': player_id, 'name': hitter_names.get(player_id, f'MLB ID {player_id}'),
                     'role': 'Hitter', 'last_team': item['team'], 'last_game': item['last_game'],
                     'plate_appearances': item['pa'], 'pitches': item['pitches'],
                     'qualified': player_id in qualified_hitters})
    for player_id, item in pitchers.items():
        rows.append({'player_id': player_id, 'name': item['name'], 'role': 'Pitcher',
                     'last_team': item['team'], 'last_game': item['last_game'],
                     'plate_appearances': item['pa'], 'pitches': item['pitches'],
                     'qualified': player_id in qualified_pitchers})
    frame = pd.DataFrame(rows)
    temp = OUT.with_suffix('.tmp.csv')
    frame.to_csv(temp, index=False)
    temp.replace(OUT)
    print(f'Saved {len(frame)} 2026 hitter/pitcher appearance records to {OUT}')
    for player_id in (800543, 811315):
        print(frame[frame.player_id.eq(player_id)].to_string(index=False))


if __name__ == '__main__':
    main()
