"""Lionfish timing: trends before (1994-2010) and after (2011 on) the first lionfish record, and the change in slope at 2011.

Usage: python3 breakpoint.py [species_year_csv effort_csv]  (defaults: analysis files, 1994-2025)
"""
import sys, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
warnings.filterwarnings('ignore')
fs, fe = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('reef_dominica_species_year_long.csv', 'effort_by_year.csv')
df = pd.read_csv(fs); eff = pd.read_csv(fe)
df = df[df.level == 'All'].copy(); df['common'] = df.species.str.split(r', \(').str[0]
eff = eff[eff.n_all >= 10].copy(); eff['exp'] = eff.n_exp / eff.n_all
SP = ['Spotted Goatfish', 'Cleaning Goby', 'Eyed Flounder', 'Flying Gurnard', 'Green Razorfish', 'Bandtail Puffer', 'Spotted Trunkfish',
      'Sand Diver', 'Trumpetfish', 'Yellow Goatfish', 'Brown Chromis', 'Peacock Flounder', 'Red Lionfish (exotic)']


def fit(g, cols):
    X = sm.add_constant(g[cols].astype(float))
    return sm.GLM(np.column_stack([g.k, g.n_all - g.k]), X, family=sm.families.Binomial()).fit(scale='X2')


rows = []
for sp in SP:
    s = df[df.common == sp][['year', 'sf']]
    g = eff.merge(s, on='year', how='left').fillna({'sf': 0})
    g['k'] = np.minimum((g.sf / 100 * g.n_sa).round(), g.n_all)
    g['yr'] = (g.year - 2010) / 10; g['post'] = (g.year >= 2011).astype(int); g['hinge'] = g.post * (g.year - 2010) / 10
    pre, post = g[g.year <= 2010], g[g.year >= 2011]
    r = dict(species=sp, sf_pre=round(100 * pre.k.sum() / pre.n_all.sum(), 1), sf_post=round(100 * post.k.sum() / post.n_all.sum(), 1))
    for lab, d in [('pre', pre), ('post', post)]:
        try:
            m = fit(d, ['yr', 'exp']); r[f'OR_{lab}'] = round(np.exp(m.params.yr), 2); r[f'p_{lab}'] = round(m.pvalues.yr, 4)
        except Exception:
            r[f'OR_{lab}'] = 1.0; r[f'p_{lab}'] = 1.0
    try:
        m = fit(g, ['yr', 'hinge', 'exp']); r['slope_change'] = round(np.exp(m.params.hinge), 2); r['p_change'] = round(m.pvalues.hinge, 4)
    except Exception:
        r['slope_change'] = 0.0; r['p_change'] = 1.0
    rows.append(r)
B = pd.DataFrame(rows)
if len(sys.argv) <= 2:
    B.to_csv('lionfish_breakpoint.csv', index=False)
print(B.to_string())
