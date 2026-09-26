"""Read the dated MLB active roster snapshot without changing season stats."""
from pathlib import Path
import pandas as pd

ROSTER_FILE = Path('data/active_roster_2026.csv')


def active_roster():
    if not ROSTER_FILE.exists():
        return None
    roster = pd.read_csv(ROSTER_FILE)
    required = {'player_id', 'team', 'position', 'as_of_utc'}
    if not required.issubset(roster.columns):
        raise ValueError(f'Roster snapshot missing columns: {required - set(roster.columns)}')
    return roster


def roster_filter(frame, player_id, team_col, roster, pitchers=False):
    if roster is None:
        if pitchers and 'total_pitches' in frame.columns:
            return frame.loc[frame.total_pitches >= 50].copy()
        return frame
    members = roster
    if pitchers:
        members = members[members.position.eq('P') | members.position_type.eq('Pitcher')]
    membership = members[['player_id', 'team']].rename(columns={'player_id': player_id,
                                                                  'team': '_roster_team'})
    result = frame.merge(membership, on=player_id, how='inner', validate='many_to_one')
    result[team_col] = result.pop('_roster_team')
    return result


def appearance_table(team, role, roster, active_only):
    """Rostered or 2026 appearance players, with honest profile availability."""
    path = Path('data/appearance_index_2026.csv')
    if not path.exists():
        return None
    rows = pd.read_csv(path)
    rows = rows[rows.role.eq(role)].copy()
    if active_only and roster is not None:
        members = roster
        if role == 'Pitcher':
            members = members[members.position.eq('P') | members.position_type.eq('Pitcher')]
        rows = rows.merge(members[['player_id', 'team']], on='player_id', how='inner')
        rows = rows[rows.team.eq(team)]
    else:
        rows = rows[rows.last_team.eq(team)]
        if role == 'Pitcher' and roster is not None:
            non_pitchers = set(roster.loc[~(roster.position.eq('P') | roster.position_type.eq('Pitcher')), 'player_id'])
            rows = rows[~rows.player_id.isin(non_pitchers)]
    rows['Profile'] = rows.qualified.map({True: 'Scouting profile available', False: 'Limited MLB sample'})
    return rows.rename(columns={'name': 'Player', 'plate_appearances': 'Plate appearances',
                                'pitches': 'Pitches', 'last_game': 'Last MLB game'})[
        ['Player', 'Plate appearances', 'Pitches', 'Last MLB game', 'Profile']
    ].sort_values('Player')
