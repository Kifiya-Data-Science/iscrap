# Here my TGenerator.py Script
import csv

class TGenerator:
    def __init__(self, file_path):
        self.tin_numbers = self._load_tins_from_csv(file_path)
        self.index = 0  # Keep track of the current position in the list

    def _load_tins_from_csv(self, file_path):
        tin_numbers = []
        with open(file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                tin_numbers.append(row['Tin'])
        return tin_numbers

    def get_next_numbers(self, n):
        """
        Returns the next batch of TIN numbers from the list.
        If there are fewer than 'n' remaining, it will return the remaining TINs.
        """
        if self.index >= len(self.tin_numbers):
            return []  # No more TINs to process

        next_batch = self.tin_numbers[self.index:self.index + n]
        self.index += n
        return next_batch

# class TGenerator:
#     def __init__(self):
#         self.generator = self._generate_numbers()

#     def _generate_numbers(self):
#         for i in range(100000000):  # 0 to 99999999
#             yield f'{i:08}'  # Format as 8-digit string, e.g., '00000000'

#     def get_next_numbers(self, n):
#         return [next(self.generator) for _ in range(n)]
    
    
    


