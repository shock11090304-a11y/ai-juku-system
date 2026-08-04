# -*- coding: utf-8 -*-
"""review3 の確定指摘9件を v2_out.json に反映:
 - 描画バグ2件(\\neq が eq に化けた)を復元
 - ベン図の答え露出を空図に
 - 図形6件を svgfig(数学座標→正しいSVG)で描き直し
"""
import json, math
import svgfig as S
from svgfig import Canvas, NAVY, RED

def venn_empty():
    return ('<svg viewBox="0 0 190 130" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="6" y="6" width="178" height="118" fill="#eef2f7" stroke="#1f3a5f" stroke-width="1.5"/>'
            '<circle cx="75" cy="66" r="42" fill="none" stroke="#1f3a5f" stroke-width="1.5"/>'
            '<circle cx="115" cy="66" r="42" fill="none" stroke="#1f3a5f" stroke-width="1.5"/>'
            '<text x="36" y="38" font-size="12">A</text><text x="148" y="38" font-size="12">B</text>'
            '<text x="170" y="20" font-size="12">U</text></svg>')

def gaisetsu():  # 図形と計量#11: b=CA=3,c=AB=8,A=60°,a=BC=7,外接円 O=(4,-0.577)R=4.041
    A=(0,0); B=(8,0); C=(1.5, 3*math.sqrt(3)/2)
    O=(4, -math.sqrt(3)/3); R=7*math.sqrt(3)/3
    c=Canvas((-0.7,8.7),(-R+O[1]-0.2, C[1]+0.5), size=(180,175))
    c.circle(O[0],O[1],R, stroke=NAVY, w=1.3)
    c.poly([A,B,C])
    c.seg(O[0],O[1],0,0, stroke=NAVY, w=0.9, dash="3 2")  # 半径R
    c.dot(O[0],O[1],NAVY)
    c.label(*A,"A",dx=-13,dy=4); c.label(*B,"B",dx=4,dy=4); c.label(*C,"C",dx=-2,dy=-5)
    c.label(*O,"O",dx=5,dy=12)                  # O は AB のすぐ下 → ラベルはさらに下へ
    c.label(0.75,C[1]/2,"3",dx=-12,dy=0)        # b=CA
    c.label(6.2,0,"8",dx=-2,dy=13)              # c=AB(Oを避け右寄り下)
    c.label(4.75,C[1]/2,"7",dx=6,dy=0)          # a=BC
    c.label(0,0,"60°",dx=13,dy=-7,size=9)
    c.label(1.6,O[1]/2,"R",dx=-4,dy=-3,size=10,color=RED)  # 半径 O→A の上側
    return c.svg()

def menelaus():  # 図形の性質#9: AD:DB=3:1, BE:EC=1:2, F=直線DE∩(CAの延長), CF:FA=2:3
    A=(1.5,2); B=(0,0); Cc=(3,0)
    D=(0.25*A[0]+0.75*B[0], 0.25*A[1]+0.75*B[1])   # AD:DB=3:1
    E=(2/3*B[0]+1/3*Cc[0], 2/3*B[1]+1/3*Cc[1])     # BE:EC=1:2
    F=(6,-4)   # CAの延長・DE上(検算済み: CF:FA=2:3)
    c=Canvas((-0.5,6.5),(-4.5,2.5), size=(195,180))
    c.poly([A,B,Cc])
    c.seg(Cc[0],Cc[1],F[0],F[1], stroke=NAVY, w=1.0, dash="3 3")  # CAの延長 C→F
    c.seg(D[0],D[1],F[0],F[1], stroke=RED, w=1.5)                 # 直線DE(→F), Eを通る
    for p,nm,dx,dy in [(A,"A",-2,-4),(B,"B",-12,4),(Cc,"C",1,13),(D,"D",-11,2),(E,"E",-3,13),(F,"F",4,4)]:
        c.dot(*p, RED if nm in ("D","E","F") else NAVY); c.label(*p,nm,dx=dx,dy=dy)
    return c.svg()

def houbeki():  # 図形の性質#6: 円外P, 割線PAB(PA=4,AB=5), 割線PCD(PC=3), CDを求める
    import math as m
    r=2.5; P=(-5.0,0.0)
    def sec(theta):
        d=(m.cos(theta), m.sin(theta))
        aa=d[0]**2+d[1]**2; bb=2*(P[0]*d[0]+P[1]*d[1]); cc=P[0]**2+P[1]**2-r*r
        disc=m.sqrt(bb*bb-4*aa*cc); t1=(-bb-disc)/(2*aa); t2=(-bb+disc)/(2*aa)
        near=(P[0]+d[0]*t1, P[1]+d[1]*t1); far=(P[0]+d[0]*t2, P[1]+d[1]*t2)
        return near, far
    A,Bp=sec(math.radians(12)); C,D=sec(math.radians(-18))
    c=Canvas((-5.8,2.9),(-2.9,2.5), size=(205,150))
    c.circle(0,0,r)
    c.seg(P[0],P[1],Bp[0],Bp[1], stroke=RED, w=1.3)
    c.seg(P[0],P[1],D[0],D[1], stroke=RED, w=1.3)
    for p,nm,dx,dy in [(P,"P",-11,3),(A,"A",-3,-5),(Bp,"B",4,-2),(C,"C",-10,7),(D,"D",4,7)]:
        c.dot(*p,NAVY); c.label(*p,nm,dx=dx,dy=dy)
    mid=lambda u,v:((u[0]+v[0])/2,(u[1]+v[1])/2)
    c.label(*mid(P,A),"4",dy=-3); c.label(*mid(A,Bp),"5",dy=-3); c.label(*mid(P,C),"3",dy=9)
    return c.svg()

def gaibun():  # 図形と方程式#2: A(-1,2),B(5,4)を3:1外分→P(8,5)
    c=Canvas((-2.6,9.6),(-1.4,6.2), size=(205,150))
    c.axes()
    c.seg(-1,2,8,5, stroke=RED, w=1.3)
    c.dot(-1,2,NAVY); c.label(-1,2,"A",dx=-14,dy=1)
    c.dot(5,4,NAVY); c.label(5,4,"B",dx=-4,dy=-6)
    c.dot(8,5,RED); c.label(8,5,"P",dx=4,dy=4)
    return c.svg()

def apollonius():  # 図形と方程式#12: A(0,0),B(6,0),PA:PB=2:1→円(x-8)^2+y^2=16
    c=Canvas((-1.6,13),(-5,5), size=(205,150))
    c.axes(olabel=False)
    c.circle(8,0,4, stroke=RED, w=1.5)
    c.dot(0,0,NAVY); c.label(0,0,"A",dx=-13,dy=13)
    c.dot(6,0,NAVY); c.label(6,0,"B",dx=-2,dy=13)
    return c.svg()

def bibun():  # 微分法#3: y=x^2-3x 上の点(2,-2)の接線 y=x-4
    c=Canvas((-1.2,4.2),(-3.2,3.0), size=(195,155))
    c.axes()
    xs=[-0.8+0.28*i for i in range(18)]
    pts=[(x, x*x-3*x) for x in xs if -3.2<=x*x-3*x<=3.0]
    pl=" ".join(f"{c.X(x)},{c.Y(y)}" for x,y in pts)
    c.parts.append(f'<polyline points="{pl}" fill="none" stroke="{NAVY}" stroke-width="1.6"/>')
    c.line_abc(1,-1,-4, stroke=RED, w=1.3)   # 接線 x-y-4=0
    c.dot(2,-2,RED); c.label(2,-2,"(2,-2)",dx=5,dy=9,size=9)
    return c.svg()

FIGS = {
    "外接円の半径": ("外接円", gaisetsu(), lambda st: "b$=3" in st or "b=3" in st.replace(" ","")),
    "menelaus": ("メネラウス", menelaus(), lambda st: "メネラウス" in st),
    "houbeki": ("方べき", houbeki(), lambda st: "割線" in st),
    "gaibun": ("外分", gaibun(), lambda st: "外分" in st and "A(-1" in st.replace(" ","")),
    "apollonius": ("アポロ", apollonius(), lambda st: "PA:PB" in st.replace(" ","") and "軌跡" in st),
    "bibun": ("微分接線", bibun(), lambda st: "y=x^{2}-3x" in st.replace(" ","")),
}

def main():
    data=json.load(open("v2_out.json",encoding="utf-8"))
    log=[]
    for u in data:
        for q in u["problems"]:
            st=q.get("stem","")
            # 描画バグ復元
            if "k eq0" in q.get("explanation",""):
                q["explanation"]=q["explanation"].replace("k eq0","k \\neq 0"); log.append("fix:keq0")
            if "a eq1" in st:
                q["stem"]=st=st.replace("a eq1","a \\neq 1"); log.append("fix:aeq1")
            # ベン図 空図
            if "バスケットボール" in st and q.get("figure"):
                q["figure"]=venn_empty(); log.append("venn-empty")
            # 図形再描画
            for key,(nm,svg,pred) in FIGS.items():
                if q.get("figure") and pred(st):
                    q["figure"]=svg; log.append("fig:"+nm)
    json.dump(data, open("v2_out.json","w"), ensure_ascii=False)
    print("applied:", sorted(log))

if __name__=="__main__":
    main()
