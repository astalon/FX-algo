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
        
class order_simple:
    def __init__(self, order_level,  amount, days=3):
        self.amount = amount
        self.good_til = days
        self.order_level = order_level
        
    def decrement(self):
        self.good_til -= 1
        
class trade:
    def __init__(self, entry, target, stop, trade_id):
        self.entry = entry
        self.target = target
        self.stop = stop
        self.id = trade_id        



def log_trade(t_id, t_date, t_type, t_price, eqt):
    global trade_log
    columns = trade_log.columns
    trade = pd.DataFrame([[t_id, t_date, t_type, t_price, eqt]], columns=columns)
    trade_log = trade_log.append(trade)



#Load and prepare the necessary statistics
df = pd.read_excel('EURUSD.xlsx')
dates = df.loc[:, 'Dates']
df = df.drop(labels=['Dates'], axis=1)
np_arr = df.to_numpy().reshape(len(df))
#df.loc[:, 'RSI2'] = pd.Series(ti.rsi(np_arr, 2))
df.loc[:, 'RSI'] = pd.Series(ti.rsi(np_arr, 5))
#df.loc[:, 'RSI4'] = pd.Series(ti.rsi(np_arr, 4))
df.dropna(inplace=True)

# fig, axs = plt.subplots(2, 1)
# axs[0].plot(df.loc[100:200, "EURUSD Curncy"], linewidth=2)
# axs[1].plot(df.loc[100:200, 'RSI'], linewidth = 2)
# fig.suptitle('EURUSD and RSI(5)')
# plt.show()


cols = df.columns

trade_log = pd.read_excel("trade_log.xlsx", )
orders = []
portfolio = []
equity_array = [1]
equity = 1
trade_id = 0
winners = 0
losers = 0
avg_win = 0
avg_loss = 0

target_return = 1.04
order_pad = 1.01
stop_loss = 0.98

for day in range(len(df)):
	todays_price = df.iloc[day, 0]
	for obj in portfolio:
		if (obj.target < todays_price or todays_price < obj.stop):
			trade_return = (todays_price/obj.entry-1)*100
			equity *= todays_price/obj.entry
			log_trade(obj.id, dates[day], 'sell', todays_price, equity)		
			
			#Keep track of statistics
			if trade_return > 0:
				winners += 1
				avg_win += trade_return
			else:
				losers += 1
				avg_loss += trade_return
				
			#If portfolio item is sold, remove it from the portfolio
			equity_array.append(equity)
			portfolio.remove(obj)
	
	for item in orders:
		if todays_price > item.order_level:
			
			if todays_price > item.order_level*target_return/order_pad:
				orders.remove(item)
			else:
				trade_id += 1
				log_trade(trade_id, dates[day], 'buy', todays_price, equity)
				orders.remove(item)
				portfolio.append(trade(todays_price, todays_price*target_return, todays_price*stop_loss,trade_id))
				
	if df.iloc[day, 1] < 20:
		mrkt_order = order_simple(todays_price*order_pad, 1)
		orders.append(mrkt_order)
        

#Algorithm statistics        
trades = winners + losers
hit_ratio = 100*winners/trade_id
avg_win = avg_win/winners
avg_loss = avg_loss/losers

print("Equity: %.2f" %equity)
print("Hit ratio: %.2f" %hit_ratio)
print("Number of trades: ", trades)
print("average win: %.2f" %avg_win)
print("average loss: %.2f" %avg_loss)

plt.plot(equity_array, linewidth =2)
plt.title('Eqity curve backtest, mean reversion')
plt.show()

#trade_log = trade_log.sort_values(by=['ID'])
trade_log.to_excel("trade_log" + str(date.today()) + ".xlsx", index=False)



