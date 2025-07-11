from base import Normalize
from utils import get_calendar_list
import pandas as pd


calendar_list = get_calendar_list('US_ALL')
df = pd.DataFrame(index=calendar_list)

print(calendar_list[-1].tzinfo)
print([ts.tzinfo for ts in calendar_list if ts.tzinfo is not None])


# 确保所有时间戳都是tz-naive，通过将时区信息移除
calendar_list_naive = [ts.tz_localize(None) if ts.tzinfo is not None else ts for ts in calendar_list]
# df = pd.DataFrame(index=calendar_list_naive)
df = pd.DataFrame(index=calendar_list)

df = df.reindex(
        # pd.DataFrame(index=calendar_list_naive) 
        pd.DataFrame(index=calendar_list) 
        .loc[
            pd.Timestamp(df.index.min()).date() : pd.Timestamp(df.index.max()).date()
            + pd.Timedelta(hours=23, minutes=59)
        ]
        .index
    )

print(df)