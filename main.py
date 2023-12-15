import config as cfg
from proxy import ProxyJuliang
import collection

juliang = cfg.get_juliang_configuration()

proxy = ProxyJuliang(juliang['username'], juliang['password'], juliang['params'])

# 验证
proxy.get_proxies()

c = collection.Collection("35208463", proxy)
c.collection()



