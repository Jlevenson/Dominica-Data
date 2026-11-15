"""Build the dashboard data files (environment/reef-fish/reef-surveys/*.csv|json) from the analysis outputs."""
import json, shutil, os
import pandas as pd, numpy as np
OUT = '/home/claude/out/dash/'; os.makedirs(OUT, exist_ok=True)
REPO = '/home/claude/dominica-data/environment/reef-fish/reef-surveys/'
grp = pd.read_csv('species_groups.csv').set_index('common').group
fished = lambda s: 'Fished' if grp.get(s) == 'Fished' else 'Not fished'

shutil.copy('out_effort.csv', OUT + 'effort.csv'); shutil.copy('out_lionfish.csv', OUT + 'lionfish.csv')
for a, b in [('out_trends.json', 'trends.json'), ('out_periods.json', 'periods.json'), ('out_groups.json', 'groups.json')]:
    shutil.copy(a, OUT + b)

old = pd.read_csv(REPO + 'reserve.csv').species
M = pd.read_csv('mpa_species.csv').set_index('species').loc[old]
R = pd.DataFrame({'species': old.values, 'sf_in': M.sf_in.round(3).values, 'sf_out': M.sf_out.round(3).values,
                  'OR_inside': M.OR_inside.round(3).values, 'robust': M.robust_inside.values,
                  'widened': ((M.q_trend < 0.05) & (M.OR_trend_diff > 1)).values, 'records': M.records.values,
                  'group': [fished(s) for s in old]})
R.to_csv(OUT + 'reserve.csv', index=False)

pd.read_csv('regional_trends_focal.csv').round(3).to_csv(OUT + 'regional.csv', index=False)

oldh = pd.read_csv(REPO + 'habitat.csv')[['species', 'group']]
H = pd.read_csv('habitat_matched.csv').set_index('species')
h = oldh.join(H[['sf_in_wall', 'sf_in_slope', 'sf_out', 'OR_inside_matched', 'q_matched']], on='species').round(3)
h.to_csv(OUT + 'habitat.csv', index=False)

P = pd.read_csv('review_regional_predictive.csv'); g = pd.read_csv('species_groups.csv'); g = g[g.group.notna()]
P = P[~P.species.str.contains('Juvenile|Complex|Unidentified|Sea Turtle|Hybrid')]
P = P.merge(g.assign(species=g.common, fished=(g.group == 'Fished').astype(float))[['species', 'fished']], on='species')
P[['species', 'fished', 'dominica_or', 'others_or', 'z', 'p']].round(3).sort_values('z').to_csv(OUT + 'regional_z.csv', index=False)

pd.read_csv('review_gam_curves.csv').round(2).to_csv(OUT + 'curves.csv', index=False)
pd.read_csv('functional_groups.csv').round(4).to_csv(OUT + 'fgroups.csv', index=False)

ws = json.load(open('within_site_all_summary.json')); rv = json.load(open('review_summary.json'))
S = pd.read_csv('review_sensitivity.csv').set_index('scenario'); ac = rv['autocorr']; n = ws['robust_compared']
rows = [('Same sites (site fixed effects)', ws['robust_same_sign_q05'], n, f"{ws['robust_same_sign']} kept their direction"),
        ('Year-to-year autocorrelation', ac['robust_still_q05_ar1'], ac['robust_n'], f"Median lag-1 autocorrelation {ac['median_ac1_robust']:.2f}"),
        ('Minimum 5 or 20 surveys per year', min(S.loc['Min 5 surveys/year', 'same_sign_q05'], S.loc['Min 20 surveys/year', 'same_sign_q05']), n, 'Instead of 10'),
        ('Without 2017–18 (Hurricane Maria)', S.loc['Drop 2017–18 (Maria)', 'same_sign_q05'], n, ''),
        ('Without 2025 (mostly experts)', S.loc['Drop 2025', 'same_sign_q05'], n, ''),
        ('From 2000 only', S.loc['From 2000 only', 'same_sign_q05'], n, f"{S.loc['From 2000 only', 'same_sign']} kept their direction"),
        ('Without the five busiest years', S.loc['Drop 5 busiest years', 'same_sign_q05'], n, f"Removes half of all surveys; {S.loc['Drop 5 busiest years', 'same_sign']} kept their direction")]
pd.DataFrame(rows, columns=['check', 'kept', 'of', 'note']).to_csv(OUT + 'robustness.csv', index=False)
print(open(OUT + 'robustness.csv').read()); print(R.to_string())
