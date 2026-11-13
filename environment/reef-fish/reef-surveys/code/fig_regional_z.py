"""Figure 4: Dominica's trend relative to six neighboring islands for fished and unfished species."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P = pd.read_csv('review_regional_predictive.csv')
t = pd.read_csv('traits_species.csv'); t['species'] = t.species.str.split(r', \(').str[0]
P2 = P.merge(t[['species', 'fished']], on='species', how='left').dropna(subset=['fished'])
P2 = P2[~P2.species.str.contains('Juvenile|Complex')].copy()
rng = np.random.default_rng(1); P2['y'] = P2.fished + rng.uniform(-0.18, 0.18, len(P2))
fig, ax = plt.subplots(figsize=(7, 3.4))
for f, c in [(0, '#c27c2c'), (1, '#2a7f8f')]:
    s = P2[P2.fished == f]
    ax.scatter(s.z.clip(-5, 5), s.y, s=18, alpha=.6, color=c, edgecolor='none')
    ax.plot([s.z.median()] * 2, [f - .3, f + .3], color='k', lw=2)
    ax.text(5.3, f, f'n = {len(s)}', va='center', fontsize=9)
for sp in ['Yellowtail Snapper', 'Schoolmaster', 'Red Hind', 'Bandtail Puffer']:
    r = P2[P2.species == sp].iloc[0]
    ax.annotate(sp, (np.clip(r.z, -5, 5), r.y), xytext=(0, 16), textcoords='offset points', ha='center', fontsize=8,
                arrowprops=dict(arrowstyle='-', lw=.5))
ax.axvline(0, color='grey', lw=.8, ls='--'); ax.set_yticks([0, 1]); ax.set_yticklabels(['Unfished', 'Fished'])
ax.set_xlabel('Dominica trend relative to six neighboring islands (z)'); ax.set_xlim(-5.2, 6.2); ax.set_ylim(-.6, 1.6)
for s_ in ['top', 'right']: ax.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig('/home/claude/out/fig4_regional_z.png', dpi=200)
