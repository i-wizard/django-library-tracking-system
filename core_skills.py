import random
def create_random():
    numbers = [i+1 for i in range(20)]
    return random.choices(numbers, k=10)


def filter_below_10(random_numbers):
    return [i for i in random_numbers if i < 10]

def filter_below_10_(random_numbers):
    return list(filter(lambda x: x <10, random_numbers))

random_numbers_list = create_random()
numbers_below_10_list_comprehension = filter_below_10(random_numbers_list)
numbers_below_10_filter = filter_below_10_(random_numbers_list)
