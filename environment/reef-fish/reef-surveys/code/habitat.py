"""Analysis 3: habitat-matched comparison inside vs outside the SSMR.

Habitat classes, based on the site descriptions in Madisetti (2018, OAS ReefFix) and checked
by authors who dive these sites:
  wall      - high relief: steep walls and drop-offs, and fields of coral pinnacles (Danglebens
              Pinnacles, Soufriere Pinnacles), around the rim of the submerged crater
  slope     - gently sloping reef, reef flat or shelf with sand and rubble patches
Every outside site is classed 'slope' (central-coast shelf, northern slopes, Roseau shore dives),
so the habitat-matched test compares inside 'slope' sites with outside sites.
"""
import json, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')

HABITAT = {
    # inside the reserve
    'Champagne Reef': 'slope', 'Champagne Reef North': 'slope', 'Champagne Beach South': 'slope',
    'Tous Sable at Scotts Head Bay': 'slope',
    'Danglebens North': 'wall', 'Danglebens Pinnacles': 'wall', 'Soufriere Pinnacles': 'wall',
    "L'Abym Wall / The Wall (Soufriere)": 'wall', 'Witches Point / La Sorciere / Caribs Leap': 'wall',
    'Pointe Guignard Caves': 'wall', 'Point Guirnard': 'wall', 'Swiss Cheese': 'wall',
    "Scott's Head Drop Off": 'wall', "Scott's Head Pinnacle": 'wall', 'Scotts Head Point': 'wall',
    'Cachacrou / Craters Edge': 'wall',
    # outside the reserve
    'Castle Comfort / Oceans Edge Lodge': 'slope', "Buddy's Front Porch / Fort Young Hotel": 'slope',
    'Brain Coral Reef': 'slope', 'Douglas Point': 'slope', "Maggie's Point": 'slope', 'Nose Reef': 'slope',
    'Lauro Reef': 'slope', 'Salisbury Falls (Lauro Reef)': 'slope', "Rodney's Rock": 'slope',
    'Toucarie Bay': 'slope', 'Shore Dive at Castaways': 'slope', 'Whale Shark Reef': 'slope',
}

SV = pd.read_csv('mpa_site_period_effort.csv', dtype={'code': str})
SP = pd.read_csv('mpa_site_period_species.csv', dtype={'code': str})
SV['habitat'] = SV.site.map(HABITAT)
assert SV.habitat.notna().all(), SV[SV.habitat.isna()].site.unique()
SV = SV.reset_index(drop=True)
tot = SP.groupby('species').k.sum()
keep = tot[tot >= 40].index
G = pd.MultiIndex.from_product([keep, SV.index], names=['species', 'i']).to_frame(index=False)
G = G.merge(SV.reset_index().rename(columns={'index': 'i'}), on='i')
G = G.merge(SP, on=['species', 'code', 'start'], how='left').fillna({'k': 0})
G['k'] = np.minimum(G.k, G.n)


def glm(g, cols):
    X = sm.add_constant(g[cols].astype(float))
    return sm.GLM(np.column_stack([g.k, g.n - g.k]), X, family=sm.families.Binomial()).fit(scale='X2')


old = pd.read_csv('mpa_species.csv').set_index('species')
rows = []
for sp, g in G.groupby('species'):
    gs = g[g.habitat == 'slope']
    gi = g[g.inside == 1]
    if gs[gs.inside == 1].k.sum() + gs[gs.inside == 0].k.sum() < 10:
        continue
    try:
        m = glm(gs, ['inside', 'yr', 'exp'])
        mi = glm(gs.assign(ixyr=gs.inside * gs.yr), ['inside', 'yr', 'exp', 'ixyr'])
        mw = glm(gi.assign(wall=(gi.habitat == 'wall').astype(int)), ['wall', 'yr', 'exp'])
    except Exception:
        continue
    sl_in, sl_out = gs[gs.inside == 1], gs[gs.inside == 0]
    wl = gi[gi.habitat == 'wall']
    rows.append(dict(species=sp,
                     sf_in_slope=100 * sl_in.k.sum() / sl_in.n.sum(), sf_in_wall=100 * wl.k.sum() / wl.n.sum(),
                     sf_out=100 * sl_out.k.sum() / sl_out.n.sum(),
                     OR_inside_matched=np.exp(m.params.inside), p_matched=m.pvalues.inside,
                     OR_trend_diff_matched=np.exp(mi.params.ixyr), p_trend_matched=mi.pvalues.ixyr,
                     OR_wall_vs_slope=np.exp(mw.params.wall), p_wall=mw.pvalues.wall,
                     OR_inside_all=old.OR_inside.get(sp, np.nan), robust_all=bool(old.robust_inside.get(sp, False)),
                     records=int(g.k.sum())))
H = pd.DataFrame(rows)
H['q_matched'] = multipletests(H.p_matched, method='fdr_bh')[1]
H['q_trend_matched'] = multipletests(H.p_trend_matched, method='fdr_bh')[1]
H['q_wall'] = multipletests(H.p_wall, method='fdr_bh')[1]
H.to_csv('habitat_matched.csv', index=False)

FOCAL = ['Schoolmaster', 'Yellowtail Snapper', 'Mutton Snapper', 'Horse-eye Jack', 'Bar Jack', 'Black Margate', 'Graysby',
         'Great Barracuda', 'Red Hind', 'Coney', 'French Grunt', 'Spotted Goatfish', 'Princess Parrotfish',
         'Queen Parrotfish', 'Stoplight Parrotfish', 'Fairy Basslet', 'Sand Diver', 'Bandtail Puffer', 'Brown Garden Eel']
eff = SV.groupby(['inside', 'habitat']).agg(sites=('code', 'nunique'), surveys=('n', 'sum')).reset_index()
both = H.dropna(subset=['OR_inside_all'])
agree = int((np.sign(np.log(both.OR_inside_matched)) == np.sign(np.log(both.OR_inside_all))).sum())
out = dict(effort=eff.to_dict('records'), n_species=len(H),
           matched_higher_inside=int(((H.q_matched < 0.05) & (H.OR_inside_matched > 1)).sum()),
           matched_higher_outside=int(((H.q_matched < 0.05) & (H.OR_inside_matched < 1)).sum()),
           wall_higher=int(((H.q_wall < 0.05) & (H.OR_wall_vs_slope > 1)).sum()),
           slope_higher=int(((H.q_wall < 0.05) & (H.OR_wall_vs_slope < 1)).sum()),
           same_direction_as_unmatched=agree, n_compared=len(both),
           trend_gap_widening_q05=int(((H.q_trend_matched < 0.05) & (H.OR_trend_diff_matched > 1)).sum()),
           trend_gap_narrowing_q05=int(((H.q_trend_matched < 0.05) & (H.OR_trend_diff_matched < 1)).sum()),
           rho_matched_vs_all=float(np.corrcoef(np.log(both.OR_inside_matched), np.log(both.OR_inside_all))[0, 1]))
json.dump(out, open('habitat_summary.json', 'w'), indent=1, default=float)
print(eff.to_string())
print({k: v for k, v in out.items() if k != 'effort'})
print(H[H.species.isin(FOCAL)][['species', 'sf_in_slope', 'sf_in_wall', 'sf_out', 'OR_inside_all', 'OR_inside_matched',
                                'q_matched', 'OR_trend_diff_matched', 'q_trend_matched', 'OR_wall_vs_slope']].round(3).to_string(index=False))
