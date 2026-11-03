"""Original motion design. Run after both evidence scripts. No browser automation."""
from pathlib import Path
import sys, math, json, subprocess, functools
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.render-deps'))
import imageio_ffmpeg
W,H=1600,900
INK='#15364B'; MUT='#58758A'; BLUE='#34749F'; GREEN='#287863'; LINE='#D7E4ED'; PALE='#E8F2F8'
FONT='/System/Library/Fonts/Avenir Next.ttc'
@functools.lru_cache(None)
def font(s,bold=False): return ImageFont.truetype(FONT,int(s),index=2 if bold else 7)
def text(im,x,y,s,size=24,color=INK,bold=False,anchor=None):
    ImageDraw.Draw(im).text((x,y),str(s),font=font(size,bold),fill=color,anchor=anchor)
def rect(im,box,fill='white',r=22,outline=None): ImageDraw.Draw(im).rounded_rectangle(box,r,fill=fill,outline=outline,width=1)
def card(im,box,fill='white',r=28):
    x,y,x2,y2=box
    rect(im,(x+2,y+12,x2+2,y2+12),'#DDE8F0',r)
    rect(im,box,fill,r,'#D7E4ED')
def line(im,pts,color=LINE,width=2): ImageDraw.Draw(im).line(pts,fill=color,width=width)
def pill(im,x,y,label,color=BLUE,fill=PALE,size=19):
    width=ImageDraw.Draw(im).textlength(label,font=font(size,True))+34
    rect(im,(x,y,x+width,y+39),fill,19)
    text(im,x+17,y+6,label,size,color,True)
    return width

def ease(x): return 1-(1-max(0,min(1,x)))**3

y,x=np.mgrid[0:H,0:W]; glow=np.exp(-((x-1180)**2+(y-280)**2)/(2*450**2)); grad=y/H
bg=np.zeros((H,W,3),dtype=np.uint8)
for k,(a,b) in enumerate([(248,232),(251,241),(253,248)]): bg[:,:,k]=a+(b-a)*grad-glow*(8 if k==0 else 4 if k==1 else 0)
BASE=Image.fromarray(bg)
# Fine orbit geometry adds depth without competing with the content.
d=ImageDraw.Draw(BASE)
for rr in [310,390,480]: d.ellipse((1200-rr,330-rr,1200+rr,330+rr),outline='#DCE8F1',width=1)
ETL=json.loads((ROOT/'evidence/etl-run.json').read_text())
AI=json.loads((ROOT/'evidence/ai-run.json').read_text())
assert all(ETL['checks'].values()) and all(AI['checks'].values())

STORIES={
'etl':[
 ('DATA ENGINEERING','Clean data.','Ready to report.','One source. A clear path to trusted reporting.','Python  /  SQL  /  PostgreSQL'),
 ('01 / INGEST','Messy input.','Visible issues.','Start with the file your team actually receives.','12 fictional source rows'),
 ('02 / VALIDATE','Keep the good.','Explain the rest.','Validate fields and resolve repeated order IDs.','Every rejected row gets a reason'),
 ('03 / LOAD','Load once.','Run it again.','The same batch leaves the same eight orders.','Parameterized SQL  /  transactional writes'),
 ('04 / RECONCILE','Numbers that','tie together.','One SQL view. Totals checked against clean input.','No invented growth or performance metrics'),
 ('DELIVERY','A pipeline you','can inspect.','Source, validation report, SQL and run instructions.','Start with one source. Expand with confidence.')],
'ai':[
 ('AI WORKFLOW','From message','to saved record.','A small workflow. A decision you control.','Node.js  /  Telegraf  /  LLM API  /  Sheets'),
 ('01 / CAPTURE','Say it once.','Make it usable.','A free-text message becomes a structured draft.','English presentation of the verified prototype'),
 ('02 / REVIEW','See the action','before it runs.','Inspect the extracted fields before confirmation.','The model output is a fixed fixture in this replay'),
 ('03 / APPROVE','Your approval.','Then the write.','The original handler saves only after confirmation.','Zero writes before approval'),
 ('04 / VERIFY','Saved once.','Read back.','Check the resulting row in the same demo sheet.','One confirmed sample row  /  matching read-back'),
 ('DELIVERY','Useful AI.','Visible control.','A focused integration with a clear review step.','Map one workflow. Define its approval boundary.')]
}

def check(im,x,y,label,active=True):
    ImageDraw.Draw(im).ellipse((x,y,x+27,y+27),fill=GREEN if active else LINE)
    if active: line(im,[(x+7,y+14),(x+12,y+19),(x+21,y+8)],'white',3)
    text(im,x+42,y-2,label,23,INK if active else MUT)

def window(im,title,sub='LOCAL DEMO',x=700,y=190,w=820,h=530):
    card(im,(x,y,x+w,y+h))
    for i,c in enumerate(['#CEDDE8','#DDE7EE','#E9F0F4']): ImageDraw.Draw(im).ellipse((x+25+20*i,y+25,x+35+20*i,y+35),fill=c)
    text(im,x+105,y+14,title,24,INK,True)
    text(im,x+w-28,y+20,sub,14,MUT,True,anchor='rt')
    line(im,[(x,y+67),(x+w,y+67)])
    return x,y

def table(im,x,y,rows,widths,headers,highlight=None,row_h=58,size=22):
    total=sum(widths)
    rect(im,(x,y,x+total,y+42),'#EFF5F9',10)
    xx=x
    for h,w in zip(headers,widths): text(im,xx+15,y+9,h,15,MUT,True);xx+=w
    for i,row in enumerate(rows):
        yy=y+48+i*row_h
        if highlight==i: rect(im,(x,yy,x+total,yy+row_h-5),'#E2F1EB',9)
        xx=x
        for v,w in zip(row,widths): text(im,xx+15,yy+9,v,size,INK);xx+=w
        line(im,[(x,yy+row_h-2),(x+total,yy+row_h-2)],'#ECF1F5',1)

def etl_scene(im,scene,u):
    a=ease(u/1.8)
    if scene==0:
        # A dimensional data object, its input on the left and a resolved chart behind.
        card(im,(830,185,1465,617),'#F9FCFE')
        text(im,870,215,'REPORTING / READY',19,MUT,True)
        for i,v in enumerate([.77,1,.35]):
            xx=925+i*155; height=int(225*v*a)
            rect(im,(xx,555-height,xx+95,555),['#89B4D0',BLUE,'#BDD5E5'][i],16)
        card(im,(720,310,1030,655))
        pill(im,750,340,'VALIDATED',GREEN,'#E7F3ED',16)
        text(im,750,400,str(round(8*a)),122,INK,True)
        text(im,752,540,'clean orders',27,MUT)
        pill(im,1080,650,'Rerun verified  ·  8 stays 8',GREEN,'#DFEEE8',21)
    elif scene==1:
        window(im,'orders.csv','SYNTHETIC DATA')
        n=min(5,max(1,int(u*2)))
        rows=[['ORD-101',' Organic ','125.50'],['ORD-103','Referral','89.90'],['ORD-103','Referral','99.90'],['—','Organic','50.00'],['ORD-110','Referral','oops']]
        table(im,730,290,rows[:n],[235,260,260],['ORDER ID','CHANNEL','AMOUNT'],row_h=62,size=24)
        if u>2.3:pill(im,740,645,'Duplicates  /  missing IDs  /  invalid values','#996E45','#F7EDDF',18)
    elif scene==2:
        window(im,'Validation report','PYTHON')
        for i,(n,label,col) in enumerate([(8,'clean orders',BLUE),(3,'rejected rows','#AB7950'),(1,'duplicate resolved',GREEN)]):
            xx=735+i*255
            rect(im,(xx,292,xx+235,480),'#F1F6FA',17)
            text(im,xx+23,306,round(n*a),80,col,True)
            text(im,xx+23,414,label,21,MUT)
        for i,s in enumerate(['Normalize channel labels and currency','Reject invalid dates, IDs and amounts','Keep the last valid row for each order ID']):
            check(im,742,520+i*51,s,u>.35+i*.5)
    elif scene==3:
        window(im,'PostgreSQL load','PGLITE / LOCAL')
        text(im,744,288,'RUN 01',18,MUT,True);text(im,1120,288,'RUN 02',18,MUT,True)
        text(im,742,310,'8',120,INK,True);text(im,1115,310,'8' if u>1.6 else '…',120,BLUE,True)
        text(im,834,395,'rows',28,MUT);text(im,1207,395,'rows',28,MUT)
        line(im,[(950,399),(1055,399)],BLUE,4);line(im,[(1042,387),(1055,399),(1042,411)],BLUE,4)
        rect(im,(738,487,1482,574),'#193D54',15)
        text(im,766,505,'ON CONFLICT (order_id) DO UPDATE',28,'#E7F4FE',True)
        check(im,750,611,'Repeated batch: identical table',u>1.6)
    elif scene==4:
        window(im,'Revenue by channel','USD / FICTIONAL')
        maximum=max(float(r['revenue']) for r in ETL['totals'])
        for i,r in enumerate(ETL['totals']):
            yy=300+i*92
            text(im,742,yy,r['channel'].title(),24,INK,True)
            text(im,1470,yy,f"${float(r['revenue']):,.2f}",25,INK,True,anchor='rt')
            rect(im,(742,yy+43,1470,yy+61),'#EDF3F7',9)
            rect(im,(742,yy+43,742+max(18,728*float(r['revenue'])/maximum*a),yy+61),BLUE,9)
        line(im,[(742,602),(1470,602)])
        text(im,742,621,'Reconciled total',23,MUT)
        text(im,1470,612,f"${float(ETL['totalRevenue']):,.2f}",38,GREEN,True,anchor='rt')
    else:
        window(im,'What you can inspect','REPRODUCIBLE')
        for i,(label,desc) in enumerate([('01  Source + transformation','CSV fixture, Python rules and rejected rows'),('02  Database + reporting','PostgreSQL schema, upsert and reporting view'),('03  Evidence + handover','Rerun checks, reconciliation and run commands')]):
            yy=295+i*117
            pill(im,738,yy,str(i+1).zfill(2),BLUE,PALE,21)
            text(im,807,yy-2,label[4:],29,INK,True)
            text(im,807,yy+42,desc,22,MUT)
        pill(im,741,657,'All three database checks passed',GREEN,'#E5F2EB',20)

def chat(im,x,y,txts,user=False,w=650):
    h=45+37*len(txts)
    rect(im,(x,y,x+w,y+h),BLUE if user else '#EFF5F9',20)
    for i,s in enumerate(txts):text(im,x+24,y+17+i*37,s,26,'white' if user else INK)

def record(im,x,y,approved=False):
    for i,(k,v) in enumerate([('PROJECT','Demo Project'),('DATE','01 Oct 2026'),('TYPE','Expense'),('NET AMOUNT','10,000'),('NOTE','Demo materials')]):
        yy=y+i*58
        text(im,x,yy,k,16,MUT,True);text(im,x+210,yy-5,v,26,INK,True)
        if i<4:line(im,[(x,yy+42),(x+680,yy+42)],'#E4EDF3',1)

def ai_scene(im,scene,u):
    a=ease(u/1.8)
    if scene==0:
        card(im,(810,185,1455,644),'#F8FBFD')
        text(im,847,210,'WORKFLOW / RECORD ENTRY',18,MUT,True)
        chat(im,848,270,['Expense: 10,000 net.','Demo materials.'],True,560)
        card(im,(710,438,1240,679))
        text(im,744,467,'Prepared for review',26,INK,True)
        text(im,744,504,'10,000',76,INK,True)
        pill(im,744,610,'Confirm to save',GREEN,'#E6F3ED',20)
        ImageDraw.Draw(im).ellipse((1300,542,1465,707),fill=BLUE)
        line(im,[(1344,624),(1373,651),(1425,594)],'white',9)
    elif scene==1:
        window(im,'Demo Project','BOT REPLAY')
        chat(im,744,286,['Add an expense: 10,000 net.','Date: 01 Oct 2026.','Note: Demo materials.'],True,724)
        if u>1.5:chat(im,744,493,['Draft prepared.','Please review before saving.'],False,724)
        text(im,746,659,'Text input / extraction / structured fields',20,MUT)
    elif scene==2:
        window(im,'Review draft','NOT SAVED')
        record(im,742,294)
        pill(im,741,636,'Writes so far: 0',BLUE,PALE,22)
    elif scene==3:
        window(im,'Confirmation gate','ORIGINAL HANDLER')
        text(im,743,292,'Database writes',24,MUT)
        text(im,740,327,'1' if u>2.6 else '0',125,GREEN if u>2.6 else INK,True)
        text(im,873,397,'after approval' if u>2.6 else 'waiting for you',28,MUT)
        rect(im,(742,512,1475,600),GREEN if u>2.6 else BLUE,19)
        text(im,1108,528,'Saved to Demo Project' if u>2.6 else 'Confirm and save',32,'white',True,anchor='mt')
        if 1.9<u<3.1:
            xx=1340; yy=559
            ImageDraw.Draw(im).polygon([(xx,yy),(xx+14,yy+43),(xx+22,yy+27),(xx+42,yy+25)],fill='white',outline=INK)
        check(im,744,639,'No write before explicit confirmation',True)
    elif scene==4:
        window(im,'Saved row / read-back','SHEETS API MOCK')
        table(im,735,292,[['01 Oct 2026','Expense','10,000']],[270,250,245],['DATE','TYPE','NET AMOUNT'],highlight=0,row_h=75,size=27)
        rect(im,(737,457,1480,569),'#E7F3ED',16)
        text(im,763,477,'Confirmed row returned',29,GREEN,True)
        text(im,763,524,'The read-back contains the saved amount.',22,MUT)
        check(im,745,620,'Handler assertions passed',True)
    else:
        window(im,'What you can inspect','REPRODUCIBLE')
        for i,(label,desc) in enumerate([('Actual prototype handlers','Node.js + Telegraf control the workflow'),('Explicit approval boundary','Draft first. Confirm. Append the record.'),('Repeatable offline replay','No credentials needed; API responses mocked')]):
            yy=295+i*117
            pill(im,738,yy,str(i+1).zfill(2),BLUE,PALE,21)
            text(im,807,yy-2,label,29,INK,True)
            text(im,807,yy+42,desc,22,MUT)
        pill(im,741,657,'Three workflow assertions passed',GREEN,'#E5F2EB',20)

def frame(kind,t):
    scene=min(5,int(t/6));u=t-scene*6
    im=BASE.copy()
    text(im,70,43,'RB',30,INK,True)
    line(im,[(129,46),(129,78)],'#B9CDDB',2)
    text(im,150,48,'RUSLAN BATASHOV',20,INK,True)
    text(im,1520,49,'WORKFLOW STUDIES  /  '+('01' if kind=='etl' else '02'),18,MUT,True,anchor='rt')
    label,h1,h2,cap,stack=STORIES[kind][scene]
    pill(im,72,199,label,BLUE,PALE,18)
    text(im,68,275,h1,69,INK,True)
    text(im,68,357,h2,69,BLUE,True)
    # Manual line breaks preserve a relaxed left-column measure.
    captions={
      'etl':[['One source. A clear path','to trusted reporting.'],['Start with the file','your team actually receives.'],['Validate fields. Resolve','repeated order IDs.'],['The same batch leaves','the same eight orders.'],['One SQL view. Totals checked','against clean input.'],['Source, validation report,','SQL and run instructions.']],
      'ai':[['A small workflow.','A decision you control.'],['A free-text message becomes','a structured draft.'],['Inspect the extracted fields','before confirmation.'],['The original handler saves','only after confirmation.'],['Check the resulting row','in the same demo sheet.'],['A focused integration','with a clear review step.']]}
    for i,s in enumerate(captions[kind][scene]):text(im,74,481+39*i,s,27,MUT)
    if scene==0:
        for i,s in enumerate((['PYTHON','SQL','POSTGRESQL'] if kind=='etl' else ['NODE.JS','TELEGRAF','LLM API','SHEETS'])):
            pill(im,74+(i%3)*175,625+(i//3)*47,s,BLUE,'#EDF4F8',16)
    else:
        text(im,74,648,f'{scene:02d} / 05',22,MUT,True)
        text(im,74,687,'Run the example. Inspect the evidence.',19,MUT)
    (etl_scene if kind=='etl' else ai_scene)(im,scene,u)
    line(im,[(74,779),(1525,779)],'#CDDFEB')
    note='Synthetic data • Local PostgreSQL via PGlite • Verified run' if kind=='etl' else 'Prototype replay • Fictional data • External APIs mocked'
    text(im,74,802,note,20,MUT)
    text(im,1524,802,f'{min(36,int(t)):02d} / 36s',20,MUT,anchor='rt')
    for i in range(6):
        xx=74+i*245
        rect(im,(xx,859,xx+223,863),'#D7E5EF',2)
        p=1 if i<scene else min(1,u/6) if i==scene else 0
        if p:rect(im,(xx,859,xx+max(4,223*p),863),BLUE,2)
    # A restrained film dissolve at each chapter change.
    if scene and u<.32:
        prev=frame(kind,scene*6-.01)
        im=Image.blend(prev,im,ease(u/.32))
    return im

def render(kind):
    media=ROOT/'media';media.mkdir(exist_ok=True)
    for i in range(6): frame(kind,i*6+4.5).save(media/f'{kind}-scene-{i}.jpg',quality=94)
    frame(kind,4.5).save(media/f'{kind}-poster.png')
    out=media/f'{kind}-demo-en.mp4'
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    for n in range(36*24):
        p.stdin.write(frame(kind,n/24).tobytes())
        if n%144==0:print(kind,'chapter',n//144+1,flush=True)
    p.stdin.close();assert p.wait()==0
    # Full narrative GIF at six frames/second; MP4 retains smooth 24 fps.
    vf='fps=6,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-i',str(out),'-filter_complex',vf,'-loop','0',str(media/f'{kind}-preview.gif')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(kind,'complete',out.stat().st_size,flush=True)

if __name__=='__main__':
    if '--stills' in sys.argv:
        for k in STORIES:
            for i in range(6):frame(k,i*6+4.5).save(ROOT/f'media/{k}-scene-{i}.jpg',quality=94)
            frame(k,4.5).save(ROOT/f'media/{k}-poster.png')
    else:
        for k in ['etl','ai']:render(k)
