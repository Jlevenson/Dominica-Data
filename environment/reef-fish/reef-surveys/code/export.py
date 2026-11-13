import pandas as pd, json, numpy as np
code = open('analyze.py').read()
meta = [{'label': 'analyze.py', 'value': code, 'type': 'code', 'lang': 'python'},
        {'label': 'Input', 'value': 'REEF Comparison Report CSV exports, zone 7112 (Dominica), one per year 1994–2026, levels All/Expert/Novice, downloaded 13 Nov 2026 from reef.org'}]

def clean(df):
    return json.loads(df.replace({np.nan: None}).to_json(orient='records'))

eff = pd.read_csv('effort_by_year.csv')
eff[['year', 'n_all', 'n_exp', 'n_nov']].rename(columns={'n_all': 'surveys', 'n_exp': 'expert', 'n_nov': 'novice'}).to_csv('out_effort.csv', index=False)

T = pd.read_csv('species_trends.csv')
T = T[~T.artifact]
tr = T[['common', 'family', 'odds_ratio_decade', 'beta_decade', 'q', 'beta_exp', 'beta_nov', 'total_k', 'robust']].copy()
tr['odds_ratio_decade'] = tr.odds_ratio_decade.round(3); tr['beta_decade'] = tr.beta_decade.round(3)
tr['beta_exp'] = tr.beta_exp.round(3); tr['beta_nov'] = tr.beta_nov.round(3)
tr['q'] = tr.q.map(lambda v: float(f'{v:.3g}'))
tr = tr.rename(columns={'common': 'species', 'total_k': 'sightings'})
tr['direction'] = np.where(~tr.robust, 'No robust trend', np.where(tr.beta_decade > 0, 'Increasing', 'Decreasing'))
json.dump({'rows': clean(tr), 'meta': meta}, open('out_trends.json', 'w'))

P = pd.read_csv('species_by_period.csv')
keep = P.groupby('common').k.sum()
P = P[P.common.isin(keep[keep >= 10].index)]
p = P[['common', 'period', 'k', 'n', 'sf', 'lo', 'hi']].rename(columns={'common': 'species', 'k': 'surveys_seen', 'n': 'surveys'})
for c in ['sf', 'lo', 'hi']: p[c] = p[c].round(2)
json.dump({'rows': clean(p), 'meta': meta}, open('out_periods.json', 'w'))

s = json.load(open('summary.json'))
g = pd.DataFrame(s['groups']); g['sf'] = g.sf.round(2)
json.dump({'rows': clean(g[['group', 'period', 'sf']]), 'meta': meta}, open('out_groups.json', 'w'))

df = pd.read_csv('reef_dominica_species_year_long.csv')
lf = df[(df.level == 'All') & df.species.str.startswith('Red Lionfish')][['year', 'sf', 'den']]
lf = eff[['year', 'n_sa', 'n_all']].merge(lf, on='year', how='left').fillna({'sf': 0})
# REEF %SF counts sightings on all surveys over SA surveys; convert to share of all surveys
lf['sf'] = (100 * (lf.sf / 100 * lf.n_sa).round() / lf.n_all).round(2)
lf = lf[lf.n_all >= 1][['year', 'n_all', 'sf', 'den']].rename(columns={'n_all': 'surveys'})
lf.to_csv('out_lionfish.csv', index=False)
import os
for f in ['out_effort.csv', 'out_trends.json', 'out_periods.json', 'out_groups.json', 'out_lionfish.csv']:
    print(f, os.path.getsize(f))
print(tr.direction.value_counts())
