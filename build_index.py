import json, glob, os, datetime
files = sorted(glob.glob('data/20??-??-??.json'), reverse=True)
dates = []
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    assert len(d['items']) == 7, f
    for it in d['items']:
        for k in ['rank','id','title','category','why','easy','normal','original','url']:
            assert it.get(k), (f, it.get('id'), k)
    dates.append({"date": d['date'], "headline": d.get('headline',''),
                  "top3": [i['title'] for i in sorted(d['items'], key=lambda x: x['rank'])[:3]],
                  "categories": sorted({i['category'] for i in d['items']})})
idx = {"updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='minutes'),
       "dates": dates}
json.dump(idx, open('data/index.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(dates), [x['date'] for x in dates])
