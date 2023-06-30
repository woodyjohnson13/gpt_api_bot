def cap_low(string):
    index = len(string)
    cap=""
    low=""
    for i in range(len(string)):
        if i % 2 == 0:
            cap = cap+ string[i].capitalize()
        else:
            low += string[i].lower()
    return cap, low
    




name = input()

cap_low(name)

print(cap_low(name))
