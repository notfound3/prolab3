
import pandas as pd
import os
from pyvis.network import Network

# Veri setini yükle
data_path = "C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\data\\PROLAB 3 - GÜNCEL DATASET.xlsx"
try:
    df = pd.read_excel(data_path)
    print(f"'{data_path}' başarıyla okundu.")
except FileNotFoundError:
    print(f"'{data_path}' dosyası bulunamadı.")
    exit()
except Exception as e:
    print(f"Bir hata oluştu: {e}")
    exit()

# PyVis ağını oluştur
net = Network(height="750px", width="100%", directed=False, notebook=True)

# Yazarlar ve ilişkiler
nodes = {}
edges = set()

for index, row in df.iterrows():
    orcid = row['orcid']
    author_name = row['author_name']
    coauthors = eval(row['coauthors'])  # List olarak değerlendirilmesi için
    paper_title = row['paper_title']
    doi = row['doi']

    # Düğümleri kontrol ederek ekle
    if orcid not in nodes:
        nodes[orcid] = {
            "name": author_name,
            "papers": []
        }
        net.add_node(orcid, label=author_name, title=f"ORCID: {orcid}")

    # Yazarın makalelerini ekle
    nodes[orcid]["papers"].append(f"{paper_title} (DOI: {doi})")

    # Ortak yazarlık ilişkilerini ekle
    for coauthor in coauthors:
        coauthor_orcid = coauthor if coauthor in nodes else coauthor  # Basit eşleme
        edge = (orcid, coauthor_orcid) if orcid != coauthor_orcid else None
        if edge and edge not in edges:
            edges.add(edge)
            net.add_edge(orcid, coauthor_orcid)

# Düğümlere tıklanabilirlik ekle
for orcid, data in nodes.items():
    papers_html = "<br>".join(data["papers"])
    net.get_node(orcid)["title"] = f"<b>Yazar:</b> {data['name']}<br><b>Makaleler:</b><br>{papers_html}"

# HTML çıktısı oluştur
output_path = "author_collaboration.html"
net.show(output_path)
print(f"Görselleştirme '{output_path}' olarak kaydedildi.")


