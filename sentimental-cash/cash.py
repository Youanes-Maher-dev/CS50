from cs50 import get_float

def calculate_quarters(n):
    quarters = 0
    while n >= 25:
        n = n - 25
        quarters += 1
    return quarters


def calculate_dimes(i):
    dimes = 0
    while i >= 10:
        i = i - 10
        dimes += 1
    return dimes

def calculate_nickels(k):
    nickels = 0
    while k >= 5:
        k = k - 5
        nickels += 1
    return nickels


def calculate_pennies(j):
    pennies = 0
    while j >= 1:
        j = j - 1
        pennies += 1
    return pennies



while True:
    coins = get_float("Change: ")
    if coins > float(0):
        break
total_cents = int(coins * 100)

quarters = calculate_quarters(total_cents)
total1_cents = total_cents - (quarters * 25)

dimes = calculate_dimes(total1_cents)
total2_cents = total1_cents - (dimes * 10)

nickels = calculate_nickels(total2_cents)
total3_cents = total2_cents - (nickels * 5)

pennies = calculate_pennies(total3_cents)

n = quarters + dimes + nickels + pennies
print (n)


