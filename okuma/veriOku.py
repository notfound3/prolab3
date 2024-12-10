import pandas as pd

# Excel dosyasını okuma
file_path = "C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\data\\PROLAB 3 - DATASET.xlsx" 
try:
    data = pd.read_excel(file_path)

    print("Veri setinin tamami:")
    print(data)

    
except FileNotFoundError:
    print(f"Dosya bulunamadi: {file_path}")
except Exception as e:
    print(f"Bir hata oluştu: {e}")
