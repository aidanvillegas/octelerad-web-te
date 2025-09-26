# database_manager.py
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.df = None
        if db_path:
            self.load_database(db_path)

    def load_database(self, db_path):
        """Loads the database from the specified path."""
        self.db_path = db_path  # Update the internal database path
        if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            # Load the file with no assumption of headers, to handle files without them
            self.df = pd.read_csv(db_path, header=None)
            # If the file has more than one row and lacks proper headers, set them
            if len(self.df.columns) == 3:
                self.df.columns = ['Label', 'Expansion', 'Diagnosis']
            elif len(self.df.index) > 0:
                # Assume the first row is data if there are 3 columns, not headers
                new_header = pd.DataFrame([['Label', 'Expansion', 'Diagnosis']], columns=self.df.columns)
                self.df = pd.concat([new_header, self.df], ignore_index=True)
                self.df.columns = ['Label', 'Expansion', 'Diagnosis']

    def save_database(self):
        """Save the DataFrame to a CSV file."""
        self.df.to_csv(self.db_path, index=False)

    """ def get_Expansion(self, word):
        """"""Returns the Expansion of a word if it exists in the database."""""""
        if self.df is not None:
            result = self.df.loc[self.df['word'] == word, 'Expansion']
            if not result.empty:
                return result.iloc[0]
        return None """
    def get_Expansion(self, Label):
        if self.df is None:
            print("Debug: DataFrame is not initialized.")
            return "Database not initialized"

        if Label is None:
            print("Debug: Provided label is None")
            return "Label not provided"

        try:
            # Convert 'Label' column to string type to handle any type safely
            self.df['Label'] = self.df['Label'].astype(str)
            
            # Filtering the DataFrame safely
            result = self.df.loc[self.df['Label'].str.lower() == str(Label).lower(), 'Expansion']
            if not result.empty:
                return result.iloc[0]
        except Exception as e:
            print(f"An exception occurred: {e}")
            return "Error processing data"

        print("Debug: Expansion not found for the provided label.")
        return "Expansion not found"
    def get_suggestions(self, text):
        """Returns a list of suggestions for Labels matching the given text."""
        print(f"Searching for: {text}")
        if self.df is not None:
            matches = self.df[self.df['Label'].str.contains(text, case=False, na=False)]
            return matches['Label'].tolist()
        return []

    # def get_Expansion(self, Label):
    #     """Returns the Expansion for the given Label from the DataFrame."""
    #     if self.df is not None:
    #         # Filter the DataFrame for the given Label
    #         result = self.df.loc[self.df['Label'].str.lower() == Label.lower(), 'Expansion']
    #         # Check if any result was found
    #         if not result.empty:
    #             return result.iloc[0]  # Return the first match's Expansion
    #     return "Expansion not found"  # Return a default message if no match is found or if df is None
