
https://finance.sina.cn/2020-12-23/detail-iiznezxs8458252.d.html


qlib的数据源基于yahoo，但是不是最新的

数据格式：

cn_data 
目录下面有个
calendars   features    financial   instruments

calendars
└── day.txt

features 下面有 sh600418

$ tree sh600418 
sh600418
├── change.day.bin
├── close.day.bin
├── factor.day.bin
├── high.day.bin
├── low.day.bin
├── open.day.bin
└── volume.day.bin

$ tree sz000725
sz000725
├── roewa_q.data
├── roewa_q.index
├── yoyni_q.data
└── yoyni_q.index

1 directory, 4 files

tree instruments
all.txt    csi100.txt csi300.txt csi500.txt

eg:
SH000300	2005-01-04	2020-09-25
SH000903	2006-05-29	2020-09-25
SH600000	1999-11-10	2020-09-25
SH600004	2003-04-28	2020-09-25
SH600006	1999-11-10	2020-09-25
SH600007	1999-11-10	2020-09-25
SH600008	2000-04-27	2020-09-25
SH600009	1999-11-10	2020-09-25
SH600010	2001-03-09	2020-09-25
SH600011	2001-12-06	2020-09-25
SH600012	2003-01-09	2020-09-25
SH600015	2003-09-12	2020-09-25


scripts/data_collector下面可以高数据收集