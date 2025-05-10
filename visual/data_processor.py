import pandas as pd
import os

def parse_model_details(df):
    """
    Parses model_combination to extract teacher and student models,
    and refines model_type into a clear training_method.
    Handles cases with explicit teacher-student pairs and standalone models.
    """
    # Initialize new columns
    df['teacher_model'] = 'None' # Default for cases with no explicit teacher
    df['student_model_arch'] = ''
    df['training_method'] = '' # Will be 'Teacher', 'TaskOnly', 'RDT', 'Follower', or 'Direct'

    for index, row in df.iterrows():
        model_combination = str(row['model_combination']) # Ensure string type
        model_type = str(row['model_type'])

        if '-' in model_combination: # Explicit Teacher-Student Pair
            parts = model_combination.split('-', 1)
            df.loc[index, 'teacher_model'] = parts[0]
            df.loc[index, 'student_model_arch'] = parts[1]

            if model_type == 'Teacher':
                df.loc[index, 'training_method'] = 'Teacher'
                # In this case, the 'value' pertains to the teacher_model itself.
                # For consistency, student_model_arch could be set to teacher_model if it's a teacher's metric.
                # However, the problem implies comparing student methods, so this row is a baseline for the teacher.
            elif model_type == 'Student_TaskOnly':
                df.loc[index, 'training_method'] = 'TaskOnly'
            elif model_type == 'Student_RDT':
                df.loc[index, 'training_method'] = 'RDT'
            elif model_type == 'Student_Follower':
                df.loc[index, 'training_method'] = 'Follower'
            else:
                df.loc[index, 'training_method'] = model_type # Fallback, should not happen with given types
        
        else: # Standalone model in model_combination (e.g., "PatchTST", "DLinear")
            # This model_combination is the primary architecture being referred to.
            # It can be a "Teacher" itself, or it can be a "Student" (TaskOnly, RDT, Follower) where the teacher is "None".
            
            if model_type == 'Teacher':
                # This is a standalone model acting as a teacher/baseline.
                df.loc[index, 'teacher_model'] = model_combination # It is its own teacher in this context
                df.loc[index, 'student_model_arch'] = model_combination # The architecture is itself
                df.loc[index, 'training_method'] = 'Teacher' # Or 'Direct_Teacher_Baseline'
            elif model_type == model_combination: # e.g. model_combination='PatchTST', model_type='PatchTST'
                df.loc[index, 'teacher_model'] = 'None' # Or model_combination if it's a baseline
                df.loc[index, 'student_model_arch'] = model_combination
                df.loc[index, 'training_method'] = 'Direct' # Indicates direct training of this model
            elif model_type in ['Student_TaskOnly', 'Student_RDT', 'Student_Follower']:
                # This is a student model (e.g. PatchTST) whose teacher is "None"
                # as per user feedback like (None, 'PatchTST')
                df.loc[index, 'teacher_model'] = 'None'
                df.loc[index, 'student_model_arch'] = model_combination # The model_combination is the student arch
                if model_type == 'Student_TaskOnly':
                    df.loc[index, 'training_method'] = 'TaskOnly'
                elif model_type == 'Student_RDT':
                    df.loc[index, 'training_method'] = 'RDT'
                elif model_type == 'Student_Follower':
                    df.loc[index, 'training_method'] = 'Follower'
            else:
                # Fallback for unknown model_type with single model_combination
                df.loc[index, 'student_model_arch'] = model_combination
                df.loc[index, 'training_method'] = model_type # Or 'Unknown'


    # Create a display name for the model being evaluated in the row
    # If training_method is 'Teacher', the value is for the 'teacher_model'.
    # Otherwise, the value is for the 'student_model_arch' trained with that method.
    df['evaluated_model_for_row'] = df.apply(
        lambda r: r['teacher_model'] if r['training_method'] == 'Teacher' and r['teacher_model'] != 'None' and '-' not in str(r['model_combination'])
        else (str(r['model_combination']).split('-',1)[0] if r['training_method'] == 'Teacher' and '-' in str(r['model_combination']) else r['student_model_arch']), axis=1
    )
    
    # Refine student_model_arch for rows where it might be empty due to 'Teacher' type in a pair
    # For a 'Teacher' type in a 'T-S' combo, the student_model_arch is still S.
    # The value pertains to T, but the context is the T-S pair.
    # This logic is complex; the key is what we group by for comparison.
    # We want to group by (dataset, horizon, teacher_model, student_model_arch)
    # and then compare training_method (TaskOnly, RDT, Follower) for that student_model_arch.
    # The 'Teacher' training_method gives the baseline for that teacher_model.

    return df

def load_and_process_data(csv_path='results/collected_partial_summary.csv'):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    df = parse_model_details(df)
    
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.dropna(subset=['value'], inplace=True)

    df.rename(columns={
        'dataset': 'dataset', 'horizon': 'horizon', 'split': 'split',
        'metric': 'metric', 'value': 'value'
    }, inplace=True)

    # Fill NaN values first (especially in numeric columns that might become strings later)
    df.fillna('', inplace=True)
    # Then replace specific strings like 'None', 'N/A' (case-insensitive, trims whitespace)
    df.replace(to_replace=r'^\s*(None|N/A)\s*$', value='', regex=True, inplace=True)
    
    return df

if __name__ == '__main__':
    processed_df = load_and_process_data()
    if processed_df is not None:
        print("Data loaded and processed successfully.")
        print(f"Shape: {processed_df.shape}")
        
        # Print unique combinations of key new columns to verify parsing
        print("\nUnique Teacher Models:", processed_df['teacher_model'].unique())
        print("Unique Student Model Archs:", processed_df['student_model_arch'].unique())
        print("Unique Training Methods:", processed_df['training_method'].unique())
        print("Unique Evaluated Model for Row:", processed_df['evaluated_model_for_row'].unique())


        # Test specific cases based on user feedback
        print("\n--- Example: DLinear-PatchTST ---")
        example1 = processed_df[processed_df['model_combination'] == 'DLinear-PatchTST']
        print(example1[['dataset', 'horizon', 'model_combination', 'model_type', 'teacher_model', 'student_model_arch', 'training_method', 'metric', 'value']].head())

        print("\n--- Example: PatchTST (standalone) ---")
        example2 = processed_df[processed_df['model_combination'] == 'PatchTST']
        print(example2[['dataset', 'horizon', 'model_combination', 'model_type', 'teacher_model', 'student_model_arch', 'training_method', 'metric', 'value']].head(10))
        
        print("\n--- Example: ETT-small_ETTh1, H192, DLinear-DLinear (as per original data) ---")
        example3 = processed_df[
            (processed_df['dataset'] == 'ETT-small_ETTh1') &
            (processed_df['horizon'] == 192) &
            (processed_df['model_combination'] == 'DLinear-DLinear')
        ]
        print(example3[['dataset', 'horizon', 'model_combination', 'model_type', 'teacher_model', 'student_model_arch', 'training_method', 'metric', 'value']].head())

        # Check for (None, PatchTST) like scenarios
        # These would have model_combination = 'PatchTST' and model_type = Student_*
        print("\n--- Example: (None, PatchTST) like scenario ---")
        example_none_teacher = processed_df[
            (processed_df['teacher_model'] == 'None') &
            (processed_df['student_model_arch'] == 'PatchTST') &
            (processed_df['training_method'].isin(['TaskOnly', 'RDT', 'Follower']))
        ]
        print(example_none_teacher[['dataset', 'horizon', 'model_combination', 'model_type', 'teacher_model', 'student_model_arch', 'training_method', 'metric', 'value']].head())
        
        # Verify all student_model_arch are filled
        if '' in processed_df['student_model_arch'].unique():
            print("\nWARNING: Empty string found in 'student_model_arch'")
            print(processed_df[processed_df['student_model_arch'] == ''][['model_combination', 'model_type', 'teacher_model']].drop_duplicates())
        if '' in processed_df['training_method'].unique():
            print("\nWARNING: Empty string found in 'training_method'")
            print(processed_df[processed_df['training_method'] == ''][['model_combination', 'model_type', 'teacher_model']].drop_duplicates())