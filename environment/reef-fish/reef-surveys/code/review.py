"""Reviewer-driven analyses 1, 2, 4 and 5.

1. Temporal autocorrelation and non-linearity: HAC (Newey-West) standard errors for the
   linear trends, lag-1 residual autocorrelation, and spline GAMs with a test of non-linearity.
2. Hierarchical regional model: per species, one binomial model across islands with island
   intercepts, a shared year slope and a Dominica x year deviation.
4. Effort-corrected species richness from incidence frequencies (rarefaction, Chao2).
5. Sensitivity of the robust trends to analysis choices.
"""
import json, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from patsy import dmatrix, build_design_matrices
from statsmodels.stats.multitest import multipletests
from scipy import stats
from scipy.special import gammaln
warnings.filterwarnings('ignore')

df = pd.read_csv('reef_dominica_species_year_long.csv')
eff = pd.read_csv('effort_by_year.csv')
eff['exp_share'] = eff.n_exp / eff.n_all.replace(0, np.nan)
d = df[df.level == 'All'].merge(eff[['year', 'n_sa', 'n_all', 'exp_share']], on='year')
d['k'] = (d.sf / 100 * d.n_sa).round().astype(int)
T = pd.read_csv('species_trends.csv')
robust = T[T.robust]
out = {}


def grid(min_n=10, years=None):
    yrs = eff.loc[eff.n_all >= min_n, 'year'] if years is None else pd.Series(years)
    sp = d.species.unique()
    g = pd.MultiIndex.from_product([sp, yrs], names=['species', 'year']).to_frame(index=False)
    g = g.merge(d[['species', 'year', 'k']], how='left', on=['species', 'year']).fillna({'k': 0})
    return g.merge(eff[['year', 'n_all', 'exp_share']].rename(columns={'n_all': 'n'}), on='year')


def glm(s, cov_type='nonrobust'):
    X = pd.DataFrame({'c': 1.0, 'yr': (s.year.values - 2010) / 10, 'exp': s.exp_share.values})
    y = np.column_stack([s.k, s.n - s.k])
    m = sm.GLM(y, X, family=sm.families.Binomial())
    if cov_type == 'HAC':
        return m.fit(cov_type='HAC', cov_kwds={'maxlags': 2})
    return m.fit(scale='X2')


# ---------------- 1. autocorrelation and non-linearity
G = grid()
rows, curves = [], []
FOCAL = ['Red Lionfish', 'Spotted Goatfish', 'Yellowtail Snapper', 'Schoolmaster', 'Cleaning Goby',
         'Trumpetfish', 'Sharknose Goby', 'Eyed Flounder', 'Queen Parrotfish', 'Bar Jack']
for sp, s in G.groupby('species'):
    s = s.sort_values('year')
    if sp not in set(T.species):
        continue
    try:
        mq = glm(s)
        mh = glm(s, 'HAC')
    except Exception:
        continue
    resid = mq.resid_pearson
    ac1 = float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
    # GAM: B-spline on year (df=5) + linear expert share. Quasi-binomial F-tests: any change over
    # time (GAM vs no-year model) and non-linearity (GAM vs linear). F is deflated for lag-1
    # residual autocorrelation (effective-sample-size factor (1+rho)/(1-rho) when rho > 0).
    x = ((s.year.values - 2010) / 10).reshape(-1, 1)
    y = np.column_stack([s.k, s.n - s.k])
    try:
        SPL = np.asarray(dmatrix('cr(x, df=4) - 1', {'x': x.ravel()}))
        SPL = SPL - SPL.mean(0)
        XG = np.column_stack([np.ones(len(s)), s.exp_share.values, SPL])
        mg = sm.GLM(y, XG, family=sm.families.Binomial()).fit()
        m0 = sm.GLM(y, pd.DataFrame({'c': 1.0, 'exp': s.exp_share.values}), family=sm.families.Binomial()).fit()
        pg = XG.shape[1]
        dfr = len(s) - pg
        rg = (y[:, 0] - (s.n.values * mg.fittedvalues)) / np.sqrt(s.n.values * mg.fittedvalues * (1 - mg.fittedvalues))
        phi = float(np.sum(rg ** 2) / dfr)
        rho_g = float(np.corrcoef(rg[:-1], rg[1:])[0, 1])
        infl = (1 + rho_g) / (1 - rho_g) if rho_g > 0 else 1.0
        F_nl = max(mq.deviance - mg.deviance, 0) / (pg - 3) / phi / infl
        F_ch = max(m0.deviance - mg.deviance, 0) / (pg - 2) / phi / infl
        p_nl = float(stats.f.sf(F_nl, pg - 3, dfr))
        p_ch = float(stats.f.sf(F_ch, pg - 2, dfr))
        fv = np.asarray(mg.fittedvalues)
        early, late = fv[s.year.values <= 2000].mean(), fv[s.year.values >= 2021].mean()
        gam_dir = float(np.sign(late - early))
    except Exception:
        mg, p_nl, p_ch, gam_dir, rho_g = None, np.nan, np.nan, np.nan, np.nan
    se_ar = mq.bse['yr'] * np.sqrt((1 + ac1) / (1 - ac1)) if ac1 > 0 else mq.bse['yr']
    p_ar = float(2 * stats.norm.sf(abs(mq.params['yr'] / se_ar)))
    rows.append(dict(species=sp, beta=mq.params['yr'], p_quasi=mq.pvalues['yr'], p_hac=mh.pvalues['yr'], p_ar1=p_ar,
                     se_quasi=mq.bse['yr'], se_hac=mh.bse['yr'], ac1=ac1, p_nonlinear=p_nl, p_gam_change=p_ch,
                     gam_dir=gam_dir, early_late_change=None))
    common = sp.split(', (')[0]
    if mg is not None and any(common.startswith(f) for f in FOCAL):
        yrs = np.arange(s.year.min(), s.year.max() + 1)
        info = dmatrix('cr(x, df=4) - 1', {'x': x.ravel()}).design_info
        sp_new = np.asarray(build_design_matrices([info], {'x': (yrs - 2010) / 10})[0]) - np.asarray(dmatrix('cr(x, df=4) - 1', {'x': x.ravel()})).mean(0)
        Xp = np.column_stack([np.ones(len(yrs)), np.full(len(yrs), s.exp_share.mean()), sp_new])
        eta = Xp @ mg.params
        V = mg.cov_params() * phi * infl
        se = np.sqrt(np.einsum('ij,jk,ik->i', Xp, V, Xp))
        inv = lambda z: 100 / (1 + np.exp(-z))
        for yy, e_, s_ in zip(yrs, eta, se):
            curves.append(dict(species=common, year=int(yy), fit=inv(e_), lo=inv(e_ - 1.96 * s_), hi=inv(e_ + 1.96 * s_)))
A = pd.DataFrame(rows)
A['q_hac'] = multipletests(A.p_hac, method='fdr_bh')[1]
A['q_nonlinear'] = multipletests(A.p_nonlinear.fillna(1), method='fdr_bh')[1]
A['q_ar1'] = multipletests(A.p_ar1, method='fdr_bh')[1]
A['q_gam'] = multipletests(A.p_gam_change.fillna(1), method='fdr_bh')[1]
A = A.merge(T[['species', 'robust']], on='species')
A.to_csv('review_autocorr_gam.csv', index=False)
pd.DataFrame(curves).to_csv('review_gam_curves.csv', index=False)
rb = A[A.robust]
out['autocorr'] = dict(
    n_species=len(A), median_ac1=float(A.ac1.median()), median_ac1_robust=float(rb.ac1.median()),
    share_ac1_gt_0_3=float((A.ac1 > 0.3).mean()),
    robust_n=int(len(rb)), robust_still_q05_hac=int((rb.q_hac < 0.05).sum()),
    median_se_ratio_hac_vs_quasi=float((A.se_hac / A.se_quasi).median()),
    nonlinear_q05=int((A.q_nonlinear < 0.05).sum()), nonlinear_q05_robust=int((rb.q_nonlinear < 0.05).sum()),
    robust_still_q05_ar1=int((rb.q_ar1 < 0.05).sum()),
    robust_gam_change_same_dir=int(((rb.q_gam < 0.05) & (rb.gam_dir == np.sign(rb.beta))).sum()))
print('1', out['autocorr'])

# ---------------- 2. hierarchical regional model
R = pd.read_csv('regional_species.csv')
E = pd.read_csv('regional_effort.csv')
E['exp_share'] = np.where(E.exp > 1, E.exp / E.n, E.exp)
E = E[(E.n >= 10) & (E.island != 'Martinique')]
R = R[R.island != 'Martinique']
reg_rows = []
for sp, s in R.groupby('species'):
    g = E.merge(s[['island', 'year', 'k']], on=['island', 'year'], how='left').fillna({'k': 0})
    g['k'] = np.minimum(g.k, g.n)
    if g.k.sum() < 200 or g[g.island == 'Dominica'].k.sum() < 30 or g[g.k > 0].island.nunique() < 4:
        continue
    g['yr'] = (g.year - 2010) / 10
    g['dom'] = (g.island == 'Dominica').astype(float)
    X = pd.get_dummies(g.island, drop_first=True, dtype=float)
    X['yr'] = g.yr
    X['dom_yr'] = g.dom * g.yr
    X['exp'] = g.exp_share.fillna(g.exp_share.mean())
    X = sm.add_constant(X)
    y = np.column_stack([g.k, g.n - g.k])
    try:
        m = sm.GLM(y, X, family=sm.families.Binomial()).fit(scale='X2')
    except Exception:
        continue
    reg_rows.append(dict(species=sp, region_or=np.exp(m.params['yr']), dom_dev_or=np.exp(m.params['dom_yr']),
                         dom_dev_lo=np.exp(m.conf_int().loc['dom_yr', 0]), dom_dev_hi=np.exp(m.conf_int().loc['dom_yr', 1]),
                         p_dev=m.pvalues['dom_yr'], p_region=m.pvalues['yr']))
H = pd.DataFrame(reg_rows)
H['q_dev'] = multipletests(H.p_dev, method='fdr_bh')[1]
H['q_region'] = multipletests(H.p_region, method='fdr_bh')[1]
H['dominica_or'] = H.region_or * H.dom_dev_or
H.sort_values('dom_dev_or').to_csv('review_regional_hier.csv', index=False)
out['regional_hier'] = dict(n_species=len(H), dom_more_positive=int(((H.q_dev < 0.05) & (H.dom_dev_or > 1)).sum()),
                            dom_more_negative=int(((H.q_dev < 0.05) & (H.dom_dev_or < 1)).sum()))
print('2', out['regional_hier'])
show = ['Yellowtail Snapper', 'Schoolmaster', 'Graysby', 'Bar Jack', 'Horse-eye Jack', 'Mutton Snapper', 'Great Barracuda',
        'Black Margate', 'Spotted Goatfish', 'Cleaning Goby', 'Sharknose Goby', 'Trumpetfish', 'Eyed Flounder',
        'Flying Gurnard', 'Green Razorfish', 'Bandtail Puffer', 'Queen Parrotfish', 'Stoplight Parrotfish', 'Coney', 'Red Hind']
print(H[H.species.isin(show)][['species', 'region_or', 'dominica_or', 'dom_dev_or', 'q_dev', 'q_region']].round(3).to_string())

# ---------------- 4. effort-corrected richness (incidence frequency data)
def rare(k, n, m):
    k = k[k > 0]
    lc = lambda a, b: gammaln(a + 1) - gammaln(b + 1) - gammaln(a - b + 1)
    with np.errstate(invalid='ignore'):
        term = np.where(n - k >= m, np.exp(lc(n - k, m) - lc(n, m)), 0.0)
    return float(np.sum(1 - term))

def chao2(k, n):
    k = k[k > 0]
    q1, q2 = (k == 1).sum(), (k == 2).sum()
    a = (n - 1) / n
    return float(len(k) + (a * q1 * q1 / (2 * q2) if q2 > 0 else a * q1 * (q1 - 1) / 2))

ex = d[~d.species.str.contains(r'Juvenile|Complex|unidentified|sp\.|spp', case=False)]
bins = [(1994, 2000), (2001, 2004), (2005, 2008), (2009, 2012), (2013, 2016), (2017, 2020), (2021, 2024), (2025, 2026)]
rich = []
for a, b in bins:
    s = ex[(ex.year >= a) & (ex.year <= b)].groupby('species').k.sum().values
    n = int(eff[(eff.year >= a) & (eff.year <= b)].n_all.sum())
    ne = eff[(eff.year >= a) & (eff.year <= b)]
    rich.append(dict(period=f'{a}–{str(b)[2:]}', surveys=n, observed=int((s > 0).sum()), rarefied_30=rare(s, n, 30),
                     rarefied_60=rare(s, n, 60), chao2=chao2(s, n), exp_share=float(ne.n_exp.sum() / n)))
Rp = pd.DataFrame(rich)
Rp.to_csv('review_richness_period.csv', index=False)
# per-year rarefied richness at 10 surveys, modelled on year + expert share
yr = []
for y, s in ex.groupby('year'):
    n = int(eff.loc[eff.year == y, 'n_all'].iloc[0])
    if n >= 10:
        yr.append(dict(year=y, n=n, r10=rare(s.k.values, n, 10), exp_share=float(eff.loc[eff.year == y, 'exp_share'].iloc[0])))
Ry = pd.DataFrame(yr)
m = sm.OLS(Ry.r10, sm.add_constant(pd.DataFrame({'yr': (Ry.year - 2010) / 10, 'exp': Ry.exp_share}))).fit(cov_type='HAC', cov_kwds={'maxlags': 2})
Ry.to_csv('review_richness_year.csv', index=False)
out['richness'] = dict(periods=Rp.round(1).to_dict('records'), slope_per_decade_r10=float(m.params['yr']),
                       ci=[float(x) for x in m.conf_int().loc['yr']], p=float(m.pvalues['yr']),
                       exp_coef=float(m.params['exp']), p_exp=float(m.pvalues['exp']), mean_r10=float(Ry.r10.mean()))
print('4', Rp.round(1).to_string(), '\n', out['richness']['slope_per_decade_r10'], out['richness']['ci'], out['richness']['p'])

# ---------------- 5. sensitivity
def refit(g):
    res = {}
    for sp, s in g.groupby('species'):
        if sp not in set(robust.species):
            continue
        s = s[s.n > 0]
        try:
            m = glm(s)
            res[sp] = (m.params['yr'], m.pvalues['yr'])
        except Exception:
            pass
    return res

busy = eff[eff.n_all >= 10].nlargest(5, 'n_all').year.tolist()
scen = {
    'Min 5 surveys/year': grid(5),
    'Min 20 surveys/year': grid(20),
    'Drop 5 busiest years': grid(years=[y for y in eff.loc[eff.n_all >= 10, 'year'] if y not in busy]),
    'From 2000 only': grid(years=[y for y in eff.loc[eff.n_all >= 10, 'year'] if y >= 2000]),
    'Drop 2025–26': grid(years=[y for y in eff.loc[eff.n_all >= 10, 'year'] if y <= 2024]),
    'Drop 2017–18 (Maria)': grid(years=[y for y in eff.loc[eff.n_all >= 10, 'year'] if y not in (2017, 2018)]),
}
base = robust.set_index('species').beta_decade
sens = []
for name, g in scen.items():
    r = refit(g)
    ps = pd.Series({k: v[1] for k, v in r.items()})
    q = pd.Series(multipletests(ps.values, method='fdr_bh')[1], index=ps.index)
    same = sum(np.sign(r[k][0]) == np.sign(base[k]) for k in r)
    sig = sum((np.sign(r[k][0]) == np.sign(base[k])) and q[k] < 0.05 for k in r)
    corr = stats.spearmanr([base[k] for k in r], [r[k][0] for k in r]).statistic
    sens.append(dict(scenario=name, species=len(r), same_sign=int(same), same_sign_q05=int(sig), rho=float(corr)))
S = pd.DataFrame(sens)
S.to_csv('review_sensitivity.csv', index=False)
out['sensitivity'] = dict(busiest_years=busy, table=S.round(3).to_dict('records'))
print('5', busy, '\n', S.round(3).to_string())
json.dump(out, open('review_summary.json', 'w'), indent=1, default=float)

# ---------------- 2b. Dominica against between-island variation (random-slopes view)
# For each species: Dominica's slope compared with the mean and spread of the other islands'
# slopes, with a DerSimonian-Laird random-effects estimate of between-island variance.
Rall = pd.read_csv('regional_trends_all.csv')
rows = []
for sp, s in Rall.groupby('species'):
    o = s[s.island != 'Dominica'].dropna()
    dm = s[s.island == 'Dominica']
    if len(o) < 4 or dm.empty:
        continue
    w = 1 / o.se ** 2
    mu_fe = np.sum(w * o.b) / w.sum()
    Q = np.sum(w * (o.b - mu_fe) ** 2)
    tau2 = max(0.0, (Q - (len(o) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    ws = 1 / (o.se ** 2 + tau2)
    mu = np.sum(ws * o.b) / ws.sum()
    b_d, se_d = float(dm.b.iloc[0]), float(dm.se.iloc[0])
    # predictive distribution for a new island: mean mu, variance tau2 + var(mu)
    sd_pred = np.sqrt(tau2 + 1 / ws.sum() + se_d ** 2)
    z = (b_d - mu) / sd_pred
    rows.append(dict(species=sp, n_islands=len(o) + 1, dominica_or=np.exp(b_d), others_or=np.exp(mu), tau=np.sqrt(tau2),
                     z=z, p=float(2 * stats.norm.sf(abs(z))), outside_range=bool(b_d > o.b.max() or b_d < o.b.min())))
P = pd.DataFrame(rows)
P['q'] = multipletests(P.p, method='fdr_bh')[1]
P.sort_values('z').to_csv('review_regional_predictive.csv', index=False)
out['regional_predictive'] = dict(n_species=len(P), dom_higher_q05=int(((P.q < 0.05) & (P.z > 0)).sum()),
                                  dom_lower_q05=int(((P.q < 0.05) & (P.z < 0)).sum()),
                                  dom_higher_p05=int(((P.p < 0.05) & (P.z > 0)).sum()), dom_lower_p05=int(((P.p < 0.05) & (P.z < 0)).sum()),
                                  outside_range=int(P.outside_range.sum()))
print('2b', out['regional_predictive'])
print(P[P.species.isin(show)][['species', 'dominica_or', 'others_or', 'z', 'p', 'q', 'outside_range']].round(3).to_string())
json.dump(out, open('review_summary.json', 'w'), indent=1, default=float)

# fished vs unfished: are fished species systematically higher in Dominica than the region predicts?
t = pd.read_csv('traits_species.csv')  # from traits.py
t['common'] = t.species.str.split(r', \(').str[0]
P = P.merge(t[['common', 'fished']], left_on='species', right_on='common', how='left')
f, o = P[P.fished == 1].z, P[P.fished == 0].z
out['regional_predictive']['fished'] = dict(n=len(f), mean_z=float(f.mean()), share_pos=float((f > 0).mean()),
                                            wilcoxon_p=float(stats.wilcoxon(f).pvalue))
out['regional_predictive']['unfished'] = dict(n=len(o), mean_z=float(o.mean()), share_pos=float((o > 0).mean()),
                                              wilcoxon_p=float(stats.wilcoxon(o).pvalue))
out['regional_predictive']['fished_vs_unfished_mw_p'] = float(stats.mannwhitneyu(f, o).pvalue)
json.dump(out, open('review_summary.json', 'w'), indent=1, default=float)
