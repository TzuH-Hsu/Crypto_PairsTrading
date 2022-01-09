money = 0
countS1 = 1
countS2 = 1
ratios =  prices_df["2021-01-01":]["ETHUSD"]/prices_df["2021-01-01":]["BNBUSD"]

for i in range(len(forecast_df1)):
    if logReturn_spreads_df["('ETHUSD', 'BNBUSD')"][i] > forecast_df1["VaR-80.0%"][i] and countS1 > 0:
        money += prices_df["2021-01-01":]["ETHUSD"][i] - prices_df["2021-01-01":]["BNBUSD"][i] * ratios[i]
        countS1 -= 1
        countS2 += ratios[i]

    if logReturn_spreads_df["('ETHUSD', 'BNBUSD')"][i] < forecast_df1["VaR-20.0%"][i] and countS2 > 0:
        money -= prices_df["2021-01-01":]["ETHUSD"][i] - prices_df["2021-01-01":]["BNBUSD"][i] * ratios[i]
        countS1 += 1
        countS2 -= ratios[i]

money = money + countS1 * prices_df["ETHUSD"][-1] + countS2 * prices_df["BNBUSD"][-1]

print((prices_df["2021-01-01":]["ETHUSD"][-1] - prices_df["2021-01-01":]["ETHUSD"][0])/prices_df["2021-01-01":]["ETHUSD"][0])
print((prices_df["2021-01-01":]["BNBUSD"][-1] - prices_df["2021-01-01":]["BNBUSD"][0])/prices_df["2021-01-01":]["BNBUSD"][0])
print((money - (prices_df["2021-01-01"]["ETHUSD"][0]+prices_df["2021-01-01"]["BNBUSD"][0]))/(prices_df["2021-01-01"]["ETHUSD"][0]+prices_df["2021-01-01"]["BNBUSD"][0]))

print(prices_df["2021-01-01":]["ETHUSD"][0])
print(prices_df["2021-01-01":]["ETHUSD"][-1])