from cs50 import get_string

text = get_string ("Text: ")
letters = 0
spaces = 0
sentences = 0

for characters in text:
    if characters.isalpha():
        letters += 1
    elif characters == " ":
        spaces += 1
    elif characters == "." or characters == "?" or characters == "!":
        sentences += 1

words = spaces + 1
L = (letters/ words) * 100
S = (sentences/ words) * 100

index = 0.0588 * L - 0.296 * S - 15.8

if index > 16 :
    print("Grade 16+")
elif index < 1:
    print("Before Grade 1")
else:
    print(f"Grade {round(index)}")
