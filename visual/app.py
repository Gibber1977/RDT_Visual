from flask import Flask, render_template, url_for
import os
import pandas as pd
import numpy as np
from visual.data_processor import load_and_process_data
from visual.plotter import PLOTS_DIR

app = Flask(__name__, template_folder='templates', static_folder='static')
os.makedirs(PLOTS_DIR, exist_ok=True)

def get_plot_files():
    if not os.path.isdir(PLOTS_DIR):
        return []
    plot_files = [f for f in os.listdir(PLOTS_DIR) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    plot_files.sort()
    return plot_files

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


@app.route('/')
def index():
    csv_path = 'results/collected_partial_summary.csv'
    df = load_and_process_data(csv_path)
    summary_tables_html = {}
    training_method_order = ['Teacher', 'Direct', 'TaskOnly', 'RDT', 'Follower']

    if df is not None:
        test_df = df[(df['split'] == 'test') & (df['metric'].isin(['mae', 'mse']))].copy()
        if not test_df.empty:
            test_df = test_df[test_df['student_model_arch'] != '']

            if not test_df.empty:
                id_vars = ['dataset', 'horizon', 'teacher_model', 'student_model_arch', 'metric']
                value_vars = 'value'
                column_vars = 'training_method'
                
                required_cols_for_pivot = id_vars + [value_vars, column_vars]
                if not all(col in test_df.columns for col in required_cols_for_pivot):
                    summary_tables_html = {"Error": "<div class='alert alert-danger'>Could not generate summary tables due to missing columns for pivot.</div>"}
                else:
                    try:
                        pivot_table = test_df.pivot_table(
                            index=id_vars, columns=column_vars, values=value_vars
                        ).reset_index()

                        for method in training_method_order:
                            if method not in pivot_table.columns:
                                pivot_table[method] = pd.NA
                        
                        # Ensure RDT_vs_TaskOnly column exists before trying to use it in display_columns
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

                        # Define display columns, including the RDT_vs_TaskOnly
                        display_columns = id_vars + [col for col in training_method_order if col in pivot_table.columns] + ['RDT_vs_TaskOnly']
                        pivot_table = pivot_table[display_columns]


                        for (dataset_val, horizon_val), group_df in pivot_table.groupby(['dataset', 'horizon']):
                            group_key = f"{dataset_val} (H={horizon_val})"
                            
                            df_to_style = group_df.drop(columns=['dataset', 'horizon']).copy()
                            performance_cols_in_group = [col for col in training_method_order if col in df_to_style.columns]
                            
                            # Apply new styling function
                            styled_df = df_to_style.style.apply(
                                style_metric_specific_top_three,
                                performance_cols=performance_cols_in_group,
                                metric_col_name='metric', # Pass the name of the metric column
                                axis=None # Apply to the entire DataFrame slice
                            ).format(
                                {col: "{:.4f}" for col in performance_cols_in_group}, na_rep='N/A'
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

    plot_image_files = get_plot_files()
    if not plot_image_files and df is not None:
        print("No plots found. Attempting to generate them...")
        from visual.plotter import generate_all_plots
        generate_all_plots(csv_path)
        plot_image_files = get_plot_files()

    return render_template('index.html',
                           title='Model Performance Analysis (Refined Highlighting)',
                           tables=summary_tables_html,
                           plot_files=plot_image_files,
                           plots_dir_name=os.path.basename(PLOTS_DIR))

if __name__ == '__main__':
    print("Visualisation server starting...")
    print(f"Ensure Python packages are installed: pip install flask pandas matplotlib seaborn numpy")
    print(f"To pre-generate plots, run: python -m visual.plotter")
    print(f"Then run the Flask app: python -m visual.app")
    app.run(debug=True, port=5001)