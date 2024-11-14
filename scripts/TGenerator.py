import csv
import logging
import os

logger = logging.getLogger(__name__)

class TGenerator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tin_numbers = self._load_tins_from_csv(file_path)
        self.index = 0  # Track position in the list

    def _load_tins_from_csv(self, file_path):
        tin_numbers = []
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return tin_numbers  # Return empty list to handle the error gracefully

        try:
            with open(file_path, mode='r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    tin_numbers.append(row['Tin'])
            if not tin_numbers:
                logger.warning("No TINs found in CSV file.")
        except (FileNotFoundError, KeyError, IOError) as e:
            logger.error(f"Error loading TINs from CSV: {e}")
        return tin_numbers

    def get_next_numbers(self, n):
        if self.index >= len(self.tin_numbers):
            return []  # No more TINs to process
        next_batch = self.tin_numbers[self.index:self.index + n]
        self.index += n
        return next_batch