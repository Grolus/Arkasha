

with open("1.txt", "r") as file:
    r1 = file.read()
with open("1.txt", "w") as file:
    file.write(r1.replace(" ", "\n"))

with open("2.txt", "r") as file:
    r2 = file.read()
with open("2.txt", "w") as file:
    file.write(r2.replace(" ", "\n"))



