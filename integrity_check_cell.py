# Run in the Kaggle notebook on each prepared dataset folder. Prints the integrity table used in Chapter Four (Table 4.3).
import os, glob, csv, yaml
ROOTS = {  # name: folder containing data.yaml, images/ and labels/
 'tomato_leaf':'/kaggle/working/tomato_leaf',
 'tomato_fruit':'/kaggle/working/tomato_fruit',
 'human_day':'/kaggle/working/human_day',
 'human_night':'/kaggle/working/human_night',
 'animal_day':'/kaggle/working/datasets/animal/day_full',
 'animal_night':'/kaggle/working/datasets/animal/night_full',
}
IMG = ('.jpg','.jpeg','.png','.bmp')
rows=[]
for name,root in ROOTS.items():
    y=yaml.safe_load(open(f'{root}/data.yaml')); nc=len(y['names'])
    for split in ('train','valid','val','test'):
        idir=f'{root}/{split}/images' if os.path.isdir(f'{root}/{split}/images') else f'{root}/images/{split}'
        ldir=idir.replace('images','labels')
        if not os.path.isdir(idir): continue
        imgs={os.path.splitext(f)[0] for f in os.listdir(idir) if f.lower().endswith(IMG)}
        labs={os.path.splitext(f)[0] for f in os.listdir(ldir) if f.endswith('.txt')} if os.path.isdir(ldir) else set()
        invalid=empty=boxes=0
        for s in labs & imgs:
            lines=[l.split() for l in open(f'{ldir}/{s}.txt') if l.strip()]
            if not lines: empty+=1
            for p in lines:
                try:
                    c=int(p[0]); v=list(map(float,p[1:]))
                    ok=len(p)==5 and 0<=c<nc and all(0<=t<=1 for t in v)
                except Exception: ok=False
                invalid+= (not ok); boxes+= ok
        rows.append([name,split,len(imgs),len(labs),len(imgs&labs),len(imgs-labs),len(labs-imgs),invalid,empty,boxes])
hdr=['dataset','split','images','labels','matched','orphan_images','orphan_labels','invalid_lines','empty_labels','boxes']
print(('{:<14}{:<7}'+'{:>14}'*8).format(*hdr))
for r in rows: print(('{:<14}{:<7}'+'{:>14}'*8).format(*map(str,r)))
csv.writer(open('/kaggle/working/integrity_report.csv','w')).writerows([hdr]+rows)
