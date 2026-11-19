# -*- coding: utf-8 -*-
"""
盘前全球市场简报 · 每日数据更新脚本
抓取：美股/欧股/亚太股指、大宗商品、美债收益率与汇率、A股指数与市场宽度、
      涨停·炸板·跌停池、行业板块与资金、K线火花线、华尔街见闻快讯(含美股频道)、财联社(可选)
输出：site/data.js  (window.MARKET_DATA = {...})
用法：python update_market_data.py
"""
import json, re, time, datetime, urllib.request, urllib.parse, gzip, os

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根（脚本在 tools/ 下）
OUT  = os.path.join(HERE, "site", "data.js")

def http(url, headers=None, timeout=9, tries=1):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip, deflate"}
    if headers: h.update(headers)
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                ct = r.headers.get("Content-Type","") or ""
                enc = "gbk" if ("gbk" in ct or "gb2312" in ct) else "utf-8"
                return raw.decode(enc, "ignore")
        except Exception as e:
            last = e; time.sleep(0.6)
    raise last or RuntimeError("http fail: " + url)

def em_jsonp(path, timeout=8):
    hosts = ["push2.eastmoney.com", "push2delay.eastmoney.com", "push2his.eastmoney.com"]
    cb = "__cb" + str(int(time.time()*1000)%100000)
    for host in hosts:
        for raw in (True, False):
            try:
                u = f"https://{host}{path}"
                if raw: u += ("&" if "?" in u else "?") + f"cb={cb}"
                txt = http(u, timeout=timeout)
                if raw and cb in txt:
                    m = re.search(re.escape(cb)+r"\((.*)\)", txt, re.S)
                    if m: txt = m.group(1)
                return json.loads(txt)
            except Exception:
                continue
    raise RuntimeError("em_jsonp fail: " + path)

# ============ 全球行情（一个 ulist 拿全部） ============
QUOTE_SETS = {
    "us":   [("100.DJI","道琼斯指数"),("100.IXIC","纳斯达克指数"),("100.SPX","标普500指数"),("100.INX","标普500指数"),("100.SOX","费城半导体")],
    "eu":   [("100.DAX","德国DAX"),("100.STOXX50E","欧洲斯托克50"),("100.SX5E","欧洲斯托克50"),("100.FTSE","英国富时100"),("100.CAC40","法国CAC40")],
    "asia": [("100.KS11","韩国KOSPI"),("100.N225","日经225"),("100.HSI","恒生指数"),("100.HSTECH","恒生科技")],
    "cmd":  [("101.GC00Y","COMEX黄金"),("113.CL00Y","WTI原油"),("113.CO00Y","布伦特原油"),("102.CL00Y","WTI原油"),("102.CO00Y","布伦特原油")],
    "bfx":  [("171.US2Y","美债2年"),("171.US10Y","美债10年"),("171.US30Y","美债30年"),("100.UDI","美元指数"),("133.USDCNH","离岸人民币")],
}
A_IDX = [("1.000001","上证指数"),("0.399001","深证成指"),("0.399006","创业板指")]
BS_IDX = [("1.000016","上证50"),("1.000300","沪深300"),("1.000905","中证500"),("1.000852","中证1000"),("0.899050","北证50")]

def fetch_global():
    secids = ",".join(c for grp in QUOTE_SETS.values() for c,_ in grp) + "," + ",".join(c for c,_ in A_IDX+BS_IDX)
    mp = {}
    try:
        r = em_jsonp(f"/api/qt/ulist.np/get?fltt=2&secids={secids}&fields=f2,f3,f4,f6,f12,f14", timeout=10)
        for x in (r.get("data",{}).get("diff") or []): mp[x["f12"]] = x
    except Exception: pass
    out = {}
    for grp, items in QUOTE_SETS.items():
        cand = []
        for code, name in items:
            short = code.split(".")[-1]
            x = mp.get(short) or mp.get(code)
            it = {"name":name, "code":code}
            if x and x.get("f2") not in (None,"-"):
                it.update({"price":float(x["f2"]), "pct":float(x["f3"]) if x.get("f3") not in (None,"-") else 0,
                           "chg": float(x["f4"]) if x.get("f4") not in (None,"-") else None,
                           "amount": float(x.get("f6") or 0)})
            cand.append(it)
        # 同名去重：优先保留有价格的
        seen, lst = {}, []
        for it in cand:
            n = it["name"]
            if n not in seen or (it.get("price") and not seen[n].get("price")):
                seen[n] = it
        for n,it in seen.items(): lst.append(it)
        # 保持原始顺序
        order = {name:i for i,(code,name) in enumerate(items)}
        lst.sort(key=lambda it: order.get(it["name"], 99))
        out[grp] = lst
    # A股指数
    a_idx = []
    for code, name in A_IDX:
        x = mp.get(code.split(".")[-1])
        it = {"name":name,"code":code}
        if x and x.get("f2") not in (None,"-"):
            it.update({"price":float(x["f2"]),"pct":float(x["f3"]) if x.get("f3") not in (None,"-") else 0,
                       "amount":float(x.get("f6") or 0)})
        a_idx.append(it)
    out["aIndices"] = a_idx
    out["bs"] = []
    for code, name in BS_IDX:
        x = mp.get(code.split(".")[-1])
        it = {"name":name,"code":code}
        if x and x.get("f2") not in (None,"-"):
            it.update({"price":float(x["f2"]),"pct":float(x["f3"]) if x.get("f3") not in (None,"-") else 0})
        out["bs"].append(it)
    # 新浪兜底：美股三大 + 商品
    if not out["us"][0].get("price") or not any(c.get("price") for c in out["cmd"]):
        try: sina_fill(out)
        except Exception: pass
    # 腾讯兜底：A股指数 + 大小盘
    if not any(it.get("price") for it in out["aIndices"]):
        try: tc_fill_a(out)
        except Exception: pass
    return out

def tc_fill_a(out):
    codes = "sh000001,sz399001,sz399006,sh000016,sh000300,sh000905,sh000852"
    txt = http(f"https://qt.gtimg.cn/q={codes}", timeout=10)
    mp = {"sh000001":("上证指数","1.000001"),"sz399001":("深证成指","0.399001"),
          "sz399006":("创业板指","0.399006"),"sh000016":("上证50","1.000016"),
          "sh000300":("沪深300","1.000300"),"sh000905":("中证500","1.000905"),
          "sh000852":("中证1000","1.000852")}
    for key,(name,code) in mp.items():
        m = re.search(r'v_%s="(.*?)"' % key, txt)
        if not m: continue
        f = m.group(1).split("~")
        try:
            price=float(f[3]); prev=float(f[4])
            seg=next((x for x in f if x and x.count("/")==2),None)
            amt=float(seg.split("/")[2]) if seg else 0
            tgt = next((it for it in out["aIndices"] if it["code"]==code), None) or \
                  next((it for it in out["bs"] if it["code"]==code), None)
            if tgt and not tgt.get("price"):
                tgt.update({"price":price,"pct":round((price-prev)/prev*100,2) if prev else 0,"amount":amt})
        except Exception: pass

def sina_fill(out):
    names = "int_dji,int_nasdaq,int_sp500,hf_GC,hf_CL,hf_OIL,hf_XAU"
    txt = http(f"https://hq.sinajs.cn/list={names}", headers={"Referer":"https://finance.sina.com.cn"}, timeout=9)
    def grab(k):
        m = re.search(r'hq_str_%s="(.*?)"' % k, txt)
        return m.group(1) if m else ""
    for key, cat, idxs in [("int_dji",0,0),("int_nasdaq",0,1),("int_sp500",0,2)]:
        f = grab(key).split(",")
        if len(f) >= 4 and f[1]:
            try:
                it = out["us"][idxs]
                if not it.get("price"):
                    it.update({"price":float(f[1]),"pct":float(f[3])})
            except Exception: pass
    for key, label, targets in [("hf_GC","COMEX黄金",["COMEX黄金"]),("hf_CL","WTI原油",["WTI原油"]),
                                 ("hf_OIL","布伦特原油",["布伦特原油"]),("hf_XAU","现货黄金",["现货黄金"])]:
        f = grab(key).split(",")
        if len(f) > 8 and f[8]:
            try:
                price = float(f[8]); prev = float(f[5]) if f[5] else 0
                pct = round((price-prev)/prev*100,2) if prev else 0
                for grp in ("cmd",):
                    it = next((c for c in out[grp] if c["name"]==label and not c.get("price")), None)
                    if it: it.update({"price":price,"pct":pct})
            except Exception: pass

# ============ A股宽度 / 涨停池 / 板块 ============
FS_ALL = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
def fetch_breadth():
    try:
        r = em_jsonp(f"/api/qt/clist/get?pn=1&pz=6000&po=0&np=1&fltt=2&fid=f12&fs={urllib.parse.quote(FS_ALL)}&fields=f3,f6", timeout=12)
        up=down=flat=0; turnover=0
        for x in (r.get("data",{}).get("diff") or []):
            a = x.get("f6")
            if a: turnover += float(a)
            p = x.get("f3")
            if p is None or p=="-": continue
            p = float(p)
            if p>0: up+=1
            elif p<0: down+=1
            else: flat+=1
        return {"up":up,"down":down,"flat":flat,"turnover":round(turnover,0)}
    except Exception: return {}

UT = "ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt"
def fetch_pools():
    today = datetime.date.today()
    zt_pool, zb_pool, dt_pool, qdate = [], [], [], None
    for i in range(0, 6):
        dd = (today - datetime.timedelta(days=i)).strftime("%Y%m%d")
        try:
            r = em_jsonp(f"https://push2ex.eastmoney.com/getTopicZTPool?{UT}&Pageindex=0&pagesize=500&sort=lbc:desc&date={dd}", timeout=9)
            pool = r.get("data",{}).get("pool") or []
            if pool: zt_pool, qdate = pool, r["data"].get("qdate") or dd; break
        except Exception: continue
    if qdate:
        for ep, dst in [("getTopicZBPool","zb"),("getTopicDTPool","dt")]:
            try:
                r = em_jsonp(f"https://push2ex.eastmoney.com/{ep}?{UT}&Pageindex=0&pagesize=500&sort=fbt:asc&date={qdate}", timeout=9)
                pool = r.get("data",{}).get("pool") or []
                if dst=="zb": zb_pool = pool
                else: dt_pool = pool
            except Exception: continue
    max_ladder = max([int(x.get("lbc") or 1) for x in zt_pool], default=0)
    ladders = []
    for l in range(max_ladder, 1, -1):
        st = [{"name":x.get("n"),"code":x.get("c"),"hy":x.get("hybk")} for x in zt_pool if int(x.get("lbc") or 1)==l][:8]
        if st: ladders.append({"lbc":l,"stocks":st})
        if len(ladders)>=6: break
    zt, zb, dtc = len(zt_pool), len(zb_pool), len(dt_pool)
    zr = zb/(zt+zb) if zt+zb else 0
    return {"zt":zt,"zb":zb,"ztDown":dtc,"maxLadder":max_ladder,"ladders":ladders,"zhabanRate":round(zr,3)}, qdate

def fetch_boards():
    def mk(fid, po):
        r = em_jsonp(f"/api/qt/clist/get?pn=1&pz=6&po={po}&np=1&fltt=2&invt=2&fid={fid}&fs={urllib.parse.quote('m:90+t:2')}&fields=f3,f12,f14,f62", timeout=9)
        return [{"name":x.get("f14"),"pct":x.get("f3"),"inflow":x.get("f62")} for x in (r.get("data",{}).get("diff") or [])]
    out = {}
    for k,args in [("topUp",("f3",1)),("topDown",("f3",0)),("topInflow",("f62",1))]:
        try: out[k]=mk(*args)
        except Exception: out[k]=[]
    return out

def fetch_spark():
    out = {}
    for code,_ in [("100.DJI","x"),("100.IXIC","x"),("100.SPX","x"),("100.SOX","x")] + A_IDX + [("100.HSTECH","x"),("100.KS11","x")]:
        try:
            r = em_jsonp(f"/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&fields1=f1,f2,f3&fields2=f51,f53&end=20500101&lmt=22", timeout=9)
            ks = r.get("data",{}).get("klines") or []
            out[code] = [float(k.split(",")[1]) for k in ks if "," in k]
        except Exception: pass
    return out

# ============ 资讯 ============
def fetch_wscn(channel="global-channel", limit=18):
    try:
        d = json.loads(http(f"https://api-one-wscn.awtmt.com/apiv1/content/lives?channel={channel}&limit={limit}", timeout=9))
        out = []
        for it in (d.get("data",{}).get("items") or []):
            txt = (it.get("content_text") or "").strip()
            if not txt: continue
            t = it.get("display_time")
            ts = datetime.datetime.fromtimestamp(t).strftime("%H:%M") if t else ""
            ch = it.get("channels") or []
            tag = "美股" if "us-stock-channel" in ch else "全球"
            out.append({"time":ts,"text":txt[:200],"tag":tag,"uri":it.get("uri") or ""})
        return out
    except Exception: return []

def fetch_jin10(limit=12):
    """金十数据快讯（接口常变动/需token，失败则跳过）"""
    for u in ["https://flash-api.jin10.com/free_flash?max_time=0&channel=-820",
              "https://flash-api.jin10.com/get_flash_list?channel=-820&vip=1&t=0&limit=%d" % limit]:
        try:
            d = json.loads(http(u, headers={"Origin":"https://www.jin10.com","Referer":"https://www.jin10.com/"}, timeout=8))
            arr = d if isinstance(d, list) else (d.get("data") or [])
            out = []
            for it in arr[:limit]:
                txt = it.get("data",{}).get("content") if isinstance(it.get("data"),dict) else it.get("content")
                txt = re.sub(r"<[^>]+>","", txt or "").strip()
                if not txt: continue
                t = it.get("time") or it.get("created_at")
                ts = ""
                if t:
                    try: ts = str(t)[11:16]
                    except Exception: pass
                out.append({"time":ts,"text":txt[:200],"tag":"金十","uri":""})
            if out: return out
        except Exception: continue
    return []

def fetch_cls(limit=12):
    for u in ["https://www.cls.cn/nodeapi/updateTelegraphList?app=CailianpressWeb&category=0&os=web&sv=8.4.6&rn=%d"%limit]:
        try:
            r = http(u, headers={"Referer":"https://www.cls.cn/telegraph"}, timeout=8)
            if not r or r.lstrip().startswith("<"): continue
            d = json.loads(r)
            roll = (d.get("data") or {}).get("roll_data") or []
            out = []
            for it in roll[:limit]:
                txt = (it.get("title") or it.get("content") or "").strip()
                if not txt: continue
                t = it.get("ctime") or it.get("created_at")
                ts = datetime.datetime.fromtimestamp(int(t)).strftime("%H:%M") if t else ""
                out.append({"time":ts,"text":re.sub(r"<[^>]+>","",txt)[:200],"tag":"财联社","uri":it.get("uri") or ""})
            if out: return out
        except Exception: continue
    return []

# ============ 温度 ============
def calc_temp(b):
    t = 50
    tot = (b.get("up",0)+b.get("down",0)) or 1
    t += (b.get("up",0)-b.get("down",0))/tot*22
    t += min(b.get("zt",0),120)/120*14
    t += min(b.get("maxLadder",0),8)/8*8
    t -= b.get("zhabanRate",0)*12
    if b.get("turnover"): t += max(-8, min(8, (b["turnover"]/1.6e12-1)*8))
    return max(2, min(98, round(t)))

def read_events():
    try:
        with open(os.path.join(HERE, "site", "events.json"), encoding="utf-8") as f:
            return json.load(f).get("events", [])
    except Exception:
        return []

def main():
    print("[1/6] 全球行情…"); g = fetch_global()
    print("[2/6] A股宽度…"); bd = fetch_breadth()
    print("[3/6] 涨停池…"); pools, qdate = fetch_pools(); bd.update(pools)
    print("[4/6] 板块+火花线…"); bo = fetch_boards(); sp = fetch_spark()
    print("[5/6] 资讯…")
    news = fetch_cls(12) + fetch_jin10(12) + fetch_wscn("global-channel", 18) + fetch_wscn("us-stock-channel", 10)
    seen=set(); news2=[]
    for n in news:
        if n["text"] in seen: continue
        seen.add(n["text"]); news2.append(n)
    news = news2[:30]
    temp = calc_temp(bd)
    trade_date = str(qdate or datetime.date.today().strftime("%Y%m%d"))
    trade_date = re.sub(r"(\d{4})(\d{2})(\d{2})", r"\1-\2-\3", trade_date)
    data = {
        "tradeDate": trade_date,
        "us": g["us"], "eu": g["eu"], "asia": g["asia"], "cmd": g["cmd"], "bfx": g["bfx"],
        "aIndices": g["aIndices"], "bs": g["bs"],
        "breadth": bd, "boards": bo, "spark": sp, "news": news, "temperature": temp,
        "events": read_events(),
    }
    # 实时接入的源 + 标注整合来源（与页面页脚一致）
    live_src = ["华尔街见闻"]
    for s in ["财联社","金十数据"]:
        if any(n["tag"]==s.replace("数据","") for n in news): live_src.append(s)
    payload = {"updatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "sources": ["新华社","财联社","国际金融报","华尔街见闻","金十数据","Adler金融日报","同花顺"],
               "liveSources": ["东方财富","新浪财经","腾讯财经"] + live_src,
               "data": data}
    with open(OUT,"w",encoding="utf-8") as f:
        f.write("/* 盘前简报 · 自动生成 · "+payload["updatedAt"]+" */\nwindow.MARKET_DATA = "+json.dumps(payload, ensure_ascii=False)+";\n")
    print("OK ->", OUT)
    print("温度:",temp,"涨停:",bd.get("zt"),"美股道指:",g["us"][0].get("price"),"资讯:",len(news))

if __name__ == "__main__":
    main()
