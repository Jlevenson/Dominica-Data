"""Figures 1-3 and Fig. S1 for the Dominica reef fish paper (analysis period 1994-2025).

Fig. 1: surveys per year by surveyor experience (effort_by_year.csv)
Fig. 2: share of surveys recording red lionfish (out_lionfish.csv)
Fig. 3: smoothed trajectories for nine species (review_gam_curves.csv)
Fig. S1: mean sighting frequency by species group and period (summary.json)
"""
import json
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = '/home/claude/out/'
TEAL, ORANGE = '#2a7f8f', '#c27c2c'


def tidy(ax):
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.grid(axis='y', color='#e5e5e5', lw=.8)
    ax.set_axisbelow(True)


# Fig. 1 effort
e = pd.read_csv('effort_by_year.csv')
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar(e.year, e.n_exp, color=TEAL, label='Expert')
ax.bar(e.year, e.n_nov, bottom=e.n_exp, color=ORANGE, label='Novice')
ax.set_ylabel('Surveys per year'); ax.legend(frameon=False, loc='upper left'); tidy(ax)
ax.set_xlim(1992.5, 2026.5)
plt.tight_layout(); plt.savefig(OUT + 'fig1_effort.png', dpi=200); plt.close()

# Fig. 2 lionfish
L = pd.read_csv('out_lionfish.csv'); L = L[L.surveys >= 5]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(L.year, L.sf.clip(upper=100), color=TEAL, lw=1.6, zorder=2)
ax.scatter(L.year, L.sf.clip(upper=100), s=L.surveys * 2.2, color=TEAL, alpha=.75, edgecolor=TEAL, zorder=3)
for n_ in [20, 100, 200]:
    ax.scatter([], [], s=n_ * 2.2, color=TEAL, alpha=.75, label=f'{n_} surveys')
ax.legend(frameon=False, loc='upper left', labelspacing=1.4, borderpad=1)
ax.set_ylim(0, 100); ax.set_xlim(1995.5, 2026.5); ax.set_ylabel('% of surveys recording lionfish')
ax.grid(color='#e5e5e5', lw=.8); ax.set_axisbelow(True)
for s in ['top', 'right']: ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(OUT + 'fig2_lionfish.png', dpi=200); plt.close()

# Fig. 3 trajectories
C = pd.read_csv('review_gam_curves.csv')
order = ['Red Lionfish (exotic)', 'Spotted Goatfish', 'Yellowtail Snapper', 'Schoolmaster', 'Cleaning Goby',
         'Sharknose Goby', 'Eyed Flounder', 'Trumpetfish', 'Bar Jack']
fig, axs = plt.subplots(3, 3, figsize=(10, 8), sharex=True, sharey=True)
for ax, sp in zip(axs.flat, order):
    s = C[C.species == sp]
    ax.fill_between(s.year, s.lo, s.hi, color=TEAL, alpha=.2, lw=0)
    ax.plot(s.year, s.fit, color=TEAL, lw=2)
    ax.axvline(2011, color=ORANGE, ls='--', lw=.9); ax.axvline(2017.7, color='grey', ls=':', lw=.9)
    ax.set_title(sp.replace(' (exotic)', ''), fontsize=11); ax.set_ylim(0, 100)
    ax.grid(color='#e5e5e5', lw=.8)
for ax in axs[:, 0]: ax.set_ylabel('% of surveys')
fig.text(.5, .01, 'Dashed: first lionfish record (2011). Dotted: Hurricane Maria (Sept 2017). Shading: 95% CI.',
         ha='center', fontsize=9)
plt.tight_layout(rect=(0, .03, 1, 1)); plt.savefig(OUT + 'fig4_trajectories.png', dpi=200); plt.close()

# Fig. S1 groups
G = pd.DataFrame(json.load(open('summary.json'))['groups'])
cols = {'Parrotfish': TEAL, 'Groupers & hinds': ORANGE, 'Snappers': '#6b5ca5', 'Grunts': '#3f8f4f', 'Large predators': '#a8434a'}
periods = list(dict.fromkeys(G.period))
fig, ax = plt.subplots(figsize=(8, 3.8))
for gname, c in cols.items():
    s = G[G.group == gname].set_index('period').reindex(periods)
    if s.sf.notna().any():
        ax.plot(range(len(periods)), s.sf, '-o', color=c, lw=2, label=gname)
ax.set_xticks(range(len(periods))); ax.set_xticklabels(periods)
ax.set_ylabel('Mean sighting frequency (%)'); ax.set_ylim(0, None); ax.legend(frameon=False, ncol=3, loc='upper left')
ax.grid(color='#e5e5e5', lw=.8); ax.set_axisbelow(True)
for s in ['top', 'right']: ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(OUT + 'fig3_groups.png', dpi=200); plt.close()
print('figures written')
