# import pandas as pd
#
# df = pd.read_csv("main_data.csv")
# print("Columns in the dataset:", df.columns)


# import pandas as pd
#
# # Load the CSV file
# df = pd.read_csv("main_data_updated.csv")
#
# # Print the column names
# print("Columns in the dataset:", df.columns)

# import pandas as pd
#
# # Load the dataset
# df = pd.read_csv("main_data_updated.csv")
#
# # Movie names to check
# movies_to_check = ["where's my dog?!", "future world"]
#
# # Check if movies exist in the dataset
# for movie in movies_to_check:
#     if movie in df['movie_title'].values:  # Updated column name
#         print(f"\u2705 '{movie}' found in dataset!")
#         print(df[df['movie_title'] == movie])  # Show details
#     else:
#         print(f"\u274C '{movie}' NOT found in dataset!")



# import pandas as pd
# df = pd.read_csv('main_data_updated.csv')
# print(df.head())  # Check if data is loaded
# print(df.columns)  # Ensure column names are correct
# print(df['movie_title'].head())  # Check movie titles

#
# import pandas as pd
#
# # Load the CSV file
# data = pd.read_csv('main_data_updated.csv')
#
# # Display first few rows
# print(data.head())
#
# # Check for missing values
# print(data.isnull().sum())
#
# # Print available columns
# print(data.columns)
#
# # Ensure 'movie_title' is properly formatted
# print(data['movie_title'].str.lower().unique())


import pandas as pd

# Load the dataset
file_path = 'main_data_updated.csv'  # Ensure this is the correct path
try:
    data = pd.read_csv(file_path)
    print("Data loaded successfully!\n")
    print("First 5 rows:\n", data.head())  # Show first 5 rows
    print("\nColumn names:\n", data.columns)  # Show column names
    print("\nData types:\n", data.dtypes)  # Show data types
    print("\nMissing values:\n", data.isnull().sum())  # Check for missing values
except Exception as e:
    print(f"Error loading data: {e}")

