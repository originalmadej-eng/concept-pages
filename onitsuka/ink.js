/* ink.js — a small sumi-e painter.
   A brush stroke is built from single bristles: each carries its own load of ink, runs dry along the way, only catches the high points of the paper
   (so dry-brush streaks appear), pools where the brush lands and bleeds when wet. Washes (mountains, mist) are per-pixel functions with ragged,
   fibrous edges, a darker rim where the wash dried, and cloudy blooms. Everything paints into float layers (ink / two pigment channels / seal)
   that the page composites over washi paper. Original code, no external assets. */

export const rng=seed=>{let s=(seed>>>0)||1;return()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return(s>>>0)/4294967296;};};
const tick=()=>new Promise(r=>setTimeout(r,0));
const sstep0=(a,b,x)=>{const t=Math.min(1,Math.max(0,(x-a)/(b-a)));return t*t*(3-2*t);};

export function makeNoise(seed){
  const r=rng(seed),perm=new Uint8Array(512),g=new Float32Array(256);
  for(let i=0;i<256;i++){perm[i]=i;g[i]=r();}
  for(let i=255;i>0;i--){const j=(r()*(i+1))|0,t=perm[i];perm[i]=perm[j];perm[j]=t;}
  for(let i=0;i<256;i++)perm[256+i]=perm[i];
  const vn=(x,y)=>{const xi=Math.floor(x),yi=Math.floor(y),X=xi&255,Y=yi&255;let xf=x-xi,yf=y-yi;xf=xf*xf*(3-2*xf);yf=yf*yf*(3-2*yf);
    const a=g[perm[perm[X]+Y]],b=g[perm[perm[X+1]+Y]],c=g[perm[perm[X]+Y+1]],d=g[perm[perm[X+1]+Y+1]];
    return a+(b-a)*xf+(c-a)*yf+(a-b-c+d)*xf*yf;};
  const fbm=(x,y,o=4)=>{let s=0,a=.5,n=0;for(let i=0;i<o;i++){s+=a*vn(x,y);n+=a;x=x*2.03+17.1;y=y*2.03+9.7;a*=.5;}return s/n;};
  return {vn,fbm};
}

/* ---------- washi paper tile (kozo fibres, soft clouds, bark flecks), seamless so it can repeat ---------- */
export function paperTile(S=1024,seed=3){
  const R=rng(seed),c=document.createElement('canvas');c.width=c.height=S;const g=c.getContext('2d');
  g.fillStyle='#eee6d1';g.fillRect(0,0,S,S);
  const wrap=(x,y,ext,draw)=>{const xs=[0],ys=[0];if(x<ext)xs.push(S);if(x>S-ext)xs.push(-S);if(y<ext)ys.push(S);if(y>S-ext)ys.push(-S);
    for(const dx of xs)for(const dy of ys){g.save();g.translate(dx,dy);draw();g.restore();}};
  for(let i=0;i<46;i++){const x=R()*S,y=R()*S,r=70+R()*210,warm=R()<.55;
    wrap(x,y,r,()=>{const gr=g.createRadialGradient(x,y,0,x,y,r);gr.addColorStop(0,warm?'rgba(210,184,140,.10)':'rgba(255,253,244,.26)');gr.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=gr;g.fillRect(x-r,y-r,r*2,r*2);});}
  const fibre=(len,wMin,wMax,ca)=>{const x=R()*S,y=R()*S,a=R()*Math.PI,k=(R()-.5)*.9,lw=wMin+R()*(wMax-wMin);
    wrap(x,y,len,()=>{g.strokeStyle=ca;g.lineWidth=lw;g.lineCap='round';g.beginPath();g.moveTo(x,y);
      g.quadraticCurveTo(x+Math.cos(a)*len*.5-Math.sin(a)*len*k*.5,y+Math.sin(a)*len*.5+Math.cos(a)*len*k*.5,x+Math.cos(a)*len,y+Math.sin(a)*len);g.stroke();});};
  for(let i=0;i<2400;i++)fibre(8+R()*52,.5,1.35,R()<.62?`rgba(255,253,246,${(.45+R()*.45).toFixed(2)})`:`rgba(160,136,100,${(.10+R()*.17).toFixed(2)})`);
  for(let i=0;i<60;i++)fibre(90+R()*190,.5,1.0,R()<.7?`rgba(255,253,246,${(.28+R()*.3).toFixed(2)})`:`rgba(150,126,92,${(.07+R()*.09).toFixed(2)})`);
  for(let i=0;i<70;i++){const x=R()*S,y=R()*S,l=3+R()*8,a=R()*Math.PI,al=(.18+R()*.28).toFixed(2),lw=.8+R()*1.1;wrap(x,y,12,()=>{g.strokeStyle=`rgba(96,74,46,${al})`;g.lineWidth=lw;g.beginPath();g.moveTo(x,y);g.lineTo(x+Math.cos(a)*l,y+Math.sin(a)*l);g.stroke();});}
  const img=g.getImageData(0,0,S,S),d=img.data;for(let i=0;i<d.length;i+=4){const n=(R()-.5)*10;d[i]+=n;d[i+1]+=n;d[i+2]+=n*.9;}g.putImageData(img,0,0);
  return c;
}

/* ---------- the painter ---------- */
/* the glyph mask of a seal (RGBA pixels, dark = carved): drawn with whichever canvas the thread has */
export function sealMask(S,text){
  const c=typeof document!=='undefined'?document.createElement('canvas'):new OffscreenCanvas(S,S);c.width=c.height=S;const g=c.getContext('2d');
  g.fillStyle='#fff';g.fillRect(0,0,S,S);g.fillStyle='#000';g.font=`400 ${Math.round(S*.62)}px "Yuji Boku","Shippori Mincho",serif`;g.textAlign='center';g.textBaseline='middle';
  const ch=[...text];ch.forEach((t,i)=>g.fillText(t,S/2,S*(ch.length>1?(.27+.46*i):.5)+S*.03));
  return g.getImageData(0,0,S,S).data;
}

export function createPainter(W,H,seed=11,opts={}){
  const u=Math.min(H,W/1.5)/1000,N=makeNoise(seed),R=rng(seed*31+7);   // one unit ≈ a thousandth of the picture height (smaller on tall, narrow screens)
  const clamp=(x,a=0,b=1)=>x<a?a:x>b?b:x,sstep=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
  const tooth=new Float32Array(W*H);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){const v=.36*N.vn(x*.6,y*.6)+.32*N.vn(x*.07+y*.03,y*.85)+.32*N.vn(x*.85,y*.065+x*.03);tooth[y*W+x]=sstep(.2,.8,v);}
  const ar=Math.min(1,W/(H*1.5));   // 1 on landscape screens, smaller on tall narrow ones: keeps mountains and branches from turning into spikes
  const SB=new Float32Array(W*H),T1=new Float32Array(W*H),T2=new Float32Array(W*H),T3=new Float32Array(W*H);
  /* the paint clock: every stroke and wash notes WHEN it lays down each pixel (L.tm), in the order the scene is painted, so the page can replay the painting stroke by stroke */
  const TB=new Float32Array(W*H).fill(1e9);let clk=0;
  const mkLayer=()=>({ink:new Float32Array(W*H),ta:new Float32Array(W*H),tb:new Float32Array(W*H),sl:new Float32Array(W*H),tm:new Float32Array(W*H).fill(1e9)});

  /* low-resolution noise fields (clouds, streaks, mist, blooms) shared by every wash; mirrored lookups keep them seamless */
  const GS=4,GW=Math.ceil(W/GS)+3,GH=Math.ceil(H/GS)+3;
  const field=(sx,sy,oct,off)=>{const F=new Float32Array(GW*GH);for(let j=0;j<GH;j++)for(let i=0;i<GW;i++)F[j*GW+i]=N.fbm(i*GS/sx+off,j*GS/sy+off*.7,oct);return F;};
  const mir=(v,L)=>{v=((v%(2*L))+2*L)%(2*L);return v>L?2*L-v:v;};
  const samp=(F,x,y)=>{x=mir(x,W-GS*2)/GS;y=mir(y,H-GS*2)/GS;const i=x|0,j=y|0,fx=x-i,fy=y-j,k=j*GW+i;return F[k]*(1-fx)*(1-fy)+F[k+1]*fx*(1-fy)+F[k+GW]*(1-fx)*fy+F[k+GW+1]*fx*fy;};
  const F_cloud=field(95*u,34*u,3,0),F_streak=field(300*u,5*u,2,5),F_mist=field(520*u,46*u,3,11),F_bloom=field(46*u,46*u,3,23),F_big=field(900*u,650*u,3,31);

  function blur(buf,x0,y0,x1,y1,r,passes=2){
    r=Math.max(1,r|0);const d=2*r+1;
    for(let p=0;p<passes;p++){
      for(let y=y0;y<y1;y++){const row=y*W;let acc=0;for(let x=x0-r;x<=x0+r;x++)acc+=buf[row+(x<0?0:x>=W?W-1:x)];
        for(let x=x0;x<x1;x++){T2[row+x]=acc/d;const a=x+r+1,b=x-r;acc+=buf[row+(a>=W?W-1:a)]-buf[row+(b<0?0:b)];}}
      for(let y=y0;y<y1;y++){const row=y*W;for(let x=x0;x<x1;x++)buf[row+x]=T2[row+x];}
      for(let x=x0;x<x1;x++){let acc=0;for(let y=y0-r;y<=y0+r;y++)acc+=buf[(y<0?0:y>=H?H-1:y)*W+x];
        for(let y=y0;y<y1;y++){T2[y*W+x]=acc/d;const a=y+r+1,b=y-r;acc+=buf[(a>=H?H-1:a)*W+x]-buf[(b<0?0:b)*W+x];}}
      for(let y=y0;y<y1;y++){const row=y*W;for(let x=x0;x<x1;x++)buf[row+x]=T2[row+x];}
    }
  }
  function spline(pts,step){
    const out=[],n=pts.length,get=i=>pts[Math.max(0,Math.min(n-1,i))];
    for(let i=0;i<n-1;i++){const p0=get(i-1),p1=get(i),p2=get(i+1),p3=get(i+2),m=Math.max(2,Math.ceil(Math.hypot(p2[0]-p1[0],p2[1]-p1[1])/step));
      for(let k=0;k<m;k++){const t=k/m,t2=t*t,t3=t2*t;
        out.push([.5*(2*p1[0]+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3),
                  .5*(2*p1[1]+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)]);}}
    out.push(pts[n-1]);return out;
  }
  const prof=(t,t0,t1)=>{const a=t0>0?Math.pow(Math.min(t/t0,1),.72):1,b=t1>0?Math.pow(Math.min((1-t)/t1,1),.85):1;return Math.max(.05,a*b);};

  /* one brush stroke.  w: width in px · ink: density · dry: 0 wet … 1 very dry · wet: bleed into the paper · t0/t1: how much of the stroke
     is a tapering entry/exit · side: one flank of the brush holds less ink (bamboo) · chan: ink | ta | tb | sl */
  function stroke(L,pts,o={}){
    o={w:10,ink:1,dry:0,wet:0,t0:.1,t1:.3,lead:.5,wob:.05,chan:'ink',press:null,side:0,...o};
    const P=spline(pts,.7),n=P.length;if(n<2)return;
    const cum=new Float32Array(n);for(let i=1;i<n;i++)cum[i]=cum[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);
    const len=cum[n-1]||1,nb=Math.max(2,Math.min(280,Math.ceil(o.w/.65)+1)),dur=.35+len*(.03+.012*o.w),ts=clk;   // a stroke takes longer the longer and fatter it is
    const off=new Float32Array(nb),ld=new Float32Array(nb),dc=new Float32Array(nb),ph=new Float32Array(nb);
    for(let i=0;i<nb;i++){off[i]=(i+R()*.8)/nb-.5;ld[i]=.55+.45*R();dc[i]=o.dry*(.25+1.6*R())+o.side*Math.max(0,(off[i]+.5)*1.5-.2);ph[i]=R()*50;}
    let bx0=W,by0=H,bx1=0,by1=0;const wph=R()*50,chan=L[o.chan],useDry=o.dry>0||o.side>0;
    for(let j=0;j<n;j++){
      const t=cum[j]/len,a=P[j>0?j-1:0],b=P[j<n-1?j+1:n-1];let tx=b[0]-a[0],ty=b[1]-a[1];const tl=Math.hypot(tx,ty)||1;tx/=tl;ty/=tl;
      const wf=o.press?o.press(t):prof(t,o.t0,o.t1),w=o.w*wf*(1+o.wob*(N.vn(cum[j]*.018+wph,3.3)-.5)*2);
      const lead=1+o.lead*Math.exp(-cum[j]/(9*u)),pr=.55+.45*Math.min(1,wf*1.5);
      for(let i=0;i<nb;i++){
        const jit=(N.vn(cum[j]*.03+ph[i],i*1.7)-.5)*Math.min(1.6,w*.05),ofs=off[i]*w+jit;
        const x=P[j][0]-ty*ofs,y=P[j][1]+tx*ofs;if(x<1||y<1||x>=W-2||y>=H-2)continue;
        const ix=x|0,iy=y|0,k=iy*W+ix;let f=1;
        if(useDry){const dr=N.vn(cum[j]*.011+ph[i],i*2.9)-.5;f=clamp((ld[i]+dr*.55-dc[i]*t-tooth[k]*o.dry*.6-.03)*4);if(f<=0)continue;}
        const v=Math.min(1.25,f*(.78+.22*ld[i])*lead*pr)*1.7,fx=x-ix,fy=y-iy;
        const a00=v*(1-fx)*(1-fy),a10=v*fx*(1-fy),a01=v*(1-fx)*fy,a11=v*fx*fy;
        if(a00>SB[k])SB[k]=a00;if(a10>SB[k+1])SB[k+1]=a10;if(a01>SB[k+W])SB[k+W]=a01;if(a11>SB[k+W+1])SB[k+W+1]=a11;
        const tt=ts+t*dur;if(tt<TB[k])TB[k]=tt;if(tt<TB[k+1])TB[k+1]=tt;if(tt<TB[k+W])TB[k+W]=tt;if(tt<TB[k+W+1])TB[k+W+1]=tt;
        if(ix<bx0)bx0=ix;if(iy<by0)by0=iy;if(ix>bx1)bx1=ix;if(iy>by1)by1=iy;
      }
    }
    clk=ts+dur*(.12+.88*clamp(o.w/14,0,1));   // thin flicks overlap in time (a pine fan is flicked in one go), broad strokes follow one another
    if(bx1<bx0)return;
    const r=Math.max(1,Math.round(o.wet*1.4*u)),pad=Math.ceil(3+(o.wet>0?r*8+4:0));
    bx0=Math.max(0,bx0-pad);by0=Math.max(0,by0-pad);bx1=Math.min(W,bx1+pad+2);by1=Math.min(H,by1+pad+2);
    if(o.wet>0){
      for(let y=by0;y<by1;y++){const row=y*W;for(let x=bx0;x<bx1;x++){const v=SB[row+x];T1[row+x]=v;T3[row+x]=v;}}
      blur(T1,bx0,by0,bx1,by1,r,2);blur(T3,bx0,by0,bx1,by1,r*3,2);                // soft body, and a faint halo bleeding into the fibres
      for(let y=by0;y<by1;y++){const row=y*W;for(let x=bx0;x<bx1;x++){const k=row+x;SB[k]=SB[k]*(1-.5*o.wet)+T1[k]*.5*o.wet+T3[k]*.3*o.wet;}}
    }
    for(let y=by0;y<by1;y++){const row=y*W;for(let x=bx0;x<bx1;x++){const k=row+x,v=SB[k];if(v>0){chan[k]+=Math.min(1.2,v)*o.ink;SB[k]=0;const tk=TB[k]<1e8?TB[k]:ts+dur*.5;if(tk<L.tm[k])L.tm[k]=tk;}TB[k]=1e9;}}
  }

  /* a wash over a region: fn(x,y) returns the density to add */
  function wash(L,chan,x0,y0,x1,y1,fn,dur=60){
    x0=Math.max(0,x0|0);y0=Math.max(0,y0|0);x1=Math.min(W,x1|0);y1=Math.min(H,y1|0);const c=L[chan],ts=clk,sw=x1-x0||1,sh=y1-y0||1;
    for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const v=fn(x,y);if(v>0){const k=y*W+x;c[k]+=v;const tt=ts+dur*clamp((x-x0)/sw*.85+(y-y0)/sh*.15+(N.vn(x*.006,y*.006)-.5)*.3);if(tt<L.tm[k])L.tm[k]=tt;}}   // a wash is laid across from the left
    clk=ts+dur*.7;
  }

  /* mountains: a ridgeline from layered noise (broad swells + crags + a few pinnacles), a wash that is densest at the crest and dissolves into mist */
  function ridge(L,o){
    o={base:.6,amp:.08,fx:2.2,sx:0,ink:.4,fade:140*u,soft:7*u,rim:.22,floor:0,peaks:[],mist:.5,crag:.35,bloom:.18,valley:0,ox:0,oy:0,tint:null,tamt:0,...o};
    const yr=new Float32Array(W);
    for(let x=0;x<W;x++){
      const xn=x/W;let h=(N.fbm(xn*o.fx+o.sx,3.7+o.sx*.3,5)-.5)*2;
      const rg=1-Math.abs(N.fbm(xn*o.fx*2.6+o.sx+9,1.3,4)*2-1);
      h=h*o.amp+Math.pow(rg,2.2)*o.amp*o.crag*1.4;
      if(o.valley)h*=1-o.valley*Math.exp(-Math.pow((xn-.5)/.2,2));
      for(const p of o.peaks){const dx=(xn-p[0])/(p[2]*(xn<p[0]?.78:1.3)),sx2=(xn-(p[0]+p[2]*1.9))/(p[2]*.8);h+=p[1]*Math.exp(-dx*dx)*(1+.3*Math.abs(dx))+p[1]*.42*Math.exp(-sx2*sx2);}
      h+=(N.fbm(xn*38+o.sx,7.7,3)-.5)*o.amp*.35;
      yr[x]=(o.base-h*ar)*H;
    }
    const reach=o.fade*3.2+20*u,ts=clk,dur=o.dur||78;
    for(let x=0;x<W;x++){
      const y0=Math.max(0,(yr[x]-18*u)|0),y1=Math.min(H,(yr[x]+reach)|0);
      for(let y=y0;y<y1;y++){
        const k=y*W+x;let d=y-yr[x];
        if(d<14*u&&d>-14*u)d+=(N.vn(x*.33,y*.33)-.5)*3.4*u+(N.vn(x*.07,y*.07)-.5)*5*u;           // ragged, fibrous edge
        const dens=sstep(-o.soft*.6,o.soft,d);if(dens<=0)continue;
        const dd=d>0?d:0,fall=o.floor+(1-o.floor)*Math.exp(-dd/o.fade);
        const m=o.mist>0?1-sstep(.5,.86,samp(F_mist,x+o.ox,y+o.oy))*o.mist:1;
        const cloud=.74+.52*samp(F_cloud,x+o.ox,y+o.oy),streak=.9+.2*samp(F_streak,x+o.ox*.5,y+o.oy);
        const rim=o.rim*Math.exp(-(dd*dd)/(36*u*u))*sstep(-o.soft,0,d);
        const bloom=o.bloom*sstep(.58,.8,samp(F_bloom,x+o.ox,y+o.oy*.6))*Math.exp(-dd/(70*u));
        const v=o.ink*(dens*fall*m*cloud*streak+rim+bloom);L.ink[k]+=v;
        if(o.tint)L[o.tint][k]+=o.tamt*dens*fall*m;
        if(v>.002){const tt=ts+dur*clamp(x/W*.82+clamp(dd/reach)*.12+(N.vn(x*.004,y*.004)-.5)*.2);if(tt<L.tm[k])L.tm[k]=tt;}   // the range is brushed in from the left, crest first
      }
    }
    clk=ts+dur*.8;
    return yr;
  }
  /* broken contour strokes riding a crest: dry, tapering, never one continuous line */
  function contour(L,yr,o){
    o={n:9,ink:.55,w:4*u,dry:.5,dy:3*u,min:.12,max:.34,x0:0,x1:1,...o};
    for(let i=0;i<o.n;i++){
      const xs=W*(o.x0+(o.x1-o.x0)*R()),len=W*(o.min+(o.max-o.min)*R()),pts=[];
      for(let x=xs;x<=Math.min(W-2,xs+len);x+=Math.max(14,len/9))pts.push([x,yr[x|0]+o.dy+(R()-.5)*3*u]);
      if(pts.length>2)stroke(L,pts,{w:o.w*(.7+.6*R()),ink:o.ink*(.7+.5*R()),dry:o.dry,wet:.12,t0:.25,t1:.45,wob:.15,lead:.2});
    }
  }
  /* small clumps of trees on a ridge: a few short upward dabs of different heights, never evenly spaced */
  function trees(L,yr,o){
    o={n:8,ink:.8,size:20*u,x0:.05,x1:.95,...o};
    for(let c=0;c<o.n;c++){
      const cx=W*(o.x0+(o.x1-o.x0)*R()),k=2+((R()*4)|0);
      for(let i=0;i<k;i++){const x=cx+(R()-.5)*o.size*2.6,y=yr[Math.max(0,Math.min(W-1,x|0))]+(R()*3-1)*u,h=o.size*(.45+R()*.9),lean=(R()-.5)*.35;
        stroke(L,[[x,y+2*u],[x+lean*h*.5,y-h*.5],[x+lean*h,y-h]],{w:o.size*(.1+.1*R()),ink:o.ink*(.55+.6*R()),wet:.3,t0:.1,t1:.7,wob:0,lead:.1});}
    }
  }
  /* pigment glow (sky / mist tint) */
  function glow(L,chan,cx,cy,rx,ry,amt,ox=0,oy=0){
    wash(L,chan,cx-rx*2.4,cy-ry*2.4,cx+rx*2.4,cy+ry*2.4,(x,y)=>{const a=(x-cx)/rx,b=(y-cy)/ry,e=Math.exp(-(a*a+b*b));return e<.01?0:amt*e*(.7+.5*samp(F_big,x+ox,y+oy));},46);
  }
  /* a pine needle fan: straight-ish strokes radiating from a point in a half-circle, dense and dark at the heart, paler at the tips */
  function needles(L,cx,cy,ang,size,n,o={}){
    for(let i=0;i<n;i++){const a=ang+(R()-.5)*(o.spread||3.0),l=size*(.45+.55*R()),c=(R()-.5)*.2*l,
        ex=cx+Math.cos(a)*l,ey=cy+Math.sin(a)*l+l*.05,mx=cx+Math.cos(a)*l*.5-Math.sin(a)*c,my=cy+Math.sin(a)*l*.5+Math.cos(a)*c;
      stroke(L,[[cx,cy],[mx,my],[ex,ey]],{w:(o.w||1.25)*u*(.8+.6*R()),ink:(o.ink||1)*(.42+.62*R()),t0:.02,t1:.6,dry:.05,wob:0,lead:0});}
  }
  const offPath=(P,dx,dy=dx)=>P.map(p=>[p[0]+dx,p[1]+dy]);
  /* a bark-textured branch: a wet body, a dry-brush second pass, knots, then twigs ending in needle fans */
  function pineBranch(L,P,o={}){
    o={w:30*u,twigs:6,fans:1,ink:1,dir:1,scale:1,...o};
    stroke(L,P,{w:o.w,ink:.62*o.ink,wet:.7,t0:.04,t1:.6,dry:.18,wob:.22});
    stroke(L,offPath(P,o.w*.1,-o.w*.12),{w:o.w*.66,ink:.8*o.ink,dry:.62,t0:.04,t1:.55,side:.2,wob:.18});
    stroke(L,offPath(P,-o.w*.2,o.w*.14),{w:o.w*.3,ink:.85*o.ink,dry:.85,t0:.05,t1:.5,wob:.2});
    stroke(L,offPath(P,o.w*.05,o.w*.2),{w:o.w*.2,ink:.7*o.ink,dry:.9,t0:.05,t1:.4,wob:.3});
    const sp=spline(P,6);
    for(let i=0;i<5;i++){const q=sp[Math.min(sp.length-1,((.12+.75*R())*sp.length)|0)];stroke(L,[[q[0]-5*u,q[1]-3*u],[q[0]+5*u,q[1]+5*u]],{w:o.w*(.22+.14*R()),ink:.9*o.ink,wet:.5,t0:.3,t1:.3,wob:.1});}
    for(let i=0;i<o.twigs;i++){
      const t=.14+.78*(i+R()*.6)/o.twigs,q=sp[Math.min(sp.length-1,(t*sp.length)|0)],dir=o.dir;
      const a=Math.PI/2+dir*(.25+R()*.75),l=(100+R()*130)*u*o.scale,dv=[Math.cos(a),Math.sin(a)],pv=[-dv[1],dv[0]],bow=(R()<.8?1:-1)*(.07+R()*.1)*l;
      const pt=t=>[q[0]+dv[0]*l*t+pv[0]*bow*t*t,q[1]+dv[1]*l*t*.82+pv[1]*bow*t*t],p1=pt(.35),p2=pt(.68),p3=pt(1);
      stroke(L,[q,p1,p2,p3],{w:o.w*(.17+.1*R()),ink:.85*o.ink,dry:.4,t0:.04,t1:.55,wob:.12});
      needles(L,p3[0],p3[1],Math.PI/2+dir*.45,(56+R()*52)*u*o.scale,Math.round(24+R()*22),{ink:o.ink});
      if(R()<.55)needles(L,p2[0],p2[1],Math.PI/2+dir*.8,(42+R()*34)*u*o.scale,Math.round(12+R()*12),{ink:o.ink*.8});
    }
    const e=P[P.length-1];for(let i=0;i<o.fans;i++)needles(L,e[0]-10*u*i,e[1]+4*u*i,Math.PI/2+o.dir*.35,(76+R()*40)*u*o.scale,Math.round(32+R()*20),{ink:o.ink});
  }
  /* a pointed leaf painted in one stroke: thin entry, a belly, a sharp tip */
  function leaf(L,x,y,ang,len,w,ink,o={}){
    const bend=(R()-.5)*.28*len;
    stroke(L,[[x,y],[x+Math.cos(ang)*len*.5-Math.sin(ang)*bend,y+Math.sin(ang)*len*.5+Math.cos(ang)*bend],[x+Math.cos(ang)*len,y+Math.sin(ang)*len+len*.07]],
      {w,ink,wet:.18,t0:.3,t1:.65,wob:0,lead:.25,press:t=>Math.max(.05,Math.pow(Math.sin(Math.PI*Math.min(1,t*1.04)),.75)),...o});
  }
  /* bamboo: a culm built of stalk-length strokes with a node bar between them; one flank runs lighter. returns the nodes */
  function bamboo(L,x,y0,y1,o={}){
    o={w:20*u,ink:.8,lean:.025,...o};let y=y0,cx=x;const nodes=[];
    while(y>y1){const seg=(115+R()*75)*u,ny=Math.max(y1,y-seg),nx=cx+(R()-.5)*7*u+o.lean*(y-ny);
      stroke(L,[[cx,y-2*u],[(cx+nx)/2+(R()-.5)*3*u,(y+ny)/2],[nx,ny+4*u]],{w:o.w*(.92+.1*R()),ink:o.ink,wet:.3,side:.45,t0:.03,t1:.03,wob:.03,dry:.12,lead:.2});
      stroke(L,[[nx-o.w*.6,ny+2*u],[nx+o.w*.6,ny-.5*u]],{w:3.4*u,ink:1,wet:.2,t0:.2,t1:.2,wob:0,lead:0});
      nodes.push([nx,ny]);cx=nx;y=ny;}
    return nodes;
  }
  /* a sprig of bamboo leaves hanging from a node */
  function leaves(L,x,y,o={}){
    o={n:4,len:105*u,w:10*u,ink:.9,dir:0,...o};
    for(let i=0;i<o.n;i++){const a=Math.PI/2+o.dir+((i-(o.n-1)/2)*.62)+(R()-.5)*.3;leaf(L,x,y,a,o.len*(.7+.5*R()),o.w*(.8+.5*R()),o.ink*(.6+.5*R()));}
  }
  /* maple leaf: five splayed dabs of red pigment with a few thin veins */
  function mapleLeaf(L,x,y,size,rot,o={}){
    for(let i=0;i<5;i++){const a=rot+(i-2)*.66,l=size*(i===2?1:.82);
      stroke(L,[[x,y],[x+Math.cos(a)*l*.5,y+Math.sin(a)*l*.5],[x+Math.cos(a)*l,y+Math.sin(a)*l]],{chan:'tb',ink:o.amt||.85,w:size*.36,wet:.3,t0:.06,t1:.5,wob:.05,lead:.2});}
    for(let i=0;i<3;i++){const a=rot+(i-1)*.66;stroke(L,[[x,y],[x+Math.cos(a)*size*.8,y+Math.sin(a)*size*.8]],{w:1.1*u,ink:.35,t0:.1,t1:.5,wob:0,lead:0});}
    stroke(L,[[x,y],[x-Math.cos(rot)*size*.45,y-Math.sin(rot)*size*.45]],{w:1.6*u,ink:.6,t0:.1,t1:.3,wob:0,lead:0});
  }
  /* a persimmon: a round wash of orange pigment that pools darker at the rim, a four-lobed calyx, a short stem */
  function persimmon(L,x,y,r){
    wash(L,'tb',x-r*1.4,y-r*1.4,x+r*1.4,y+r*1.4,(px,py)=>{const dx=px-x,dy=(py-y)*1.06,d=Math.hypot(dx,dy),rr=r*(1+.07*(N.vn(px*.05,py*.05)-.5)*2);
      const body=1-sstep(rr*.93,rr,d);if(body<=0)return 0;return body*(.55+.3*sstep(.45,1,d/rr)+.25*N.vn(px*.1,py*.1));});
    for(let i=0;i<4;i++){const a=i*Math.PI/2+.4;stroke(L,[[x,y-r*.82],[x+Math.cos(a)*r*.42,y-r*.82+Math.sin(a)*r*.2]],{w:r*.22,ink:.9,wet:.3,t0:.1,t1:.5,wob:0,lead:0});}
  }
  /* a pine tree in a few strokes: leaning trunk, two arms, fans at their tips */
  function pineTree(L,x,yb,h,o={}){
    o={ink:.8,w:h*.06,lean:(R()-.5)*.18,...o};
    const top=[x+o.lean*h,yb-h],mid=[x+o.lean*h*.45+(R()-.5)*h*.06,yb-h*.5];
    stroke(L,[[x,yb],mid,top],{w:o.w,ink:o.ink*.75,wet:.5,dry:.3,t0:.05,t1:.5,wob:.2,side:.15});
    for(let i=0;i<3;i++){const t=.45+.2*i+R()*.1,bx=mid[0]+(top[0]-mid[0])*(t-.5)*2,by=yb-h*t,sd=i%2?1:-1,l=h*(.3+.25*R());
      stroke(L,[[bx,by],[bx+sd*l*.5,by-l*.12],[bx+sd*l,by-l*.04]],{w:o.w*.4,ink:o.ink*.7,dry:.4,t0:.05,t1:.5,wob:.15});
      needles(L,bx+sd*l,by-l*.04,-Math.PI/2+sd*.2,h*.2,Math.round(18+R()*14),{ink:o.ink,spread:2.6,w:1.1});}
    needles(L,top[0],top[1],-Math.PI/2,h*.22,Math.round(22+R()*14),{ink:o.ink,spread:2.4,w:1.1});
  }
  /* a wild goose: two bent strokes */
  function goose(L,x,y,s){stroke(L,[[x-s,y+s*.12],[x-s*.45,y-s*.3],[x,y]],{w:s*.11,ink:.95,t0:.1,t1:.8,wob:0,lead:0});stroke(L,[[x,y],[x+s*.45,y-s*.3],[x+s,y+s*.12]],{w:s*.11,ink:.95,t0:.1,t1:.8,wob:0,lead:0});}
  /* flicked drops of ink */
  function splatter(L,cx,cy,rx,ry,n,o={}){for(let i=0;i<n;i++){const a=R()*6.283,d=Math.pow(R(),.7),x=cx+Math.cos(a)*rx*d,y=cy+Math.sin(a)*ry*d,r=(o.size||3)*u*(.3+R()*R()*2);
      stroke(L,[[x,y],[x+(R()-.5)*r,y+(R()-.5)*r]],{w:r,ink:(o.ink||.8)*(.5+R()*.6),wet:.4,t0:.5,t1:.5,wob:0,lead:0});}}
  /* the vermilion seal: white characters carved out of a red square with eroded edges. It is queued while the scene is painted and stamped at the end,
     so a worker can wait for the page to send the glyph mask (the page owns the brush font) */
  const sealJobs=[];
  function seal(L,cx,cy,size,text){sealJobs.push([L,cx,cy,Math.round(size),text]);}
  async function applySeals(){
    const st=clk+6;   // the seal is pressed last
    for(const [L,cx,cy,S,text] of sealJobs.splice(0)){
      const d=opts.sealMask?await opts.sealMask(S,text):sealMask(S,text);
      for(let y=0;y<S;y++)for(let x=0;x<S;x++){const px=Math.round(cx-S/2+x),py=Math.round(cy-S/2+y);if(px<0||py<0||px>=W||py>=H)continue;
        const carve=d[(y*S+x)*4]<128,ed=Math.min(x,y,S-1-x,S-1-y)/S,er=N.vn(px*.4,py*.4)*.045+N.vn(px*.11,py*.11)*.03;
        if(ed<er)continue;const v=(carve?.12:1)*(.78+.22*N.vn(px*.2,py*.2));L.sl[py*W+px]=Math.max(L.sl[py*W+px],v*(1-.2*tooth[py*W+px]));if(st<L.tm[py*W+px])L.tm[py*W+px]=st;}
    }
  }
  /* pack a layer to RGBA8: R = how much ink (as absorbed fraction), G/B = pigment washes, A = seal */
  function pack(L){const out=new Uint8ClampedArray(W*H*4);for(let k=0,j=0;k<W*H;k++,j+=4){out[j]=255*(1-Math.exp(-L.ink[k]*1.35));out[j+1]=255*clamp(L.ta[k]);out[j+2]=255*clamp(L.tb[k]);out[j+3]=255*clamp(L.sl[k]);}return out;}

  /* the paint times of the three layers as one RGBA8 map (R/G/B = layer 0/1/2, 0..254 over the whole painting, 255 = never touched).
     Untouched texels next to painted ones take their neighbour's time, so the soft edge of a stroke appears with its core */
  function packTimes(Ls){
    const total=clk+14,out=new Uint8Array(W*H*4);
    Ls.forEach((L,c)=>{const tm=L.tm;
      for(let p=0;p<2;p++){const o=tm.slice();for(let y=1;y<H-1;y++){const r=y*W;for(let x=1;x<W-1;x++){const k=r+x;if(tm[k]<1e8)continue;
        const m=Math.min(tm[k-1],tm[k+1],tm[k-W],tm[k+W],tm[k-W-1],tm[k-W+1],tm[k+W-1],tm[k+W+1]);if(m<1e8)o[k]=m;}}tm.set(o);}
      for(let k=0,j=c;k<W*H;k++,j+=4)out[j]=tm[k]>=1e8?255:Math.min(254,Math.round(tm[k]/total*254));});
    for(let j=3;j<out.length;j+=4)out[j]=255;return out;
  }
  const fit=(pts,y0)=>pts.map(([x,y])=>[W*x,H*(y0+(y-y0)*ar)]);
  const api={fit,ar,W,H,u,N,R,tooth,mkLayer,stroke,wash,blur,ridge,contour,trees,glow,needles,pineBranch,leaf,bamboo,leaves,mapleLeaf,persimmon,pineTree,goose,splatter,seal,pack,clamp,sstep,spline,offPath,samp,F_big,tick};
  api.scene=async idx=>{const f=SCENES[idx%SCENES.length];clk=0;const Ls=[api.mkLayer(),api.mkLayer(),api.mkLayer()];await f(api,Ls[0],Ls[1],Ls[2]);await applySeals();const out=Ls.map(pack),times=packTimes(Ls);return {W,H,layers:out,times};};
  return api;
}

/* ---------- the six paintings (one per colourway) ---------- */
const SCENES=[
  /* 山吹 — dawn: pale gold glow behind far peaks, layered ranges dissolving into mist, a pine bough from the upper left */
  async (P,L0,L1,L2)=>{
    const {W,H,u}=P;
    P.glow(L0,'ta',W*.62,H*.56,W*.5,H*.28,.9);
    P.ridge(L0,{base:.575,amp:.05,fx:1.7,sx:1.2,ink:.17,fade:80*u,peaks:[[.3,.09,.035],[.74,.11,.04]],crag:.9,mist:.7,ox:30,oy:10});await P.tick();
    P.ridge(L0,{base:.645,amp:.06,fx:2.1,sx:4.7,ink:.27,fade:100*u,peaks:[[.16,.08,.04],[.52,.06,.035],[.88,.1,.04]],crag:.85,mist:.65,ox:200,oy:70});await P.tick();
    const yr=P.ridge(L1,{base:.735,amp:.075,fx:2.3,sx:8.3,ink:.4,fade:125*u,rim:.26,peaks:[[.09,.15,.07],[.93,.18,.06]],valley:.55,crag:.8,mist:.5,ox:420,oy:140});await P.tick();
    P.trees(L1,yr,{n:6,size:16*u,ink:.55});
    P.pineBranch(L2,P.fit([[-.04,.105],[.05,.145],[.14,.163],[.22,.215],[.29,.25],[.345,.305]].map(([x,y])=>[x,y]),.105),{w:30*u,twigs:6,dir:-1,fans:2});await P.tick();
    P.seal(L2,W*.94,H*.79,56*u,'六六');
  },
  /* 茜 — dusk: a rose glow, wild geese, a maple bough from the upper right */
  async (P,L0,L1,L2)=>{
    const {W,H,u}=P;
    P.glow(L0,'ta',W*.36,H*.5,W*.5,H*.3,.95);
    P.ridge(L0,{base:.6,amp:.05,fx:1.5,sx:21,ink:.17,fade:85*u,peaks:[[.62,.1,.04],[.2,.07,.04]],crag:.9,mist:.7,ox:60,oy:20});await P.tick();
    P.ridge(L0,{base:.67,amp:.06,fx:2.0,sx:25,ink:.28,fade:100*u,peaks:[[.4,.08,.04],[.86,.11,.04]],crag:.85,mist:.62,ox:260,oy:90});await P.tick();
    const yr=P.ridge(L1,{base:.75,amp:.075,fx:2.2,sx:31,ink:.4,fade:120*u,rim:.26,peaks:[[.07,.17,.07],[.95,.15,.06]],valley:.55,crag:.8,mist:.5,ox:520,oy:180});await P.tick();
    P.trees(L1,yr,{n:6,size:16*u,ink:.55});
    for(let i=0;i<6;i++)P.goose(L0,W*(.6+.036*i+.01*Math.sin(i*2)),H*(.2+.014*i+.02*Math.cos(i*3)),(9+5*Math.abs(Math.sin(i+1)))*u);
    const br=P.fit([[-.04,.105],[.05,.145],[.13,.16],[.20,.215],[.265,.245],[.31,.305]],.105);
    P.stroke(L2,br,{w:24*u,ink:.7,wet:.6,t0:.04,t1:.6,dry:.2,wob:.2});P.stroke(L2,P.offPath(br,4*u,-5*u),{w:13*u,ink:.8,dry:.75,t0:.05,t1:.5});
    const sp=P.spline(br,10);
    for(let i=0;i<7;i++){const q=sp[Math.min(sp.length-1,((.1+.8*i/7)*sp.length)|0)],a=Math.PI/2-.2-P.R()*.7,l=(70+P.R()*90)*u,e=[q[0]+Math.cos(a)*l,q[1]+Math.sin(a)*l*.9];
      P.stroke(L2,[q,[(q[0]+e[0])/2-6*u,(q[1]+e[1])/2],e],{w:6*u,ink:.8,dry:.4,t0:.05,t1:.5});
      for(let k=0;k<3;k++)P.mapleLeaf(L2,e[0]+(P.R()-.5)*50*u,e[1]+(P.R()-.3)*40*u,(34+P.R()*26)*u,Math.PI/2+(P.R()-.5)*1.6);}
    for(let i=0;i<5;i++)P.mapleLeaf(L2,W*(.3+.5*P.R()),H*(.22+.3*P.R()),(22+P.R()*16)*u,P.R()*6.28,{amt:.6});await P.tick();
    P.seal(L2,W*.94,H*.79,56*u,'六六');
  },
  /* 紺 — indigo dusk: a deep wash across the top, bamboo on both sides */
  async (P,L0,L1,L2)=>{
    const {W,H,u}=P;
    P.glow(L0,'ta',W*.5,-H*.08,W*.95,H*.5,1.0);
    P.ridge(L0,{base:.63,amp:.05,fx:1.6,sx:41,ink:.2,fade:90*u,peaks:[[.55,.11,.04],[.15,.08,.04]],crag:.9,mist:.7,ox:100,oy:30});await P.tick();
    const yr=P.ridge(L1,{base:.74,amp:.07,fx:2.1,sx:47,ink:.4,fade:120*u,rim:.26,peaks:[[.82,.15,.06]],valley:.55,crag:.8,mist:.55,ox:600,oy:210});await P.tick();
    [[.045,1.12,-.12,24],[.105,1.15,.03,19],[.915,1.12,.02,20]].forEach(([x,y0,y1,w],i)=>{
      const nodes=P.bamboo(L2,W*x,H*y0,H*y1,{w:w*u,ink:.78,lean:i===2?-.03:.03});
      nodes.forEach((n,j)=>{if(n[1]<H*.62&&j%2===0&&n[1]>H*.0)P.leaves(L2,n[0],n[1],{n:3+((P.R()*3)|0),dir:(i===2?-.5:.5)+(P.R()-.5)*.5,len:(80+P.R()*40)*u,w:9*u,ink:.95});});
    });await P.tick();
    P.seal(L2,W*.94,H*.79,56*u,'六六');
  },
  /* 常磐 — evergreen: cedars standing in mist, three depths, a pine bough from the upper right */
  async (P,L0,L1,L2)=>{
    const {W,H,u,R}=P;
    P.glow(L0,'ta',W*.5,H*.58,W*.62,H*.3,.85);
    const trunk=(L,x,yb,h,w,ink)=>{const top=[x+(R()-.5)*h*.03,yb-h];
      P.stroke(L,[[x,yb],[(x+top[0])/2+(R()-.5)*w*.8,yb-h*.5],top],{w,ink,wet:.35,dry:.28,side:.12,t0:.02,t1:.55,wob:.1,lead:.2});
      const k=3+((R()*4)|0);for(let i=0;i<k;i++){const t=.5+.45*R(),bx=x+(top[0]-x)*t,by=yb-h*t,sd=R()<.5?-1:1,l=w*(2+R()*3.5);
        P.stroke(L,[[bx,by],[bx+sd*l*.6,by-l*.25],[bx+sd*l,by-l*.05+l*.2]],{w:w*.32,ink:ink*.8,dry:.4,t0:.05,t1:.6,wob:.1,lead:0});P.needles(L,bx+sd*l,by-l*.05+l*.2,Math.PI/2+sd*.6,l*.9,Math.round(8+R()*8),{ink:ink*.9,w:1.05,spread:2.2});}};
    for(let i=0;i<15;i++)trunk(L0,W*(.02+.96*(i+R()*.7)/15),H*(.7+.03*R()),H*(.32+.28*R()),(5+3*R())*u,.16+.1*R());await P.tick();
    P.ridge(L1,{base:.78,amp:.03,fx:1.8,sx:57,ink:.26,fade:100*u,crag:.4,mist:.6,ox:300,oy:90,valley:.3});
    [.09,.2,.33,.67,.8,.91].forEach((x,i)=>trunk(L1,W*(x+(R()-.5)*.02),H*(.86+.02*R()),H*(.62+.26*R()),(10+6*R())*u,.38+.14*R()));await P.tick();
    [[.025,19],[.92,22]].forEach(([x,w])=>trunk(L2,W*x,H*1.04,H*1.1,w*u,.75));
    P.pineBranch(L2,P.fit([[-.04,.105],[.05,.14],[.13,.152],[.2,.195],[.255,.23]],.105),{w:21*u,twigs:4,dir:-1,fans:2,scale:.9});
    P.seal(L2,W*.94,H*.79,56*u,'六六');
  },
  /* 橙 — a persimmon bough from the upper left, warm light low in the sky */
  async (P,L0,L1,L2)=>{
    const {W,H,u,R}=P;
    P.glow(L0,'ta',W*.5,H*.62,W*.55,H*.26,.9);
    P.ridge(L0,{base:.62,amp:.05,fx:1.7,sx:61,ink:.17,fade:85*u,peaks:[[.7,.09,.04],[.25,.07,.04]],crag:.9,mist:.7,ox:150,oy:40});await P.tick();
    const yr=P.ridge(L1,{base:.75,amp:.07,fx:2.2,sx:67,ink:.4,fade:120*u,rim:.26,peaks:[[.1,.16,.07],[.92,.17,.06]],valley:.55,crag:.8,mist:.5,ox:700,oy:240});P.trees(L1,yr,{n:6,size:16*u,ink:.55});await P.tick();
    const br=P.fit([[-.04,.105],[.05,.145],[.13,.155],[.2,.21],[.265,.23],[.31,.295]],.105);
    P.stroke(L2,br,{w:22*u,ink:.7,wet:.6,t0:.04,t1:.6,dry:.2,wob:.2});P.stroke(L2,P.offPath(br,4*u,-5*u),{w:12*u,ink:.8,dry:.75,t0:.05,t1:.5});
    const sp=P.spline(br,10);
    [[.28,70,1],[.5,95,-.4],[.72,85,.8],[.9,70,-.2]].forEach(([t,l,s])=>{const q=sp[Math.min(sp.length-1,(t*sp.length)|0)],a=Math.PI/2+s*.35,e=[q[0]+Math.cos(a)*l*u,q[1]+Math.sin(a)*l*u];
      P.stroke(L2,[q,[(q[0]+e[0])/2+s*6*u,(q[1]+e[1])/2],e],{w:5*u,ink:.8,dry:.3,t0:.05,t1:.4});P.persimmon(L2,e[0],e[1]+34*u,(30+R()*8)*u);
      P.leaf(L2,e[0],e[1]-6*u,Math.PI/2+s*1.3,(95+R()*30)*u,26*u,.8);P.leaf(L2,e[0],e[1]-6*u,Math.PI/2-s*1.0,(80+R()*30)*u,22*u,.55);});
    await P.tick();P.seal(L2,W*.94,H*.79,56*u,'六六');
  },
  /* 鼠 — haboku: broken ink, rain-grey ranges, flicked drops */
  async (P,L0,L1,L2)=>{
    const {W,H,u,R}=P;
    P.ridge(L0,{base:.58,amp:.06,fx:1.5,sx:71,ink:.2,fade:90*u,peaks:[[.68,.12,.045],[.22,.09,.04]],crag:1,mist:.75,ox:90,oy:30});await P.tick();
    P.ridge(L0,{base:.66,amp:.07,fx:2.0,sx:77,ink:.34,fade:110*u,peaks:[[.4,.1,.04],[.9,.12,.04]],crag:.95,mist:.7,ox:330,oy:110});await P.tick();
    const yr=P.ridge(L1,{base:.76,amp:.08,fx:2.1,sx:83,ink:.62,fade:130*u,rim:.4,bloom:.3,peaks:[[.08,.18,.07],[.94,.2,.06]],valley:.55,crag:.9,mist:.4,ox:800,oy:270});
    P.trees(L1,yr,{n:7,size:18*u,ink:.7});await P.tick();
    for(let i=0;i<150;i++){const x=W*(1.05*R()-.02),y=H*(.02+.55*R()),l=(70+R()*110)*u;P.stroke(L2,[[x,y],[x-l*.16,y+l]],{w:(.8+.5*R())*u,ink:.1+.14*R(),dry:.4,t0:.3,t1:.6,wob:0,lead:0});}
    P.splatter(L2,W*.18,H*.7,W*.16,H*.14,40,{ink:.9});P.splatter(L2,W*.84,H*.66,W*.14,H*.14,36,{ink:.9});await P.tick();
    P.seal(L2,W*.94,H*.79,56*u,'六六');
  }
];

/* ---------- a character painted with a big brush: a brush-hand typeface, then dry-brush streaks that follow each stroke, run-out edges and a soft bleed ---------- */
function boxBlurArr(buf,tmp,W,H,r,passes=2){
  const d=2*r+1;
  for(let p=0;p<passes;p++){
    for(let y=0;y<H;y++){const row=y*W;let acc=0;for(let x=-r;x<=r;x++)acc+=buf[row+(x<0?0:x>=W?W-1:x)];
      for(let x=0;x<W;x++){tmp[row+x]=acc/d;const a=x+r+1,b=x-r;acc+=buf[row+(a>=W?W-1:a)]-buf[row+(b<0?0:b)];}}
    for(let x=0;x<W;x++){let acc=0;for(let y=-r;y<=r;y++)acc+=tmp[(y<0?0:y>=H?H-1:y)*W+x];
      for(let y=0;y<H;y++){buf[y*W+x]=acc/d;const a=y+r+1,b=y-r;acc+=tmp[(a>=H?H-1:a)*W+x]-tmp[(b<0?0:b)*W+x];}}
  }
}
/* turn an alpha mask (a typeface) into brush-written ink: dry streaks that follow each stroke, run-out edges, a soft bleed and tonal variation.
   fade: 1 = even ink; <1 lets the ink run out toward the end of the mask (top → bottom) */
function brushify(a,CS,CH,size,seed,fade=1){
  const N=makeNoise(seed*3+1),n=CS*CH,b=a.slice(),h=a.slice(),tmp=new Float32Array(n);
  const sc=Math.min(.3,.075*820/size),sc2=Math.min(.12,.011*820/size);
  const blurW=(buf,r)=>{const d=2*r+1;for(let p=0;p<2;p++){
    for(let y=0;y<CH;y++){const row=y*CS;let acc=0;for(let x=-r;x<=r;x++)acc+=buf[row+(x<0?0:x>=CS?CS-1:x)];for(let x=0;x<CS;x++){tmp[row+x]=acc/d;const q=x+r+1,w=x-r;acc+=buf[row+(q>=CS?CS-1:q)]-buf[row+(w<0?0:w)];}}
    for(let x=0;x<CS;x++){let acc=0;for(let y=-r;y<=r;y++)acc+=tmp[(y<0?0:y>=CH?CH-1:y)*CS+x];for(let y=0;y<CH;y++){buf[y*CS+x]=acc/d;const q=y+r+1,w=y-r;acc+=tmp[(q>=CH?CH-1:q)*CS+x]-tmp[(w<0?0:w)*CS+x];}}}};
  blurW(b,Math.max(1,Math.round(size*.011)));blurW(h,Math.max(2,Math.round(size*.03)));
  const out=new Uint8ClampedArray(n*4);
  for(let y=1;y<CH-1;y++)for(let x=1;x<CS-1;x++){const i=y*CS+x;
    const core=sstep0(.5,.96,b[i]),gx=b[i+1]-b[i-1],gy=b[i+CS]-b[i-CS],wv=Math.abs(gx)/(Math.abs(gx)+Math.abs(gy)+1e-4);
    const streak=wv*N.vn(x*sc,y*sc*.15)+(1-wv)*N.vn(x*sc*.15,y*sc),dry=(1-core)*.8+.12+(1-fade)*(y/CH)*.9;
    let v=a[i]*(1-dry*sstep0(.42,.72,streak)*.95);
    v=Math.max(v,h[i]*.22*(.5+.5*N.fbm(x*sc2,y*sc2,2)));v*=(.82+.36*N.fbm(x*sc2*.35,y*sc2*.35,3))*(1-(1-fade)*(y/CH)*.55);
    const j=i*4;out[j]=30;out[j+1]=21;out[j+2]=14;out[j+3]=Math.min(255,v*255);}
  return out;
}
const maskOf=(g,CS,CH)=>{const src=g.getImageData(0,0,CS,CH).data,a=new Float32Array(CS*CH);for(let i=0;i<a.length;i++)a[i]=src[i*4+3]/255;return a;};
const finish=(g,c,out,CS,CH)=>{g.clearRect(0,0,CS,CH);g.putImageData(new ImageData(out,CS,CH),0,0);return c;};
export function brushGlyph(ch,size=820,seed=5){
  const pad=Math.round(size*.1),CS=size+pad*2,c=document.createElement('canvas');c.width=c.height=CS;const g=c.getContext('2d');
  g.fillStyle='#000';g.font=`400 ${size}px "Yuji Boku","Shippori Mincho",serif`;g.textAlign='center';g.textBaseline='middle';g.fillText(ch,CS/2,CS/2+size*.04);
  return finish(g,c,brushify(maskOf(g,CS,CS),CS,CS,size,seed,1),CS,CS);
}
/* a column of calligraphy, written top to bottom, each character a little off its neighbour, the ink running out toward the end */
export function brushText(str,size=84,seed=5,o={}){
  const R=rng(seed*7+1),chars=[...str],pad=Math.round(size*.45),step=size*(o.step||1.12),CS=Math.round(size+pad*2),CH=Math.round(chars.length*step+pad*2),c=document.createElement('canvas');c.width=CS;c.height=CH;const g=c.getContext('2d');
  g.fillStyle='#000';g.font=`400 ${size}px "Yuji Boku","Shippori Mincho",serif`;g.textAlign='center';g.textBaseline='middle';
  chars.forEach((ch,i)=>{g.save();g.translate(CS/2+(R()-.5)*size*.07,pad+(i+.5)*step+(R()-.5)*size*.04);g.rotate((R()-.5)*.07);g.scale(1,1);
    if(/[。、]/.test(ch)){g.translate(size*.32,-size*.3);g.font=`400 ${size*.8}px "Yuji Boku","Shippori Mincho",serif`;}
    g.fillText(ch,0,0);g.restore();});
  return finish(g,c,brushify(maskOf(g,CS,CH),CS,CH,size,seed,o.fade??.7),CS,CH);
}
