import numpy as np
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import pandas as pd
import math
from datetime import date
import tulipy as ti

class order:
	def __init__(self, share, order_level,  amount, days=5):
		self.stock = share
		self.amount = amount
		self.good_til = days
		self.order_level = order_level
		
	def decrement(self):
		self.good_til -= 1
		
class order_long_short:
	def __init__(self, order_level,  amount, order_type, days=3):
		self.amount = amount
		self.good_til = days
		self.order_type = order_type
		self.order_level = order_level
		
	def decrement(self):
		self.good_til -= 1
		
class trade:
	def __init__(self, entry, target, stop, trade_id, trade_type):
		self.entry = entry
		self.target = target
		self.stop = stop
		self.id = trade_id        
		self.trade_type = trade_type

def log_trade(t_id, t_date, t_type, t_price, eqt):
	global trade_log
	columns = trade_log.columns
	trade = pd.DataFrame([[t_id, t_date, t_type, t_price, eqt]], columns=columns)
	trade_log = trade_log.append(trade)



#Load and prepare the necessary statistics
df = pd.read_excel('EURUSD.xlsx')
dates = df.loc[:, 'Dates']
df = df.drop(labels=['Dates'], axis=1)

#df['20ema'] = df['EURUSD'].ewm(span=20).mean()
df['sma20'] = df['EURUSD'].rolling(window=20).mean()
df['sma50'] = df['EURUSD'].rolling(window=50).mean()
df['std'] = df['EURUSD'].rolling(window=20).std()

df.dropna(inplace=True)

df['UB'] = df['sma20'] + 1*df['std'] 
df['LB'] = df['sma20'] - 1*df['std'] 

#Trending upwards if 20 EMA > 50 SMA
#Downwards if 20 EMA < 50 SMA
#Average band distance? Mean reversion


starting_cash = 100000

cols = df.columns

trade_log = pd.read_excel("trade_log.xlsx")
orders = []
portfolio = []
equity_array = [1]
equity = 1
trade_id = 1
winners_long = 0
losers_long = 0
avg_win_long = 0
avg_loss_long = 0
winners_short = 0
losers_short = 0
avg_win_short = 0
avg_loss_short = 0
yesterdays_row = df.iloc[0, :]
df = df.iloc[1:, :]
for row in df.itertuples():
	active_trades = len(portfolio)
	todays_price = row.EURUSD
	yesterdays_price = yesterdays_row.EURUSD

	for obj in portfolio:
		if obj.trade_type == 'long':
			if todays_price > obj.target or todays_price < obj.stop:
				trade_return = todays_price/obj.entry
				equity *= trade_return
				log_trade(obj.id, dates[row.Index], 'Sell', todays_price, equity)

				if trade_return > 1:
					winners_long += 1
					avg_win_long += trade_return
				else:
					losers_long += 1
					avg_loss_long += trade_return

				equity_array.append(equity)
				portfolio.remove(obj)

		else:
			if todays_price < obj.target or todays_price > obj.stop:
				trade_return = obj.entry/todays_price
				equity *= trade_return
				log_trade(obj.id, dates[row.Index], 'Buy back', todays_price, equity)
			
				if trade_return > 1:
					winners_short += 1
					avg_win_short += trade_return
				else:
					losers_short += 1
					avg_loss_short += trade_return

				equity_array.append(equity)
				portfolio.remove(obj)
				
	# Need to distinguish between orders for long and short trades
	# Where to put entry
	# Only short trades in down-trend, only long in uptrend
	# Play around with order expiry
	# Check closing prices of three days, below -> above -> below or vice versa to avoid curve balls

	for item in orders:
		if item.order_type == 'long':
			if todays_price > item.order_level:
				tmp_trade = trade(item.order_level, row.sma20, row.LB*0.98, trade_id, 'long')
				log_trade(trade_id, dates[row.Index], 'long', item.order_level, equity)
				portfolio.append(tmp_trade)
				orders.remove(item)
				trade_id += 1

		else:
			if todays_price < item.order_level:
				tmp_trade = trade(item.order_level, row.sma20, row.UB*1.02, trade_id, 'short')
				log_trade(trade_id, dates[row.Index], 'short', item.order_level, equity)
				portfolio.append(tmp_trade)
				orders.remove(item)
				trade_id += 1

	uptrend = row.sma20 > row.sma50


	if todays_price < row.LB and yesterdays_price > row.LB:
		order = order_long_short(row.LB, 1, 'long')
		orders.append(order)
	elif todays_price > row.UB and yesterdays_price < row.UB:
		order = order_long_short(row.UB, 1, 'short')
		orders.append(order)

	#Only place buy orders in up-trend and sell orders in down-trend
	# if uptrend:
	# 	if todays_price < row.LB and yesterdays_price > row.LB:
	# 		order = order_long_short(row.LB, 1, 'long')
	# 		orders.append(order)
	# else:
	# 	if todays_price > row.UB and yesterdays_price < row.UB:
	# 		order = order_long_short(row.UB, 1, 'short')
	# 		orders.append(order)
		

# #Algorithm statistics     
years = len(df)/260
CAGR = np.power(equity, 1/years)-1

print("Total equity: %.2f" %equity)
print("CAGR: %.2f" %CAGR)


trades_long = winners_long + losers_long
hit_ratio_long = 100*winners_long/trades_long
avg_win_long = avg_win_long/winners_long
avg_loss_long = avg_loss_long/losers_long

print("\n")
print("Long trades statistics")
print("Hit ratio: %.2f" %hit_ratio_long)
print("Number of trades:", trades_long)
print("average win: %.3f" %avg_win_long)
print("average loss: %.3f" %avg_loss_long)

trades_short = winners_short + losers_short
hit_ratio_short = 100*winners_short/trades_short
avg_win_short = avg_win_short/winners_short
avg_loss_short = avg_loss_short/losers_short

print("\n")
print("Short trades statistics")
print("Hit ratio: %.2f" %hit_ratio_short)
print("Number of trades:", trades_short)
print("average win: %.3f" %avg_win_short)
print("average loss: %.3f" %avg_loss_short)

plt.plot(equity_array, linewidth =2)
plt.title('Equity curve backtest, mean reversion')
plt.show()

trade_log = trade_log.sort_values(by=['ID'])
trade_log.to_excel("trade_log" + str(date.today()) + ".xlsx", index=False)



