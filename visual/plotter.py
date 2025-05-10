import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from visual.data_processor import load_and_process_data

PLOTS_DIR = 'visual/static/images/plots'
os.makedirs(PLOTS_DIR, exist_ok=True)

def generate_comparison_plots(df, metrics_to_plot=['mae', 'mse']):
    if df is None or df.empty:
        print("Dataframe is empty. No plots will be generated.")
        return

    test_df = df[df['split'] == 'test'].copy()
    if test_df.empty:
        print("No 'test' split data found. No plots will be generated.")
        return

    # Key columns for grouping and plotting based on the new data_processor.py
    # We want to compare training methods for each student architecture,
    # under a specific teacher (or 'None' teacher).
    
    # Iterate through unique combinations of dataset, horizon, teacher_model, and student_model_arch
    # Note: student_model_arch can be the same as teacher_model if it's a standalone model being evaluated directly or as a teacher.
    
    # Filter out rows where student_model_arch might be empty if parsing had issues
    test_df = test_df[test_df['student_model_arch'] != '']
    if test_df.empty:
        print("No valid student_model_arch found after filtering. No plots will be generated.")
        return

    # Define the desired order for training methods in plots
    training_method_order = ['Teacher', 'Direct', 'TaskOnly', 'RDT', 'Follower']


    for (dataset, horizon, teacher, student_arch), group_data in test_df.groupby(
            ['dataset', 'horizon', 'teacher_model', 'student_model_arch']):
        
        if group_data.empty:
            continue

        for metric in metrics_to_plot:
            metric_group = group_data[group_data['metric'] == metric].copy()
            if metric_group.empty:
                continue

            # Ensure 'training_method' is categorical with the defined order for consistent plotting
            metric_group['training_method'] = pd.Categorical(
                metric_group['training_method'], 
                categories=training_method_order, 
                ordered=True
            )
            metric_group.sort_values('training_method', inplace=True)


            plt.figure(figsize=(12, 7)) # Adjusted size
            
            sns.barplot(
                data=metric_group,
                x='training_method', 
                y='value',
                # hue='training_method', # Not needed if x is training_method
                palette='viridis',
                order=training_method_order # Ensure consistent order on x-axis
            )
            
            title_teacher_part = f"Teacher: {teacher}" if teacher != 'None' else "No Explicit Teacher"
            plot_title = (f'Comparison on {dataset} (H={horizon})\n'
                          f'{title_teacher_part}, Student Arch: {student_arch} - Metric: {metric.upper()}')
            
            plt.title(plot_title, fontsize=14) # Adjusted font size
            plt.xlabel('Training Method / Model Type', fontsize=12)
            plt.ylabel(metric.upper() + ' Value (Lower is Better)', fontsize=12)
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.yticks(fontsize=10)
            # plt.legend().remove() # Remove legend if hue is not used or redundant
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()

            # Sanitize filename components
            sanitized_dataset = "".join(c if c.isalnum() else "_" for c in dataset)
            sanitized_teacher = "".join(c if c.isalnum() else "_" for c in str(teacher))
            sanitized_student_arch = "".join(c if c.isalnum() else "_" for c in student_arch)

            plot_filename = f"{sanitized_dataset}_H{horizon}_T_{sanitized_teacher}_S_{sanitized_student_arch}_{metric}.png"
            plot_path = os.path.join(PLOTS_DIR, plot_filename)
            
            try:
                plt.savefig(plot_path)
                print(f"Saved plot: {plot_path}")
            except Exception as e:
                print(f"Error saving plot {plot_path}: {e}")
            plt.close()

def generate_all_plots(data_path='results/collected_partial_summary.csv'):
    df = load_and_process_data(data_path)
    if df is not None:
        generate_comparison_plots(df, metrics_to_plot=['mae', 'mse'])
    else:
        print("Failed to load or process data. Plot generation aborted.")

if __name__ == '__main__':
    print(f"Generating plots, saving to: {os.path.abspath(PLOTS_DIR)}")
    generate_all_plots()
    print("Plot generation process finished.")