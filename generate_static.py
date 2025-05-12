import os
import pandas as pd
import numpy as np
from flask import Flask, render_template
from visual.data_processor import load_and_process_data
import shutil # Import shutil for copying directories

# Define the style function (copy-pasted from app.py lines 21-65)
def style_metric_specific_top_three(df_group, performance_cols, metric_col_name='metric'):
    """
    Applies CSS styles to the top three (lowest) performance values
    for each metric (mae, mse) within the given DataFrame group.
    Assumes df_group is already filtered for a specific dataset and horizon.
    """

    # Create a DataFrame of styles, initialized to empty strings
    style_df = pd.DataFrame('', index=df_group.index, columns=df_group.columns)

    for metric_value in ['mae', 'mse']: # Iterate for each metric
        metric_rows = df_group[df_group[metric_col_name] == metric_value]
        if metric_rows.empty:
            continue

        # Collect all performance values for the current metric across relevant columns
        all_perf_values_for_metric = []
        for col in performance_cols:
            if col in metric_rows.columns:
                all_perf_values_for_metric.extend(pd.to_numeric(metric_rows[col], errors='coerce').dropna().tolist())

        if not all_perf_values_for_metric:
            continue

        sorted_distinct_values = sorted(list(set(all_perf_values_for_metric)))

        # Define styles for ranks (lowest is best)
        rank_styles_map = {}
        base_style = "color: #198754;" # Green base for all top 3

        if len(sorted_distinct_values) > 0:
            rank_styles_map[sorted_distinct_values[0]] = f"{base_style} font-weight: bold;" # 1st
        if len(sorted_distinct_values) > 1:
            rank_styles_map[sorted_distinct_values[1]] = f"{base_style} text-decoration: underline;" # 2nd
        if len(sorted_distinct_values) > 2:
            rank_styles_map[sorted_distinct_values[2]] = base_style # 3rd (just green)

        # Apply styles to the style_df
        for idx in metric_rows.index:
            for p_col in performance_cols:
                if p_col in metric_rows.columns:
                    cell_value = pd.to_numeric(metric_rows.loc[idx, p_col], errors='coerce')
                    if pd.notna(cell_value) and cell_value in rank_styles_map:
                        style_df.loc[idx, p_col] = rank_styles_map[cell_value]
    return style_df


# Set up a dummy Flask app to use its rendering capabilities
# Specify template_folder relative to this script's location
app = Flask(__name__, template_folder='visual/templates', static_folder='visual/static')

# Define output directory for static site
STATIC_OUTPUT_DIR = 'static_site'
os.makedirs(STATIC_OUTPUT_DIR, exist_ok=True)

# --- Data Loading and Table Generation Logic (from app.py index function) ---
csv_path = 'results/collected_partial_summary.csv' # Path relative to project root
df = load_and_process_data(csv_path)
summary_tables_html = {}
training_method_order = ['Teacher', 'Direct', 'TaskOnly', 'RDT', 'Follower']

if df is not None:
    test_df_for_tables = df[
        (df['split'] == 'test') &
        (df['metric'].isin(['mae', 'mse'])) &
        (df['student_model_arch'] != '') &
        (df['student_model_arch'].notna())
    ].copy()

    if not test_df_for_tables.empty:
        id_vars = ['dataset', 'horizon', 'teacher_model', 'student_model_arch', 'metric']
        value_vars = 'value'
        column_vars = 'training_method'

        required_cols_for_pivot = id_vars + [value_vars, column_vars]
        if all(col in test_df_for_tables.columns for col in required_cols_for_pivot):
            try:
                pivot_table = test_df_for_tables.pivot_table(
                    index=id_vars, columns=column_vars, values=value_vars
                ).reset_index()

                for method in training_method_order:
                    if method not in pivot_table.columns:
                        pivot_table[method] = pd.NA

                if 'RDT' in pivot_table.columns and 'TaskOnly' in pivot_table.columns:
                    pivot_table['RDT_numeric'] = pd.to_numeric(pivot_table['RDT'], errors='coerce')
                    pivot_table['TaskOnly_numeric'] = pd.to_numeric(pivot_table['TaskOnly'], errors='coerce')
                    conditions = [
                        (pivot_table['RDT_numeric'] < pivot_table['TaskOnly_numeric']),
                        (pivot_table['RDT_numeric'] > pivot_table['TaskOnly_numeric']),
                        (pivot_table['RDT_numeric'] == pivot_table['TaskOnly_numeric'])
                    ]
                    choices = ['Better', 'Worse', 'Same']
                    pivot_table['RDT_vs_TaskOnly'] = pd.Series([pd.NA] * len(pivot_table), dtype=object)
                    mask_both_valid = pivot_table['RDT_numeric'].notna() & pivot_table['TaskOnly_numeric'].notna()
                    select_results = np.full(mask_both_valid.sum(), pd.NA, dtype=object)
                    if mask_both_valid.sum() > 0:
                        valid_conditions = [cond[mask_both_valid].to_numpy() for cond in conditions]
                        select_results = np.select(valid_conditions, choices, default=pd.NA)
                    pivot_table.loc[mask_both_valid, 'RDT_vs_TaskOnly'] = select_results
                    pivot_table.drop(columns=['RDT_numeric', 'TaskOnly_numeric'], inplace=True)
                else:
                    pivot_table['RDT_vs_TaskOnly'] = 'N/A'

                display_columns = id_vars + [col for col in training_method_order if col in pivot_table.columns] + ['RDT_vs_TaskOnly']
                pivot_table = pivot_table[display_columns]

                for (dataset_val, horizon_val), group_df in pivot_table.groupby(['dataset', 'horizon']):
                    group_key = f"{dataset_val} (H={horizon_val})"
                    df_to_style = group_df.drop(columns=['dataset', 'horizon']).copy()
                    performance_cols_in_group = [col for col in training_method_order if col in df_to_style.columns]

                    # Use the style function defined above
                    styled_df = df_to_style.style.apply(
                        style_metric_specific_top_three,
                        performance_cols=performance_cols_in_group,
                        metric_col_name='metric',
                        axis=None
                    ).format(
                        {col: "{:.4f}" for col in performance_cols_in_group}, na_rep=''
                    ).set_table_attributes(
                        'class="table table-striped table-hover table-sm table-responsive-sm"'
                    ).hide(axis="index").to_html()
                    summary_tables_html[group_key] = styled_df

            except Exception as e:
                print(f"Error creating pivot table or styling it: {e}")
                summary_tables_html = {"Error": f"<div class='alert alert-danger'>Could not generate summary tables: {e}</div>"}
        else:
             summary_tables_html = {"Info": "<div class='alert alert-info'>No data available for summary tables after filtering.</div>"}
    else:
        summary_tables_html = {"Info": "<div class='alert alert-info'>No 'test' data or no 'mae'/'mse' metrics found for summary.</div>"}
else:
    summary_tables_html = {"Error": "<div class='alert alert-danger'>Failed to load or process data.</div>"}

# --- Render Template and Save ---
# Need to set up app context for render_template to work outside a request
with app.app_context():
    rendered_html = render_template('index.html',
                                    title='Model Performance Analysis',
                                    tables=summary_tables_html)

# Write the rendered HTML to the output directory
output_html_path = os.path.join(STATIC_OUTPUT_DIR, 'index.html')
with open(output_html_path, 'w', encoding='utf-8') as f:
    f.write(rendered_html)

print(f"Generated static index.html at {output_html_path}")

# --- Copy Static Assets ---
# Need to copy visual/static/ contents to static_site/
source_static_dir = 'visual/static'
destination_static_dir = os.path.join(STATIC_OUTPUT_DIR, 'static')

if os.path.exists(source_static_dir):
    # Use copytree to copy the directory and its contents
    shutil.copytree(source_static_dir, destination_static_dir, dirs_exist_ok=True)
    print(f"Copied static assets from {source_static_dir} to {destination_static_dir}")
else:
    print(f"Source static directory not found: {source_static_dir}")

print("Static site generation complete.")