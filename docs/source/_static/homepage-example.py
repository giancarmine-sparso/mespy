from mespy import lin_fit

x = [0, 1, 2, 3, 4, 5]
y = [0.52, 0.92, 1.39, 1.76, 2.24, 2.61]
sigma_y = [0.10, 0.12, 0.10, 0.15, 0.12, 0.10]

lin_fit(x, y, sigma_y=sigma_y)
