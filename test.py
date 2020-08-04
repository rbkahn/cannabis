from vec_utils import generate_glove

years = [range(n, n+5) for n in range(1980, 2020, 5)] + [range(n, n+10) for n in range(1980, 2020, 10)]
for y in years:
    generate_glove(y)