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
	def __init__(self, order_level, order_type, days=3):
		self.good_til = days
		self.order_type = order_type
		self.order_level = order_level
		
	def decrement(self):
		self.good_til -= 1
		
class trade:
	def __init__(self, entry, target, stop, trade_id, trade_type, invested):
		self.entry = entry
		self.target = target
		self.stop = stop
		self.id = trade_id        
		self.trade_type = trade_type
		self.invested = invested

def log_trade(t_id, t_date, t_type, t_price, eqt):
	global trade_log
	columns = trade_log.columns
	trade = pd.DataFrame([[t_id, t_date, t_type, t_price, eqt]], columns=columns)
	trade_log = trade_log.append(trade)



#Load and prepare the necessary statistics
df = pd.read_excel('EURUSD.xlsx')
dates = df.loc[:, 'Dates']
df = df.drop(labels=['Dates'], axis=1)


df['sma20'] = df['EURUSD'].rolling(window=7).mean()
df['std'] = df['EURUSD'].rolling(window=7).std()

df.dropna(inplace=True)

df['UB'] = df['sma20'] + df['std'] 
df['LB'] = df['sma20'] - df['std'] 



#Average band distance? Mean reversion

current_cash = 100000
start_cash = current_cash

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
invested = 0

def exit_position(position, fraction, sell_price):
	global winners_long
	global losers_long
	global winners_short
	global losers_short

	global avg_win_long
	global avg_loss_long
	global avg_win_short
	global avg_loss_short

	global current_cash
	global equity
	global equity_array


	invested = -position.invested
	for obj in portfolio:
		invested += obj.invested

	if position.trade_type == 'long':
		
		trade_return = sell_price/position.entry
		if trade_return > 1:
			# df_plot.iloc[:row.Index-9,].plot(linewidth=1)
			# plt.title("Exit long, win")
			# plt.show()
			winners_long += 1
			avg_win_long += trade_return
		else:

			losers_long += 1
			avg_loss_long += trade_return

		current_cash += position.invested*fraction*trade_return 
		equity = (current_cash+invested)/start_cash
		log_trade(obj.id, dates[row.Index], 'Sell', sell_price, equity)

		if fraction == 1:
			portfolio.remove(obj)
		else:
			position.invested *= (1-fraction)
		
		equity_array.append(equity)

	### Logic for exiting short positions
	else:

		trade_return = position.entry/sell_price
		
		if trade_return > 1:
			winners_short += 1
			avg_win_short += trade_return
		
		else:
			losers_short += 1
			avg_loss_short += trade_return

		current_cash += position.invested*fraction*trade_return 
		equity = (current_cash+invested)/start_cash
		log_trade(obj.id, dates[row.Index], 'Buy', sell_price, equity)

		if fraction == 1:
			portfolio.remove(obj)
		else:
			position.invested *= (1-fraction)
		
		equity_array.append(equity)


def enter_position():
	None

df_plot = df.loc[:, df.columns!='std']

for row in df.itertuples():
	active_trades = len(portfolio)
	todays_price = row.EURUSD
	yesterdays_price = yesterdays_row.EURUSD

	for obj in portfolio:
		obj.target = row.sma20
		if obj.trade_type == 'long':
			obj.stop = row.LB*0.98
			if todays_price > obj.target:
				exit_position(obj, 1, obj.target)
			elif todays_price < obj.stop:
				exit_position(obj, 1, obj.stop)

		else:
			obj.stop = row.UB*1.02
			if todays_price < obj.target:
				exit_position(obj, 1, obj.target)
			elif todays_price > obj.stop:
				exit_position(obj, 1, obj.stop)

	# Play around with order expiry
	# Check closing prices of three days, below -> above -> below or vice versa to avoid curve balls
	# Investigate if, and how, we can get more out of out winners
	# Köra flera valutor samtidigt på något smart sätt
	# Limit for current_cash when to re-weight

	# Always want to be fully invested, split cash among "wanted" positions evenly
	# Write function for entering trade, enter_position()
	for item in orders:
		if item.order_type == 'long':
			if todays_price > item.order_level:

				if current_cash < 5:
					fraction_to_sell = 1/(len(portfolio)+1)
					for obj in portfolio:
						exit_position(obj, fraction_to_sell, item.order_level) 


				tmp_trade = trade(item.order_level, row.sma20, row.LB*0.98, trade_id, 'long', current_cash)
				log_trade(trade_id, dates[row.Index], 'long', item.order_level, equity)
				portfolio.append(tmp_trade)
				orders.remove(item)
				trade_id += 1

		else:
			if todays_price < item.order_level:

				if current_cash < 5:
					fraction_to_sell = 1/(len(portfolio)+1)
					for obj in portfolio:
						exit_position(obj, fraction_to_sell, item.order_level) 

				tmp_trade = trade(item.order_level, row.sma20, row.UB*1.02, trade_id, 'short', current_cash)
				log_trade(trade_id, dates[row.Index], 'short', item.order_level, equity)
				portfolio.append(tmp_trade)
				orders.remove(item)
				trade_id += 1


	if todays_price < row.LB and yesterdays_price > yesterdays_row.LB:
		
		order = order_long_short(row.LB, 'long')
		orders.append(order)
	elif todays_price > row.UB and yesterdays_price < yesterdays_row.UB:

		order = order_long_short(row.UB, 'short')
		orders.append(order)
		
	yesterdays_row = row
		

# #Algorithm statistics     
years = len(df)/260
CAGR = np.power(equity, 1/years)-1

print("Total equity: %.2f" %equity)
print("CAGR: %.2f" %CAGR)


trades_long = winners_long + losers_long
hit_ratio_long = 100*winners_long/trades_long
avg_win_long = avg_win_long/winners_long
avg_loss_long = avg_loss_long/losers_long

print()
print("Long trades statistics")
print("Hit ratio: %.2f" %hit_ratio_long)
print("Number of trades:", trades_long)
print("average win: %.3f" %avg_win_long)
print("average loss: %.3f" %avg_loss_long)

trades_short = winners_short + losers_short
hit_ratio_short = 100*winners_short/trades_short
avg_win_short = avg_win_short/winners_short
avg_loss_short = avg_loss_short/losers_short

print()
print("Short trades statistics")
print("Hit ratio: %.2f" %hit_ratio_short)
print("Number of trades:", trades_short)
print("average win: %.3f" %avg_win_short)
print("average loss: %.3f" %avg_loss_short)

plt.plot(equity_array, linewidth =2)
plt.title('Equity curve backtest, mean reversion')
plt.show()

trade_log = trade_log.sort_values(by=['Date'])
trade_log.to_excel("trade_log" + str(date.today()) + ".xlsx", index=False)



