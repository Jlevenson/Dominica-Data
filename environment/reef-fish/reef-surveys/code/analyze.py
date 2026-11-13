import pandas as pd, numpy as np, json, warnings
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')

df = pd.read_csv('reef_dominica_species_year_long.csv')
eff = pd.read_csv('effort_by_year.csv')
# REEF's %SF = sightings on ALL surveys (species-and-abundance + species-only) / SA surveys x 100,
# so it can exceed 100%. Back-calculate sightings with the SA count, then use ALL surveys as the denominator.
eff['exp_share'] = eff.n_exp / eff.n_all.replace(0, np.nan)
df['common'] = df.species.str.split(r', \(').str[0]
df['sci'] = df.species.str.extract(r'\((.*)\)$')[0]

def counts(level, sacol, ncol):
    d = df[df.level == level].merge(eff[['year', sacol, ncol, 'exp_share']], on='year')
    d['k'] = (d.sf / 100 * d[sacol]).round().astype(int)
    d['n'] = d[ncol]
    assert (d.k <= d.n).all()
    return d

allc = counts('All', 'n_sa', 'n_all')
MIN_N = 10
years_ok = eff.loc[eff.n_all >= MIN_N, 'year'].tolist()

# Full grid species x year (zeros where not seen)
def grid(c, ncol, yrs):
    sp = c.groupby('species').k.sum()
    g = pd.MultiIndex.from_product([sp.index, yrs], names=['species', 'year']).to_frame(index=False)
    g = g.merge(c[['species', 'year', 'k', 'den']], how='left', on=['species', 'year']).fillna({'k': 0})
    g = g.merge(eff[['year', ncol, 'exp_share']].rename(columns={ncol: 'n'}), on='year')
    return g

G = grid(allc, 'n_all', years_ok)

def fit(g, cov=True):
    out = []
    for sp, s in g.groupby('species'):
        s = s[s.n > 0]
        if s.k.sum() < 30 or (s.k > 0).sum() < 5:
            continue
        X = pd.DataFrame({'c': 1.0, 'yr': (s.year - 2010) / 10})
        if cov:
            X['exp'] = s.exp_share.values
        y = np.column_stack([s.k, s.n - s.k])
        try:
            m = sm.GLM(y, X, family=sm.families.Binomial()).fit(scale='X2')
        except Exception:
            continue
        b, se, p = m.params['yr'], m.bse['yr'], m.pvalues['yr']
        out.append(dict(species=sp, beta_decade=b, se=se, p=p, odds_ratio_decade=np.exp(b), total_k=int(s.k.sum())))
    r = pd.DataFrame(out)
    r['q'] = multipletests(r.p, method='fdr_bh')[1]
    return r

T = fit(G)
# robustness: expert-only and novice-only (no covariate)
TE = fit(grid(counts('Expert', 'n_sa_exp', 'n_exp'), 'n_exp', eff.loc[eff.n_exp >= MIN_N, 'year'].tolist()), cov=False)
TN = fit(grid(counts('Novice', 'n_sa_nov', 'n_nov'), 'n_nov', eff.loc[eff.n_nov >= MIN_N, 'year'].tolist()), cov=False)
T = T.merge(TE[['species', 'beta_decade', 'q']].rename(columns={'beta_decade': 'beta_exp', 'q': 'q_exp'}), how='left', on='species')
T = T.merge(TN[['species', 'beta_decade', 'q']].rename(columns={'beta_decade': 'beta_nov', 'q': 'q_nov'}), how='left', on='species')
T['common'] = T.species.str.split(r', \(').str[0]
T['family'] = T.species.map(df.drop_duplicates('species').set_index('species').family)

def agree(r):
    s = np.sign(r.beta_decade)
    return all((np.isnan(x) or np.sign(x) == s) for x in [r.beta_exp, r.beta_nov])
T['consistent'] = T.apply(agree, axis=1)
T['direction'] = np.where(T.q < 0.05, np.where(T.beta_decade > 0, 'Increasing', 'Decreasing'), 'No clear trend')
# Reporting-category artifacts (codes added later, complexes, unidentified) are excluded from trend calls
T['artifact'] = T.species.str.contains(r'Juvenile|Complex|unidentified|sp\.|spp', case=False)
# Robust = significant (FDR q<0.05) with the same sign in expert-only AND novice-only fits
T['robust'] = ((T.q < 0.05) & T.beta_exp.notna() & T.beta_nov.notna()
               & (np.sign(T.beta_exp) == np.sign(T.beta_decade)) & (np.sign(T.beta_nov) == np.sign(T.beta_decade)) & ~T.artifact)
T.sort_values('beta_decade').to_csv('species_trends.csv', index=False)

# Periods (pooled)
bins = [(1994, 2000), (2001, 2004), (2005, 2008), (2009, 2012), (2013, 2016), (2017, 2020), (2021, 2024), (2025, 2026)]
lab = {y: f'{a}–{str(b)[2:]}' for a, b in bins for y in range(a, b + 1)}
allfull = grid(allc, 'n_all', eff.year.tolist())
allfull['period'] = allfull.year.map(lab)
P = allfull.groupby(['species', 'period']).agg(k=('k', 'sum'), n=('n', 'sum')).reset_index()
P['sf'] = 100 * P.k / P.n
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)
P['lo'], P['hi'] = wilson(P.k, P.n)
P['common'] = P.species.str.split(r', \(').str[0]
P.to_csv('species_by_period.csv', index=False)
peff = eff.assign(period=eff.year.map(lab)).groupby('period').agg(n_all=('n_all', 'sum'), n_exp=('n_exp', 'sum')).reset_index()
peff['exp_share'] = peff.n_exp / peff.n_all

# Richness per year
rich = allc.groupby('year').species.nunique().rename('species_recorded').reset_index().merge(eff, on='year')

# Lionfish first record
lf = allc[allc.common.str.contains('Lionfish')].sort_values('year')

# Group-level indices (mean SF of member species per period)
groups = {
 'Parrotfish': ['Stoplight Parrotfish','Redband Parrotfish','Princess Parrotfish','Queen Parrotfish','Striped Parrotfish','Yellowtail (Redfin) Parrotfish','Redtail Parrotfish'],
 'Groupers & hinds': ['Coney','Graysby','Red Hind','Rock Hind','Nassau Grouper','Yellowmouth Grouper','Tiger Grouper','Black Grouper'],
 'Snappers': ['Yellowtail Snapper','Mahogany Snapper','Mutton Snapper','Schoolmaster','Dog Snapper','Lane Snapper','Cubera Snapper','Gray Snapper'],
 'Grunts': ['French Grunt','Smallmouth Grunt','Bluestriped Grunt','Caesar Grunt','White Grunt','Tomtate'],
 'Large predators': ['Great Barracuda','Horse-Eye Jack','Cero','Nurse Shark','Southern Stingray','Spotted Eagle Ray'],
}
print('unmatched:', {g: [s for s in v if s not in set(P.common)] for g, v in groups.items()})
GP = []
for g, v in groups.items():
    s = P[P.common.isin(v)].groupby('period').sf.mean().reset_index(); s['group'] = g; GP.append(s)
GP = pd.concat(GP)

periods = [lab[a] for a, b in bins]
focal = ['Red Lionfish','Stoplight Parrotfish','Queen Parrotfish','Nassau Grouper','Red Hind','Coney','Graysby','Yellowtail Snapper',
         'Mutton Snapper','Great Barracuda','Hawksbill Sea Turtle','Green Sea Turtle','Nurse Shark','Southern Stingray','French Angelfish','Queen Angelfish',
         'Blue Tang','Ocean Surgeonfish','Longsnout Seahorse','Spotted Drum']
print('focal missing:', [f for f in focal if not P.common.str.startswith(f).any()])

out = dict(
  effort=eff[['year','n_all','n_exp','n_nov','exp_share']].to_dict('records'),
  period_effort=peff.set_index('period').loc[periods].reset_index().to_dict('records'),
  richness=rich[['year','species_recorded','n_all']].to_dict('records'),
  lionfish=lf[['year','sf','den','n']].to_dict('records'),
  groups=GP.to_dict('records'),
  periods=periods,
)
json.dump(out, open('summary.json', 'w'), default=float)
print(T.direction.value_counts(), T.robust.sum())
print(T[T.robust].sort_values('beta_decade')[['common','odds_ratio_decade','q','beta_exp','beta_nov','total_k']].to_string())
print(lf[['year','sf','n']].to_string())
print(peff.to_string())
print(rich[['year','species_recorded','n_all']].to_string())
