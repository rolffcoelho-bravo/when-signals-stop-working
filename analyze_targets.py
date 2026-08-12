import pandas as pd, glob, json

dfs = [pd.read_csv(f) for f in glob.glob('outputs/v3/development_execution_results/*.csv')]
df = pd.concat(dfs, ignore_index=True)
df = df[df['status'] == 'SUCCESS']
plan = pd.read_csv('outputs/v3/forecast_foundation/nested_fold_plan.csv')
merged = df.merge(plan, on='job_id')
print(merged.groupby('target_name')[['log_loss', 'brier_score', 'mse']].mean())
