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

		
class order_long_short:
	def __init__(self, order_level,  amount, order_type, days=3):
		self.amount = amount
		self.good_til = days
		self.order_type = order_type
		self.order_level = order_level
		
	def decrement(self):
		self.good_til -= 1
		
class trade:
	def __init__(self, entry, target, stop, trade_id, trade_type, index_enter, size):
		self.entry = entry
		self.target = target
		self.stop = stop
		self.id = trade_id        
		self.trade_type = trade_type
		self.index_enter = index_enter
		self.size = size

def log_trade(t_id, t_date, t_type, t_price, eqt, open_trades):
	global trade_log
	columns = trade_log.columns
	trade = pd.DataFrame([[t_id, t_date, t_type, t_price, eqt, open_trades]], columns=columns)
	trade_log = trade_log.append(trade)


#Load and prepare the necessary statistics
df = pd.read_excel('SPYOHLCDaily.xlsx')
dates = df.loc[:, 'Dates']
df = df.drop(labels=['Dates'], axis=1)

leverage = 1
spread = 0
time_period = 3
num_std = 1

df['TR'] = df['H'] - df['L']

df['ATR'] = df['TR'].rolling(window=time_period).mean()
df['sma5'] = df['C'].rolling(window=time_period).mean()
df['std'] = df['C'].rolling(window=time_period).std()

df.dropna(inplace=True)

df['UB'] = df['sma5'] + num_std*df['std'] 
df['LB'] = df['sma5'] - num_std*df['std'] 

#Average band distance? Mean reversion

current_cash = 100000

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

max_open_trades = 1
current_open_trades = 0
position_size = 1/max_open_trades

df_plot = df.drop(['std', 'TR', 'ATR', 'H', 'O'], axis=1)

avg_hold_long_loss = 0
avg_hold_long_win = 0
avg_hold_short_loss = 0
avg_hold_short_win = 0

for row in df.itertuples():
	active_trades = len(portfolio)
	todays_high = row.H
	todays_low = row.L
	todays_close = row.C
	#todays_price = row.EURUSD
	yesterdays_close = yesterdays_row.C

	if current_open_trades < max_open_trades:
		if yesterdays_row.L < yesterdays_row.LB and yesterdays_close > yesterdays_row.LB:
			tmp_trade = trade(row.O, row.UB, yesterdays_row.L - yesterdays_row.ATR*0.05, trade_id, 'long', row.Index, position_size)
			log_trade(trade_id, dates[row.Index], 'long', row.O, equity, current_open_trades+1)
			portfolio.append(tmp_trade)
			current_open_trades += 1
			trade_id += 1

		elif yesterdays_row.H > yesterdays_row.UB and yesterdays_close < yesterdays_row.UB:
			tmp_trade = trade(row.O, row.LB, yesterdays_row.H + yesterdays_row.ATR*0.05, trade_id, 'short', row.Index, position_size)
			log_trade(trade_id, dates[row.Index], 'long', row.O, equity, current_open_trades+1)
			portfolio.append(tmp_trade)
			current_open_trades += 1
			trade_id += 1

	# Check if we were stopped out or took profit for any trades during the day

	for obj in portfolio[:]:

		if obj.trade_type == 'long':
			if todays_high > obj.target or todays_low < obj.stop:
				sell_price = obj.target if todays_high > obj.target else obj.stop

				trade_return = (sell_price/obj.entry-1)*leverage -2*spread/10000+1
				#trade_return = sell_price/obj.entry

				equity_return = (trade_return-1)*obj.size + 1 
				equity *= equity_return

				log_trade(obj.id, dates[row.Index], 'Sell', sell_price, equity, 1/obj.size)

				if trade_return > 1:
					# df_plot.iloc[:row.Index-9,].plot(linewidth=2)
					# plt.title("Exit long, win ")
					# plt.show()
					winners_long += 1
					avg_win_long += trade_return
					avg_hold_long_win += (row.Index-obj.index_enter)
				else:	
					# df_plot.iloc[:row.Index-9,].plot(linewidth=2)
					# plt.title("Exit long, loss ")
					# plt.show()								
					losers_long += 1
					avg_loss_long += trade_return
					avg_hold_long_loss += (row.Index-obj.index_enter)


				equity_array.append(equity)
				portfolio.remove(obj)
				current_open_trades -= 1

		else:
			if todays_low < obj.target or todays_high > obj.stop:
				sell_price = obj.target if todays_low < obj.target else obj.stop

				trade_return = (obj.entry/sell_price-1)*leverage -2*spread/10000+1
				#trade_return = obj.entry/sell_price
				equity_return = (trade_return-1)*obj.size + 1 
				equity *= equity_return


				log_trade(obj.id, dates[row.Index], 'Buy back', sell_price, equity, 1/obj.size)
			
				if trade_return > 1:
					# df_plot.iloc[:row.Index-9,].plot(linewidth=2)
					# plt.title("Exit short, win ")
					# plt.show()
					winners_short += 1
					avg_win_short += trade_return
					avg_hold_short_win += (row.Index-obj.index_enter)
				else:
					# df_plot.iloc[:row.Index-9,].plot(linewidth=2)
					# plt.title("Exit short, loss ")
					# plt.show()	
					losers_short += 1
					avg_loss_short += trade_return
					avg_hold_short_loss += (row.Index-obj.index_enter)

				equity_array.append(equity)
				portfolio.remove(obj)
				current_open_trades -= 1				

	yesterdays_row = row
		

# #Algorithm statistics     
# years = 140/260
years = len(df)/260
CAGR = np.power(equity, 1/years)-1

print("Leverage used:", leverage)
print("Spread used:", spread)

print("Total equity: %.2f" %equity)
print("CAGR: %.2f" %CAGR)


trades_long = winners_long + losers_long
hit_ratio_long = 100*winners_long/trades_long
avg_win_long = (avg_win_long/winners_long-1)*10000
avg_loss_long = (avg_loss_long/losers_long-1)*10000
profit_loss_ratio_long = avg_win_long/abs(avg_loss_long)
exp_long_return = hit_ratio_long * avg_win_long/100 + avg_loss_long*(1-hit_ratio_long/100)

print()
print("Long trades statistics")
print("Hit ratio: %.2f" %hit_ratio_long)
print("Number of trades:", trades_long)
print("average win: %.3f" %avg_win_long)
print("average loss: %.3f" %avg_loss_long)
print("profit to loss ratio: %.3f" %profit_loss_ratio_long)
print("expected trade return: %.3f" %exp_long_return)

trades_short = winners_short + losers_short
hit_ratio_short = 100*winners_short/trades_short
avg_win_short = (avg_win_short/winners_short-1)*10000
avg_loss_short = (avg_loss_short/losers_short-1)*10000
profit_loss_ratio_short = avg_win_short/abs(avg_loss_short)
exp_short_return = hit_ratio_short * avg_win_short/100 + avg_loss_short*(1-hit_ratio_short/100)

print()
print("Short trades statistics")
print("Hit ratio: %.2f" %hit_ratio_short)
print("Number of trades:", trades_short)
print("average win: %.3f" %avg_win_short)
print("average loss: %.3f" %avg_loss_short)
print("profit to loss ratio short: %.3f" %profit_loss_ratio_short)
print("expected trade return: %.3f" %exp_short_return)

# plt.plot(equity_array, linewidth =2)
# plt.title('Equity curve backtest, mean reversion')
# plt.show()

# trade_log = trade_log.sort_values(by=['ID'])
# trade_log.to_excel("trade_log" + str(date.today()) + ".xlsx", index=False)



