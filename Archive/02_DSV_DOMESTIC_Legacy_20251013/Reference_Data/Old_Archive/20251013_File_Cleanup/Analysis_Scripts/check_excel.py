import pandas as pd

df = pd.read_excel(
    'Data/DSV 202509/SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025.xlsx',
    sheet_name=0, 
    header=None
)

print('Excel Shape:', df.shape)
print('\nFirst 20 rows:\n')

for i in range(min(20, len(df))):
    row_data = df.iloc[i].tolist()
    # 컬럼 값 중 NaN이 아닌 것만 출력
    non_nan = [str(v) for v in row_data if pd.notna(v)]
    if non_nan:
        print(f'{i:2d}: {" | ".join(non_nan[:8])}')  # 처음 8개만

