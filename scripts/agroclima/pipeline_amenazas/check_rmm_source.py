import urllib.request,concurrent.futures
urls=['https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt','https://reg.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt','https://bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt','https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_mjo_index/proj_norm_order.ascii']
def check(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/plain,*/*;q=0.8'})
  with urllib.request.urlopen(req,timeout=20) as r:return (url,r.status,r.read(180).decode('utf-8',errors='replace'))
 except Exception as e:return (url,str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r in pool.map(check,urls):print(r)
