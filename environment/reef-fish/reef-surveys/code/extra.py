"""Analyses 2-6: abundance index, functional groups, lionfish vs prey by site,
Hurricane Maria before/after, community composition."""
import pandas as pd, numpy as np, json, warnings
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from scipy import stats
warnings.filterwarnings('ignore')
rng = np.random.default_rng(1)

df = pd.read_csv('reef_dominica_species_year_long.csv')
eff = pd.read_csv('effort_by_year.csv')
eff['exp_share'] = eff.n_exp / eff.n_all
df['common'] = df.species.str.split(r', \(').str[0]
A = df[df.level == 'All'].merge(eff[['year', 'n_sa', 'n_all', 'exp_share']], on='year')
A['k'] = (A.sf / 100 * A.n_sa).round()
A['sfc'] = 100 * A.k / A.n_all                     # corrected sighting frequency
T = pd.read_csv('species_trends.csv')
T = T[~T.artifact].copy()
fam = df.drop_duplicates('common').set_index('common').family
out = {}

# ---------------------------------------------------------------- 2. abundance
# DEN = mean REEF abundance category (1-4) when seen. Trend in DEN per species:
# weighted least squares on years with >=10 surveys and >=3 sightings, weights = sightings,
# adjusting for expert share. Abundance index = corrected SF x DEN / 4 (0-100 scale).
yrs = eff.loc[eff.n_all >= 10, 'year']
rows = []
for sp, g in A[A.year.isin(yrs) & (A.k >= 3)].groupby('common'):
    if len(g) < 10 or sp not in set(T.common):
        continue
    X = sm.add_constant(pd.DataFrame({'yr': (g.year - 2010) / 10, 'exp': g.exp_share}))
    m = sm.WLS(g.den, X, weights=g.k).fit()
    rows.append(dict(species=sp, den_mean=np.average(g.den, weights=g.k), den_change_decade=m.params.yr,
                     p=m.pvalues.yr, years=len(g)))
D = pd.DataFrame(rows)
D['q'] = multipletests(D.p, method='fdr_bh')[1]
D = D.merge(T[['common', 'beta_decade', 'robust']].rename(columns={'common': 'species'}), on='species')
D.to_csv('abundance_den_trends.csv', index=False)
rho, prho = stats.spearmanr(D.beta_decade, D.den_change_decade)
out['abundance'] = dict(n_species=len(D), den_up=int(((D.q < 0.05) & (D.den_change_decade > 0)).sum()),
                        den_down=int(((D.q < 0.05) & (D.den_change_decade < 0)).sum()),
                        rho_sf_vs_den=round(rho, 3), p=round(prho, 4))
# abundance index by period for focal species
bins = [(1994, 2000), (2001, 2004), (2005, 2008), (2009, 2012), (2013, 2016), (2017, 2020), (2021, 2024), (2025, 2026)]
lab = {y: f'{a}–{str(b)[2:]}' for a, b in bins for y in range(a, b + 1)}
foc = ['Red Lionfish (exotic)', 'Spotted Goatfish', 'Yellowtail Snapper', 'Stoplight Parrotfish', 'Queen Parrotfish',
       'Graysby', 'Coney', 'Bar Jack', 'Brown Chromis', 'Blue Tang', 'Creole Wrasse', 'Sergeant Major']
ai = []
for sp in foc:
    g = A[A.common == sp].copy()
    g['period'] = g.year.map(lab)
    full = eff.assign(period=eff.year.map(lab)).groupby('period').n_all.sum()
    pk = g.groupby('period').agg(k=('k', 'sum'), dk=('den', lambda s: np.average(s, weights=g.loc[s.index, 'k']) if g.loc[s.index, 'k'].sum() else np.nan))
    pk = pk.reindex(full.index).fillna({'k': 0})
    pk['sf'] = 100 * pk.k / full
    pk['abund_index'] = pk.sf * pk.dk / 4
    pk['species'] = sp
    ai.append(pk.reset_index())
pd.concat(ai).to_csv('abundance_index_by_period.csv', index=False)

# ---------------------------------------------------------------- 3. functional groups
FISHED_FAM = {'Snapper', 'Jack', 'Barracuda', 'Mackerel', 'Triggerfish', 'Porgy', 'Grunt', 'Goatfish'}
GROUPERS = {'Coney', 'Graysby', 'Red Hind', 'Rock Hind', 'Yellowmouth Grouper', 'Nassau Grouper', 'Tiger Grouper', 'Black Grouper', 'Yellowfin Grouper', 'Red Grouper', 'Gag'}
HERB_FAM = {'Parrotfish', 'Surgeonfish', 'Chub'}
CRYPTIC_FAM = {'Goby', 'Blenny - Combtooth', 'Blenny - Pike', 'Blenny - Labrisomids', 'Blenny - Triplefin', 'Flounder', 'Scorpionfish',
               'Snake Eel', 'Frogfish', 'Jawfish', 'Cardinalfish', 'Flying Gurnard', 'Lizardfish', 'Batfish', 'Pipefish and Seahorse',
               'Dragonet', 'Dartfish', 'Electric Ray', 'Moray', 'Conger'}
CRYPTIC_SP = {'Green Razorfish', 'Rosy Razorfish', 'Pearly Razorfish', 'Sand Diver'}
def group(r):
    if r.common.startswith('Red Lionfish'):
        return None
    if r.common in GROUPERS or r.family in FISHED_FAM:
        return 'Fished'
    if r.family in CRYPTIC_FAM or r.common in CRYPTIC_SP:
        return 'Small cryptic / benthic'
    return 'Other reef fish'
T['group'] = T.apply(group, axis=1)
T['herbivore'] = T.family.isin(HERB_FAM)
def re_meta(b, se):
    w = 1 / se**2; fe = np.sum(w * b) / np.sum(w)
    Q = np.sum(w * (b - fe) ** 2); k = len(b)
    tau2 = max(0, (Q - (k - 1)) / (np.sum(w) - np.sum(w**2) / np.sum(w)))
    wr = 1 / (se**2 + tau2); mu = np.sum(wr * b) / np.sum(wr); s = np.sqrt(1 / np.sum(wr))
    return mu, mu - 1.96 * s, mu + 1.96 * s, k
G = []
for name, sel in [('Fished', T.group == 'Fished'), ('Small cryptic / benthic', T.group == 'Small cryptic / benthic'),
                  ('Other reef fish', T.group == 'Other reef fish'), ('Herbivores (parrotfish, surgeonfish, chubs)', T.herbivore)]:
    g = T[sel & T.se.notna() & (T.se < 5)]
    mu, lo, hi, k = re_meta(g.beta_decade.values, g.se.values)
    G.append(dict(group=name, n_species=k, OR_decade=np.exp(mu), lo=np.exp(lo), hi=np.exp(hi),
                  n_up=int((g.robust & (g.beta_decade > 0)).sum()), n_down=int((g.robust & (g.beta_decade < 0)).sum())))
G = pd.DataFrame(G); G.to_csv('functional_groups.csv', index=False)
T[['common', 'family', 'group', 'herbivore', 'beta_decade', 'se', 'robust']].to_csv('species_groups.csv', index=False)
f, c = T[T.group == 'Fished'].beta_decade, T[T.group == 'Small cryptic / benthic'].beta_decade
out['groups_test_fished_vs_cryptic'] = dict(mannwhitney_p=float(stats.mannwhitneyu(f, c).pvalue))

# ---------------------------------------------------------------- 5. Hurricane Maria
pre, post = list(range(2013, 2017)), list(range(2019, 2023))
rows = []
for sp, g in A[A.common.isin(T.common)].groupby('common'):
    x = eff[eff.year.isin(pre + post)][['year', 'n_all', 'exp_share']].merge(g[['year', 'k']], on='year', how='left').fillna({'k': 0})
    if x.k.sum() < 20:
        continue
    X = sm.add_constant(pd.DataFrame({'post': x.year.isin(post).astype(float), 'exp': x.exp_share}))
    try:
        m = sm.GLM(np.column_stack([x.k, x.n_all - x.k]), X, family=sm.families.Binomial()).fit(scale='X2')
    except Exception:
        continue
    rows.append(dict(species=sp, sf_pre=100 * x[x.year.isin(pre)].k.sum() / x[x.year.isin(pre)].n_all.sum(),
                     sf_post=100 * x[x.year.isin(post)].k.sum() / x[x.year.isin(post)].n_all.sum(),
                     OR_post=np.exp(m.params.post), p=m.pvalues.post))
M = pd.DataFrame(rows); M['q'] = multipletests(M.p, method='fdr_bh')[1]
M = M.merge(T[['common', 'group']].rename(columns={'common': 'species'}), on='species', how='left')
M.to_csv('maria_before_after.csv', index=False)
out['maria'] = dict(n=len(M), up=int(((M.q < 0.05) & (M.OR_post > 1)).sum()), down=int(((M.q < 0.05) & (M.OR_post < 1)).sum()),
                    by_group=M.assign(lo=np.log(M.OR_post)).groupby('group').lo.median().apply(np.exp).round(2).to_dict(),
                    surveys_pre=int(eff[eff.year.isin(pre)].n_all.sum()), surveys_post=int(eff[eff.year.isin(post)].n_all.sum()))

# ---------------------------------------------------------------- site-level data (28 classified sites)
SV = pd.read_csv('mpa_site_period_effort.csv', dtype={'code': str})
SP = pd.read_csv('mpa_site_period_species.csv', dtype={'code': str})
SP = SP.merge(SV[['code', 'start', 'n']], on=['code', 'start'])
SP['p'] = np.minimum(SP.k, SP.n) / SP.n

# ---------------------------------------------------------------- 4. lionfish vs prey by site
PREY_FAM = {'Goby', 'Blenny - Combtooth', 'Blenny - Pike', 'Blenny - Labrisomids', 'Blenny - Triplefin', 'Cardinalfish', 'Basslet',
            'Jawfish', 'Dragonet', 'Dartfish'}
PREY_SP = {'Bicolor Damselfish', 'Beaugregory', 'Cocoa Damselfish', 'Threespot Damselfish', 'Dusky Damselfish', 'Longfin Damselfish',
           'Bluehead', 'Yellowhead Wrasse', 'Slippery Dick', 'Clown Wrasse', 'Rainbow Wrasse', 'Blackear Wrasse',
           'Green Razorfish', 'Rosy Razorfish', 'Brown Chromis', 'Blue Chromis', 'Peppermint Basslet', 'Fairy Basslet',
           'Harlequin Bass', 'Lantern Bass', 'Tobaccofish', 'Masked Goby / Glass Goby', 'Flamefish', 'Sharknose Goby', 'Cleaning Goby',
           'Spotted Goatfish', 'Juvenile Grunt', 'Glassy Sweeper'}
SP['fam'] = SP.species.map(fam)
SP['prey'] = SP.fam.isin(PREY_FAM) | SP.species.isin(PREY_SP)
early = SV[SV.start <= 2005].groupby('code').n.sum(); late = SV[SV.start >= 2013].groupby('code').n.sum()
ok = early[early >= 10].index.intersection(late[late >= 10].index)
prey_sp = SP[SP.prey].groupby('species').k.sum(); prey_sp = prey_sp[prey_sp >= 30].index
rows = []
for code in ok:
    e = SV[(SV.code == code) & (SV.start <= 2005)]; l = SV[(SV.code == code) & (SV.start >= 2013)]
    ne, nl = e.n.sum(), l.n.sum()
    def sf(sp, sub, n):
        return (SP[(SP.code == code) & (SP.species == sp) & SP.start.isin(sub.start)].k.sum() + 0.5) / (n + 1)
    lg = lambda p: np.log(p / (1 - p))
    ch = [lg(sf(sp, l, nl)) - lg(sf(sp, e, ne)) for sp in prey_sp]
    lf = SP[(SP.code == code) & (SP.species == 'Red Lionfish (exotic)') & SP.start.isin(l.start)].k.sum() / nl
    rows.append(dict(code=code, site=SV[SV.code == code].site.iloc[0], inside=int(SV[SV.code == code].inside.iloc[0]),
                     n_early=int(ne), n_late=int(nl), lionfish_sf_late=100 * lf, prey_logit_change=np.mean(ch),
                     exp_late=float(np.average(l.exp, weights=l.n))))
L = pd.DataFrame(rows); L.to_csv('lionfish_vs_prey_sites.csv', index=False)
r, pr = stats.spearmanr(L.lionfish_sf_late, L.prey_logit_change)
Xl = sm.add_constant(L[['lionfish_sf_late', 'exp_late']]); ml = sm.OLS(L.prey_logit_change, Xl).fit()
out['lionfish_prey'] = dict(n_sites=len(L), n_prey_species=len(prey_sp), spearman_rho=round(r, 3), p=round(pr, 3),
                            ols_slope_per10pct=round(ml.params.lionfish_sf_late * 10, 3), ols_p=round(ml.pvalues.lionfish_sf_late, 3))

# ---------------------------------------------------------------- 6. community composition
from sklearn.manifold import MDS
mat = SP.pivot_table(index=['code', 'start'], columns='species', values='p', aggfunc='sum', fill_value=0)
mat = mat.loc[:, ~mat.columns.str.contains('Juvenile|Complex|nidentified|sp\\.', regex=True)]
meta = SV.set_index(['code', 'start']).loc[mat.index]
keep = meta.n >= 8
mat, meta = mat[keep], meta[keep]
mat = mat.loc[:, (mat > 0).sum() >= 5]
X = mat.values
def bray(X):
    n = len(X); Dm = np.zeros((n, n))
    for i in range(n):
        Dm[i] = np.abs(X - X[i]).sum(1) / (X + X[i]).sum(1)
    return Dm
Dm = bray(X)
def permanova(Dm, design, perms=999):
    # sequential (type I) PERMANOVA via distance-based linear model (McArdle & Anderson)
    n = len(Dm); A_ = -0.5 * Dm**2; Cn = np.eye(n) - 1 / n; Gm = Cn @ A_ @ Cn
    terms = list(design.keys()); res = {}
    Xs = [np.ones((n, 1))]
    def ss(Xm):
        H = Xm @ np.linalg.pinv(Xm)
        return np.trace(H @ Gm @ H)
    sst = np.trace(Gm)
    full = np.column_stack([np.ones(n)] + [design[t] for t in terms])
    Hf = full @ np.linalg.pinv(full); sse = np.trace((np.eye(n) - Hf) @ Gm @ (np.eye(n) - Hf)); dfe = n - np.linalg.matrix_rank(full)
    prev = np.ones((n, 1)); prev_ss = ss(prev)
    for t in terms:
        cur = np.column_stack([prev, design[t]]); cur_ss = ss(cur); df_t = np.linalg.matrix_rank(cur) - np.linalg.matrix_rank(prev)
        F = ((cur_ss - prev_ss) / df_t) / (sse / dfe)
        cnt = 0
        for _ in range(perms):
            idx = rng.permutation(n); Gp = Gm[np.ix_(idx, idx)]
            Hc = cur @ np.linalg.pinv(cur); Hp = prev @ np.linalg.pinv(prev)
            Hfp = Hf
            ssc = np.trace(Hc @ Gp @ Hc) - np.trace(Hp @ Gp @ Hp)
            ssep = np.trace((np.eye(n) - Hfp) @ Gp @ (np.eye(n) - Hfp))
            if (ssc / df_t) / (ssep / dfe) >= F: cnt += 1
        res[t] = dict(R2=round((cur_ss - prev_ss) / sst, 3), F=round(F, 2), p=(cnt + 1) / (perms + 1))
        prev, prev_ss = cur, cur_ss
    return res
design = {'expert_share': meta.exp.values.reshape(-1, 1), 'site': pd.get_dummies(meta.index.get_level_values(0), drop_first=True).values.astype(float),
          'year': meta.yr.values.reshape(-1, 1)}
pm_site = permanova(Dm, design, perms=499)
design2 = {'expert_share': meta.exp.values.reshape(-1, 1), 'inside_reserve': meta.inside.values.reshape(-1, 1).astype(float),
           'year': meta.yr.values.reshape(-1, 1), 'inside_x_year': (meta.inside * meta.yr).values.reshape(-1, 1)}
pm_res = permanova(Dm, design2, perms=499)
nm = MDS(n_components=2, metric=False, dissimilarity='precomputed', random_state=1, n_init=8, max_iter=500, normalized_stress='auto')
Y = nm.fit_transform(Dm)
pd.DataFrame({'code': meta.index.get_level_values(0), 'start': meta.index.get_level_values(1), 'site': meta.site.values,
              'inside': meta.inside.values, 'n': meta.n.values, 'nmds1': Y[:, 0], 'nmds2': Y[:, 1]}).to_csv('nmds_scores.csv', index=False)
# species most associated with each NMDS axis
cor = pd.DataFrame({'species': mat.columns, 'r1': [stats.spearmanr(mat[c], Y[:, 0])[0] for c in mat.columns],
                    'r2': [stats.spearmanr(mat[c], Y[:, 1])[0] for c in mat.columns]})
cor.to_csv('nmds_species_correlations.csv', index=False)
out['community'] = dict(site_periods=len(meta), species=mat.shape[1], stress=round(float(nm.stress_), 3),
                        permanova_site_model=pm_site, permanova_reserve_model=pm_res,
                        nmds1_vs_year_rho=round(stats.spearmanr(Y[:, 0], meta.yr)[0], 3), nmds2_vs_year_rho=round(stats.spearmanr(Y[:, 1], meta.yr)[0], 3))

json.dump(out, open('extra_summary.json', 'w'), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
print(G.round(3).to_string(index=False))
