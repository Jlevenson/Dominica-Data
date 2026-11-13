import json, pandas as pd, numpy as np, warnings, statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')
raw=json.load(open('/tmp/claude-tool-results/d4e88a66-dff1-588b-bbcb-ed217c0a46e5/mcp-remote-devices-Claude_Browser__javascript_tool-1794555590240-ca3ce354.txt'))
t=raw[0]['text']; t=t[:t.rfind('"')+1]; d=json.loads(json.loads(t))
INSIDE={'71120005','71120004','71120001','71120009','71120081','71120015','71120043','71120003','71120013','71120048','71120008','71120090','71120047','71120088','71120046','71120092'}
names=pd.read_csv('site_counts_by_year.csv').drop_duplicates('code').assign(code=lambda x:x.code.astype(str)).set_index('code').site
mid={1994:1997,2001:2002.5,2005:2006.5,2009:2010.5,2013:2014.5,2017:2018.5,2021:2022.5,2025:2025.5}
sp_rows=[]; sv=[]
for l in d['out']:
    parts=l.split('|')
    if parts[2]=='ERR': print('ERR',l); continue
    s,a,h,spl=parts; eSA,eSO,nSA,nSO=map(int,h.split(',')); SA=eSA+nSA; n=SA+eSO+nSO
    if n==0: continue
    sv.append(dict(code=s,start=int(a),n=n,SA=SA,exp=(eSA+eSO)/n))
    for kv in spl.split(';'):
        if kv.count('=')<2: continue
        nm,sf,den=kv.rsplit('=',2); sp_rows.append(dict(code=s,start=int(a),species=nm,k=round(float(sf)/100*SA)))
SV=pd.DataFrame(sv); SV['inside']=SV.code.isin(INSIDE).astype(int); SV['yr']=(SV.start.map(mid)-2010)/10; SV['site']=SV.code.map(names)
SP=pd.DataFrame(sp_rows)
SV.to_csv('mpa_site_period_effort.csv',index=False); SP.to_csv('mpa_site_period_species.csv',index=False)
print('site-periods',len(SV),'surveys inside',SV[SV.inside==1].n.sum(),'outside',SV[SV.inside==0].n.sum())
print(SV.groupby(['start','inside']).n.sum().unstack().fillna(0).astype(int).to_string())
print('outside surveys by site:'); print(SV[SV.inside==0].groupby('site').n.sum().sort_values(ascending=False).to_string())
# grid
tot=SP.groupby('species').k.sum(); keep=tot[tot>=40].index
G=pd.MultiIndex.from_product([keep,SV.index],names=['species','i']).to_frame(index=False)
G=G.merge(SV.reset_index().rename(columns={'index':'i'}),on='i')
G=G.merge(SP,on=['species','code','start'],how='left').fillna({'k':0}); G['k']=np.minimum(G.k,G.n)
def fit(g,drop_cc=False):
    if drop_cc: g=g[g.code!='71120010']
    X=sm.add_constant(pd.DataFrame({'inside':g.inside,'yr':g.yr,'exp':g.exp,'ixyr':g.inside*g.yr}))
    m=sm.GLM(np.column_stack([g.k,g.n-g.k]),X,family=sm.families.Binomial()).fit(scale='X2')
    return m
rows=[]
for sp,g in G.groupby('species'):
    if (g[g.inside==0].k.sum()<5) and (g[g.inside==1].k.sum()<5): continue
    try:
        m=fit(g); m2=fit(g,True)
        # main effect at 2010 (yr=0) because yr centered
        rows.append(dict(species=sp,sf_in=100*g[g.inside==1].k.sum()/g[g.inside==1].n.sum(),sf_out=100*g[g.inside==0].k.sum()/g[g.inside==0].n.sum(),
            OR_inside=np.exp(m.params.inside),p_inside=m.pvalues.inside,OR_inside_noCC=np.exp(m2.params.inside),p_inside_noCC=m2.pvalues.inside,
            OR_trend_diff=np.exp(m.params.ixyr),p_trend_diff=m.pvalues.ixyr,records=int(g.k.sum())))
    except Exception as e: pass
R=pd.DataFrame(rows); R['q_inside']=multipletests(R.p_inside,method='fdr_bh')[1]; R['q_trend']=multipletests(R.p_trend_diff,method='fdr_bh')[1]
R['robust_inside']=(R.q_inside<0.05)&(np.sign(np.log(R.OR_inside))==np.sign(np.log(R.OR_inside_noCC)))&(R.p_inside_noCC<0.05)
R.to_csv('mpa_species.csv',index=False)
fam=pd.read_csv('species_trends.csv')[['common','family']].drop_duplicates().set_index('common').family
R['family']=R.species.map(fam)
targets={'Snapper':'Snappers','Seabass':'Groupers, hinds & seabass','Parrotfish':'Parrotfish','Jack':'Jacks','Barracuda':'Barracuda','Grunt':'Grunts','Triggerfish':'Triggerfish','Porgy':'Porgies','Goatfish':'Goatfish','Mackerel':'Mackerel'}
print(R.sort_values('OR_inside')[['species','family','sf_in','sf_out','OR_inside','q_inside','OR_inside_noCC','OR_trend_diff','q_trend','robust_inside','records']].round(3).to_string(index=False))
