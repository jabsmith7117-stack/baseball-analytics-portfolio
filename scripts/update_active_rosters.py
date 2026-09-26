"""Save MLB active MLB roster memberships and official playing positions.

Run from the project root: python scripts/update_active_rosters.py
Requires internet access to statsapi.mlb.com. Existing snapshot stays intact
if any team request fails.
"""
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
import certifi

TEAM_IDS = {
    108: 'LAA', 109: 'AZ', 110: 'BAL', 111: 'BOS', 112: 'CHC',
    113: 'CIN', 114: 'CLE', 115: 'COL', 116: 'DET', 117: 'HOU',
    118: 'KC', 119: 'LAD', 120: 'WSH', 121: 'NYM', 133: 'ATH',
    134: 'PIT', 135: 'SD', 136: 'SEA', 137: 'SF', 138: 'STL',
    139: 'TB', 140: 'TEX', 141: 'TOR', 142: 'MIN', 143: 'PHI',
    144: 'ATL', 145: 'CWS', 146: 'MIA', 147: 'NYY', 158: 'MIL',
}


def get_json(url):
    request = Request(url, headers={'User-Agent': 'baseball-portfolio-roster/1.0'})
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(request, timeout=30, context=context) as response:
        return json.load(response)


def main():
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for team_id, team in TEAM_IDS.items():
        url = f'https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active&season=2026'
        roster = get_json(url)['roster']
        if not roster:
            raise RuntimeError(f'No active roster returned for {team}; no snapshot replaced')
        for player in roster:
            position = player.get('position') or {}
            rows.append({'player_id': player['person']['id'],
                         'team': team, 'position': position.get('abbreviation', ''),
                         'position_type': position.get('type', ''),
                         'as_of_utc': timestamp})
        print(f'{team}: {len(roster)} active players', flush=True)
    snapshot = pd.DataFrame(rows)
    if snapshot.player_id.duplicated().any():
        raise ValueError('Player appeared on two active rosters; snapshot not replaced')
    target = Path('data/active_roster_2026.csv')
    temporary = target.with_suffix('.tmp.csv')
    snapshot.to_csv(temporary, index=False)
    temporary.replace(target)
    print(f'Saved {len(snapshot)} active roster records as of {timestamp}')


if __name__ == '__main__':
    main()
