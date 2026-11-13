import json, pandas as pd, numpy as np, warnings, statsmodels.api as sm
from scipy import stats
warnings.filterwarnings('ignore')
raw=json.load(open('/tmp/claude-tool-results/d4e88a66-dff1-588b-bbcb-ed217c0a46e5/mcp-remote-devices-Claude_Browser__javascript_tool-1794555981538-b2375572.txt'))
t=raw[0]['text']; t=t[:t.rfind('"')+1]; d=json.loads(json.loads(t))
NAMES={'7302':'St Lucia','7303':'St Vincent','7307':'Grenada','7104':'Saba','7106':'St Kitts','7105':'St Eustatius','7301':'Martinique'}
ef=[]; sp=[]
for l in d['out']:
    p=l.split('|')
    if p[2]=='ERR': print('ERR',l); continue
    z,y,h,spl=p; eSA,eSO,nSA,nSO=map(int,h.split(',')); SA=eSA+nSA; n=SA+eSO+nSO
    if n==0: continue
    ef.append(dict(island=NAMES[z],year=int(y),n=n,SA=SA,exp=(eSA+eSO)/n))
    for kv in spl.split(';'):
        if kv.count('=')<2: continue
        nm,sf,den=kv.rsplit('=',2); sp.append(dict(island=NAMES[z],year=int(y),species=nm,k=min(round(float(sf)/100*SA),n)))
E=pd.DataFrame(ef); S=pd.DataFrame(sp)
# add Dominica
dom=pd.read_csv('reef_dominica_species_year_long.csv'); dom=dom[dom.level=='All']; dom['species']=dom.species.str.split(r', \(').str[0]
e2=pd.read_csv('effort_by_year.csv'); e2['exp']=e2.n_exp/e2.n_all
E=pd.concat([E,e2.rename(columns={'n_all':'n','n_sa':'SA'})[['year','n','SA','exp']].assign(island='Dominica')])
dd=dom.merge(e2[['year','n_sa','n_all']],on='year'); dd['k']=(dd.sf/100*dd.n_sa).round().clip(upper=dd.n_all)
S=pd.concat([S,dd[['year','species','k']].assign(island='Dominica')])
E.to_csv('regional_effort.csv',index=False); S.to_csv('regional_species.csv',index=False)
print(E.groupby('island').n.sum().sort_values(ascending=False).to_string())
print(E[E.n>=10].groupby('island').year.agg(['min','max','count']).to_string())
def trend(isl,sp_):
    e=E[(E.island==isl)&(E.n>=10)]
    if len(e)<6: return None
    x=e.merge(S[(S.island==isl)&(S.species==sp_)][['year','k']],on='year',how='left').fillna({'k':0})
    if x.k.sum()<20 or (x.k>0).sum()<4: return None
    X=sm.add_constant(pd.DataFrame({'yr':(x.year-2010)/10,'exp':x.exp}))
    try: m=sm.GLM(np.column_stack([x.k,x.n-x.k]),X,family=sm.families.Binomial()).fit(scale='X2')
    except Exception: return None
    return m.params.yr, m.bse.yr, 100*x.k.sum()/x.n.sum()
FOC=['Spotted Goatfish','Cleaning Goby','Sharknose Goby','Eyed Flounder','Flying Gurnard','Green Razorfish','Bandtail Puffer','Spotted Trunkfish','Sand Diver','Trumpetfish','Yellow Goatfish','Peacock Flounder','Brown Chromis','Yellowtail Snapper','Mutton Snapper','Schoolmaster','Queen Parrotfish','Stoplight Parrotfish','Graysby','Coney','Red Hind','Great Barracuda','Bar Jack','Black Margate','Red Lionfish (exotic)']
isl=['Dominica','St Lucia','St Vincent','Grenada','Saba','St Kitts','St Eustatius']
rows=[]
for s in FOC:
    for i in isl:
        r=trend(i,s)
        if r: rows.append(dict(species=s,island=i,OR=np.exp(r[0]),lo=np.exp(r[0]-1.96*r[1]),hi=np.exp(r[0]+1.96*r[1]),sf=r[2]))
R=pd.DataFrame(rows); R.to_csv('regional_trends_focal.csv',index=False)
W=R.pivot(index='species',columns='island',values='OR').reindex(FOC)[isl].round(2); print(W.to_string())
# all-species correlation: Dominica vs mean of other islands (common species)
allsp=S.groupby('species').k.sum(); allsp=allsp[allsp>=200].index
rows=[]
for s in allsp:
    for i in isl:
        r=trend(i,s)
        if r and r[1]<3: rows.append(dict(species=s,island=i,b=r[0],se=r[1]))
B=pd.DataFrame(rows); B.to_csv('regional_trends_all.csv',index=False)
P=B.pivot(index='species',columns='island',values='b')
oth=[c for c in isl if c!='Dominica' and c in P]
P['region_mean']=P[oth].mean(1); P['n_isl']=P[oth].notna().sum(1)
Q=P[P.Dominica.notna()&(P.n_isl>=3)]
rho,p=stats.spearmanr(Q.Dominica,Q.region_mean); print('species',len(Q),'Dominica vs regional mean trend rho',round(rho,3),'p',p)
print('pairwise rho with Dominica:',{c:round(stats.spearmanr(P[['Dominica',c]].dropna().Dominica,P[['Dominica',c]].dropna()[c])[0],2) for c in oth})
