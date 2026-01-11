import pandas as pd

df = pd.read_csv('backend/data/processed/mpi_scores_latest.csv')

print('\n' + '='*60)
print('MPI CALCULATION SUMMARY - IMPROVED MODEL')
print('='*60)
print(f'Total wards analyzed: {len(df)}')

print(f'\nRisk Distribution:')
risk_counts = df['risk_level'].value_counts()
for level in ['Low', 'Moderate', 'High', 'Critical']:
    count = risk_counts.get(level, 0)
    pct = (count / len(df)) * 100
    print(f'  {level:10s}: {count:3d} wards ({pct:5.1f}%)')

print(f'\nMPI Statistics:')
print(f'  Mean MPI: {df["mpi_score"].mean():.1f}')
print(f'  Min MPI:  {df["mpi_score"].min():.1f}')
print(f'  Max MPI:  {df["mpi_score"].max():.1f}')

print(f'\n{"="*60}')
print('TOP 10 HIGH-RISK WARDS')
print('='*60)
top10 = df.nlargest(10, 'mpi_score')
for idx, row in top10.iterrows():
    print(f"\n{row['ward_id']:6s} - MPI: {row['mpi_score']:.1f} ({row['risk_level']})")
    print(f"   Model Prob: {row['model_prob']*100:.1f}%")
    print(f"   History: {row['hist_flood_count']:.0f} floods")
    print(f"   Drain: {row['drain_density']:.2f} pts/km²")
