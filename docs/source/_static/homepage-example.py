from mespy import lin_fit

x = [0, 1, 2, 3, 4, 5]
y = [0.57, 1.13, 1.28, 1.89, 2.17, 2.77]
sigma_y = [0.10, 0.12, 0.10, 0.15, 0.12, 0.10]

lin_fit(x, y, sigma_y=sigma_y, style="report")
