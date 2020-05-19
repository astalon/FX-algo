import matplotlib.pyplot as plt
plt.style.use('seaborn')
import pandas as pd
import math
import stats
from datetime import date

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


class trade_new:
    def __init__(self, entry, stop, trade_id):
        self.entry = entry
        self.stop = stop
        self.id = trade_id   

def log_trade(t_id, t_date, t_type, t_price, eqt):
    global trade_log
    columns = trade_log.columns
    trade = pd.DataFrame([[t_id, t_date, t_type, t_price, eqt]], columns=columns)
    trade_log = trade_log.append(trade)



#Load and prepare the necessary statistics
df = pd.read_excel('EURUSD org.xlsx')
dates = df.loc[:, 'Dates']
df = df.drop(labels=['Dates'], axis=1)

look_ahead = 2
df['labels'] = df['EURUSD Curncy'].shift(-look_ahead)
df = df.dropna()

labels=df['labels']

# df['2y change'] = df['2Y spread'].diff()
# df['5y change'] = df['5Y spread'].diff()
# df['EURUSD change'] = df['EURUSD Curncy'].diff()
df.dropna(inplace=True)


# for i in range(len(df)-look_ahead):
# 	if df.iloc[i+look_ahead, 0]>df.iloc[i, 0]:
# 		labels.iloc[i,] = 1
train = 0.65

df = df.drop(['labels'], axis=1)

labels = labels.iloc[:-look_ahead, ]
df = df.iloc[:-look_ahead, ]

row = math.floor(train*len(df))

train_input = df.iloc[:row,].to_numpy()
test_input = df.iloc[row:, ].to_numpy()
 
train_label = labels.iloc[:row, ].to_numpy()
test_label = labels.iloc[row:, ].to_numpy()

lm = stats.linreg(train_input, train_label)
lm.fit(False)

lm_predictions = []
for i in range(len(test_label)):
    lm_predictions.append(lm.predict(test_input[i, ].reshape(1, -1)))



trade_log = pd.read_excel("trade_log.xlsx", )
todays = test_input[:,0]    
equity = 1
buy = True
trade_id = 0
predicted = 0
for day in range(0, len(test_input), look_ahead):
    
    #Close current trade and log it
    if day > 0:
        if buy:
            equity *= todays[day]/todays[day-look_ahead]
            log_trade(trade_id, predicted, 'Close buy', todays[day], equity)
        else:
            equity *= todays[day-look_ahead]/todays[day]
            log_trade(trade_id, predicted, 'Close sell', todays[day], equity)

    trade_id += 1
    
    #Predict tomorrows value
    predicted = lm.predict(test_input[day,].reshape(1, -1))
    
    #Act on prediction
    if predicted > todays[day]:
        buy = True
        log_trade(trade_id, predicted, 'Buy', todays[day], equity)
    else:
        buy = False
        log_trade(trade_id, predicted, 'Sell', todays[day], equity)



#trade_log = trade_log.sort_values(by=['ID'])
trade_log.to_excel("trade_log" + str(date.today()) + ".xlsx", index=False)



