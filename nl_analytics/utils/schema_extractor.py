import pandas as pd
import os

def extract_schema(filepath: str) -> str:
    """
    Reads a CSV file and generates a schema summary including column names,
    data types, and representative sample values for prompt injection.
    """
    if not os.path.exists(filepath):
        return f"Error: CSV file not found at {filepath}"
    
    try:
        df = pd.read_csv(filepath)
        schema_lines = []
        schema_lines.append(f"Table Name: df")
        schema_lines.append(f"Total Rows: {len(df)}")
        schema_lines.append("Columns:")
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Get up to 3 non-null unique sample values
            non_null_samples = df[col].dropna().unique()
            samples = [str(x) for x in non_null_samples[:3]]
            sample_str = ", ".join(samples)
            schema_lines.append(f"  - {col} (Type: {dtype}, Samples: [{sample_str}])")
            
        return "\n".join(schema_lines)
    except Exception as e:
        return f"Error extracting schema: {str(e)}"
