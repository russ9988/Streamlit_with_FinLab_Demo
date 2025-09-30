from datetime import datetime
import pandas as pd
from finlab import data as finlab_data

class stock:
    now = datetime.now()

    def __init__(self, stock_code: str, from_month: int) -> None:
        self.stock_code = str(stock_code).strip()
        self.from_month = int(from_month)
        if self.now.month < self.from_month:
            self.start = datetime(self.now.year - 1, self.from_month, 1)
        else:
            self.start = datetime(self.now.year, self.from_month, 1)

    def _slice_date(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            df.index = pd.to_datetime(df.index)
        return df.loc[self.start.date():]

    def get_price_value(self) -> pd.DataFrame:
        open_df  = self._slice_date(finlab_data.get('price:開盤價'))
        high_df  = self._slice_date(finlab_data.get('price:最高價'))
        low_df   = self._slice_date(finlab_data.get('price:最低價'))
        close_df = self._slice_date(finlab_data.get('price:收盤價'))
        vol_df   = self._slice_date(finlab_data.get('price:成交股數'))
        try:
            s_open  = open_df[self.stock_code]
            s_high  = high_df[self.stock_code]
            s_low   = low_df[self.stock_code]
            s_close = close_df[self.stock_code]
            s_vol   = vol_df[self.stock_code]
        except KeyError as e:
            available = list(close_df.columns[:15])
            raise KeyError(f'找不到代號 {self.stock_code}，請確認是否正確。可用範例(前15檔)：{available}') from e
        out = pd.DataFrame({
            '日期': s_close.index,
            '開盤價': s_open.values,
            '最高價': s_high.values,
            '最低價': s_low.values,
            '收盤價': s_close.values,
            '成交量': s_vol.values,
        }).dropna()
        out['日期'] = pd.to_datetime(out['日期'])
        return out.reset_index(drop=True)

    def get_three_major(self) -> pd.DataFrame:
        candidates = {
            '外資': 'institutional_investors:外資買賣超股數',
            '投信': 'institutional_investors:投信買賣超股數',
            '自營商': 'institutional_investors:自營商買賣超股數',
        }
        series = {}
        for name, key in candidates.items():
            try:
                df = self._slice_date(finlab_data.get(key))
                series[name] = df[self.stock_code]
            except Exception:
                series[name] = None
        if any(s is None for s in series.values()):
            alt = {
                '外資': 'institutional_investors:外資買賣超(股數)',
                '投信': 'institutional_investors:投信買賣超(股數)',
                '自營商': 'institutional_investors:自營商買賣超(股數)',
            }
            for name, key in alt.items():
                if series.get(name) is None:
                    try:
                        df = self._slice_date(finlab_data.get(key))
                        series[name] = df[self.stock_code]
                    except Exception:
                        series[name] = None
        if any(s is None for s in series.values()):
            return pd.DataFrame(columns=['日期','外資','投信','自營商','單日合計'])
        data = pd.DataFrame({
            '日期': series['外資'].index,
            '外資': series['外資'].values,
            '投信': series['投信'].values,
            '自營商': series['自營商'].values,
        })
        data['單日合計'] = data[['外資','投信','自營商']].sum(axis=1)
        data['日期'] = pd.to_datetime(data['日期'])
        return data.reset_index(drop=True)

    def get_all_data(self, enable_color: bool = True) -> pd.DataFrame:
        prices = self.get_price_value()
        t86 = self.get_three_major()
        if prices.empty:
            return prices
        if t86.empty:
            data = prices.copy()
        else:
            data = pd.merge(t86, prices, on='日期', how='inner')
        if data.empty:
            return data
        if enable_color:
            if '外資' in data:
                data['外資買賣顏色'] = data['外資'].apply(lambda x: '#FF0000' if x > 0 else '#008E09')
                data['投信買賣顏色'] = data['投信'].apply(lambda x: '#FF0000' if x > 0 else '#008E09')
                data['自營商買賣顏色'] = data['自營商'].apply(lambda x: '#FF0000' if x > 0 else '#008E09')
            data['收盤價買賣顏色'] = (data['收盤價'] - data['開盤價']).apply(lambda x: '#FF0000' if x > 0 else '#008E09')
            data['成交量買賣顏色'] = (data['收盤價'] - data['開盤價']).apply(lambda x: '#FF0000' if x > 0 else '#008E09')
        return data.sort_values('日期').reset_index(drop=True)