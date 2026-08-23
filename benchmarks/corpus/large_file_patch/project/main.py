def double(value):
    return value * 2


def triple(value):
    return value * 3


def square(value):
    return value * value


def describe(number):
    if number % 2 == 0:
        return "even"
    return "odd"


def is_positive(number):
    return number > 0


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def join_words(words, separator=" "):
    return separator.join(words)


def count_chars(text):
    return len(text)


def summarize(items):
    total = 0
    for item in items:
        total += item
    return total


def total_length(words):
    total = 0
    for word in words:
        total += len(word)
    return total_length


def main():
    words = ["hi", "there"]
    print(f"total: {total_length(words)}")


if __name__ == "__main__":
    main()
