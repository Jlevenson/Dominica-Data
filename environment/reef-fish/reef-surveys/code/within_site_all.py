"""Within-site trends for all species at the 28 classified sites (site fixed effects).

Tests whether island-wide trends, especially increases in fished species, hold at the same
sites, i.e. are not produced by survey effort shifting towards reserve walls.
"""
import json, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')

SV = pd.read_csv('mpa_site_period_effort.csv', dtype={'code': str}).reset_index(drop=True)
SP = pd.read_csv('mpa_site_period_species.csv', dtype={'code': str})
tot = SP.groupby('species').k.sum()
keep = tot[tot >= 40].index
G = pd.MultiIndex.from_product([keep, SV.index], names=['species', 'i']).to_frame(index=False)
G = G.merge(SV.reset_index().rename(columns={'index': 'i'}), on='i')
G = G.merge(SP, on=['species', 'code', 'start'], how='left').fillna({'k': 0})
G['k'] = np.minimum(G.k, G.n)
T = pd.read_csv('species_trends.csv')[['common', 'odds_ratio_decade', 'robust']].rename(columns={'common': 'species'})
grp = pd.read_csv('traits_species.csv')
grp['species'] = grp.species.str.split(r', \(').str[0]

rows = []
for sp, g in G.groupby('species'):
    sites = g.groupby('code').k.sum()
    g = g[g.code.isin(sites[sites > 0].index)]
    if g.code.nunique() < 3:
        continue
    X = pd.get_dummies(g.code, prefix='s', drop_first=True, dtype=float)
    X['yr'], X['exp'] = g.yr.values, g.exp.values
    X = sm.add_constant(X)
    try:
        m = sm.GLM(np.column_stack([g.k, g.n - g.k]), X, family=sm.families.Binomial()).fit(scale='X2')
    except Exception:
        continue
    ci = m.conf_int().loc['yr']
    rows.append(dict(species=sp, within_site_OR=np.exp(m.params.yr), lo=np.exp(ci[0]), hi=np.exp(ci[1]),
                     p=m.pvalues.yr, sites=g.code.nunique()))
W = pd.DataFrame(rows)
W['q'] = multipletests(W.p, method='fdr_bh')[1]
W = W.merge(T, on='species', how='left').merge(grp[['species', 'fished']], on='species', how='left')
W.to_csv('within_site_all.csv', index=False)
both = W.dropna(subset=['odds_ratio_decade'])
rb = both[both.robust == True]
out = dict(n_species=len(W),
           robust_compared=len(rb),
           robust_same_sign=int((np.sign(np.log(rb.within_site_OR)) == np.sign(np.log(rb.odds_ratio_decade))).sum()),
           robust_same_sign_q05=int(((np.sign(np.log(rb.within_site_OR)) == np.sign(np.log(rb.odds_ratio_decade))) & (rb.q < 0.05)).sum()),
           rho=float(np.corrcoef(np.log(both.within_site_OR), np.log(both.odds_ratio_decade))[0, 1]),
           fished_median_within_OR=float(W[W.fished == 1].within_site_OR.median()),
           unfished_median_within_OR=float(W[W.fished == 0].within_site_OR.median()))
json.dump(out, open('within_site_all_summary.json', 'w'), indent=1, default=float)
print(out)
F = ['Yellowtail Snapper', 'Schoolmaster', 'Mutton Snapper', 'Bar Jack', 'Horse-eye Jack', 'Graysby', 'Black Margate',
     'Great Barracuda', 'Red Hind', 'Coney', 'Queen Parrotfish', 'Blackfin Snapper']
print(W[W.species.isin(F)][['species', 'odds_ratio_decade', 'within_site_OR', 'lo', 'hi', 'q', 'sites']].round(3).to_string(index=False))
