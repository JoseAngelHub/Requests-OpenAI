from decimal import Decimal

# Function to convert Decimal objects to float to avoid errors when converting to JSON
def convert_decimals(obj):
    # Check if the object is of type Decimal
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    return str(obj)  # Return the object as a string for other types
