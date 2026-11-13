"""Analysis 6: do species traits predict long-term trends?

Traits come from FishLife (Thorson et al.), which gives FishBase-based trait predictions for
every fish species, filling gaps from relatives: maximum length, trophic level, body shape,
habitat and feeding mode. Species trends (log odds per decade, species_trends.csv) are
regressed on traits with a family random intercept (taxonomic non-independence) and
inverse-variance weights.
"""
import json, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')

# FishLife data: git clone https://github.com/James-Thorson-NOAA/FishLife and read
# data/FishBase_and_Morphometrics.rda with the Python 'rdata' package.
import rdata
_fl = rdata.read_rda('FishLife/data/FishBase_and_Morphometrics.rda')['FishBase_and_Morphometrics']
B = np.asarray(_fl['beta_gv'])
names = [str(x) for x in _fl['beta_gv'].coords[_fl['beta_gv'].dims[1]].values]
pc = _fl['ParentChild_gz']
tr = pd.DataFrame(B, columns=[f'{n}_{i}' if n == 'base' else n for i, n in enumerate(names)])
tr['taxon'] = pc.ChildName.values
tr = tr[tr.taxon.str.count('_') == 4].copy()          # class_order_family_genus_species
tr['sci'] = tr.taxon.str.split('_').str[-2:].str.join(' ')
tr = tr.drop_duplicates('sci').set_index('sci')

df = pd.read_csv('reef_dominica_species_year_long.csv')
u = df.drop_duplicates('species')
sci = pd.Series(u.species.str.extract(r'\((.*)\)$')[0].values, index=u.species.values)
T = pd.read_csv('species_trends.csv')
T = T[~T.artifact].copy()
T['sci'] = T.species.map(sci)
FISHED = {'Snapper', 'Jack', 'Barracuda', 'Mackerel', 'Triggerfish', 'Porgy', 'Grunt', 'Goatfish', 'Grouper', 'Sea Bass'}
GROUPER_GENERA = ('Epinephelus', 'Cephalopholis', 'Mycteroperca', 'Hyporthodus')
T = T.join(tr[['log(length_max)', 'trophic_level', 'habitatreefassociated', 'feeding_modemacrofauna',
               'feeding_modeplanktivorous_or_other', 'body_shapeelongated', 'body_shapeeellike',
               'body_shapeshort_and_or_deep']], on='sci')
T = T.dropna(subset=['log(length_max)'])
T['fished'] = (T.family.isin({'Snapper', 'Jack', 'Barracuda', 'Mackerel', 'Triggerfish', 'Porgy', 'Grunt', 'Goatfish'})
               | T.sci.str.startswith(GROUPER_GENERA)).astype(int)
T = T.rename(columns={'log(length_max)': 'loglmax'})
T['lmax_cm'] = np.exp(T.loglmax)
T['w'] = 1 / T.se ** 2
for c in ['loglmax', 'trophic_level']:
    T[c + '_z'] = (T[c] - T[c].mean()) / T[c].std()
T['eel_or_elongated'] = T.body_shapeelongated + T.body_shapeeellike
T[['species', 'family', 'beta_decade', 'se', 'robust', 'lmax_cm', 'trophic_level', 'fished',
   'eel_or_elongated', 'feeding_modemacrofauna', 'feeding_modeplanktivorous_or_other']].to_csv('traits_species.csv', index=False)

out = dict(n_species=len(T), n_families=int(T.family.nunique()))
f = 'beta_decade ~ loglmax_z + trophic_level_z + fished + eel_or_elongated'
wls = smf.wls(f, T, weights=T.w).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(T.family)[0]})
mm = smf.mixedlm(f, T, groups=T.family).fit(reml=True)
out['wls_cluster_family'] = {k: dict(coef=float(wls.params[k]), lo=float(wls.conf_int().loc[k, 0]),
                                     hi=float(wls.conf_int().loc[k, 1]), p=float(wls.pvalues[k])) for k in wls.params.index}
out['mixed_family'] = {k: dict(coef=float(mm.params[k]), p=float(mm.pvalues[k])) for k in wls.params.index}
# Simple single-trait associations among all modelled species
for c in ['loglmax', 'trophic_level']:
    m = smf.wls(f'beta_decade ~ {c}_z', T, weights=T.w).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(T.family)[0]})
    out[f'single_{c}'] = dict(coef=float(m.params[f'{c}_z']), p=float(m.pvalues[f'{c}_z']))
# Body size classes for presentation
T['size'] = pd.cut(T.lmax_cm, [0, 15, 40, 1000], labels=['<15 cm', '15–40 cm', '>40 cm'])
out['by_size'] = T.groupby('size', observed=True).apply(lambda s: dict(n=len(s), median_or=float(np.exp(s.beta_decade.median())),
    up=int((s.robust & (s.beta_decade > 0)).sum()), down=int((s.robust & (s.beta_decade < 0)).sum()))).to_dict()
print(wls.summary().tables[1]); print(mm.summary().tables[1]); print(out['by_size'], out['n_species'], out['n_families'])
json.dump(out, open('traits_summary.json', 'w'), indent=1, default=str)
