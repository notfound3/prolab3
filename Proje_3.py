from collections import defaultdict
import os
import ast
import pandas as pd
from itertools import combinations
from flask import Flask, render_template, request, jsonify, send_file
from pyvis.network import Network
import math

#####################################
# DOSYA YOLLARI
#####################################
data_path = "C:\\Users\\sezer\\OneDrive\\Desktop\\Proje\\PROLAB 3 - GUNCEL DATASET.xlsx"
template_path = "C:\\Users\\sezer\\OneDrive\\Desktop\\Proje\\templates"

app = Flask(__name__, template_folder=template_path)

#####################################
# Veri Yapıları
#####################################


class Yazar:
    def __init__(self, isim):
        # Hem veri seti tarafında hem de user input tarafında
        # tutarlı olması için normalize ediyoruz:
        self.isim = isim.strip().lower()
        self.makaleler = []


class Makale:
    def __init__(self, baslik, yazarlar):
        self.baslik = baslik
        self.yazarlar = yazarlar


class BSTNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


class Graf:
    def __init__(self):
        self.dugumler = {}  # isim -> Yazar nesnesi
        self.kenarlar = []  # (yazar_isim1, yazar_isim2)
        self.weights = {}  # ((yazar1,yazar2) sorted tuple) -> ortak makale sayısı
        self.adj_list = {}  # isim -> [(komsu, weight), ...]

    def dugum_ekle(self, yazar):
        if yazar.isim not in self.dugumler:
            self.dugumler[yazar.isim] = yazar

    def kenar_ekle(self, yazar1, yazar2, weight=1):
        # Kenar eklerken isimleri sorted tuple olarak kontrol edelim
        e1 = (yazar1.isim, yazar2.isim)
        e2 = (yazar2.isim, yazar1.isim)
        if e1 not in self.kenarlar and e2 not in self.kenarlar:
            self.kenarlar.append(e1)
            key = tuple(sorted([yazar1.isim, yazar2.isim]))
            self.weights[key] = weight

    def build_adj_list(self):
        # Adjacency list'i oluştur
        for yazar in self.dugumler:
            self.adj_list[yazar] = []
        for u, v in self.kenarlar:
            w = self.get_edge_weight(u, v)
            self.adj_list[u].append((v, w))
            self.adj_list[v].append((u, w))

    def get_edge_weight(self, y1, y2):
        key = tuple(sorted([y1, y2]))
        return self.weights.get(key, 1)

    def dijkstra(self, start):
        dist = {node: math.inf for node in self.adj_list}
        dist[start] = 0
        visited = set()
        while len(visited) < len(self.adj_list):
            current = None
            current_dist = math.inf
            for node in self.adj_list:
                if node not in visited and dist[node] < current_dist:
                    current = node
                    current_dist = dist[node]
            if current is None or current_dist == math.inf:
             break
            visited.add(current)
            for komsu, w in self.adj_list[current]:
                if dist[current] + w < dist[komsu]:
                    dist[komsu] = dist[current] + w
        return dist

    def shortest_path(self, start, end):
        # Basit Dijkstra tabanlı "en kısa yol" hesaplama
        dist = {node: math.inf for node in self.adj_list}
        prev = {node: None for node in self.adj_list}
        dist[start] = 0
        visited = set()

        while len(visited) < len(self.adj_list):
            current = None
            current_dist = math.inf
            for node in dist:
                if node not in visited and dist[node] < current_dist:
                    current = node
                    current_dist = dist[node]
            if current is None:
                break
            visited.add(current)
            for komsu, w in self.adj_list[current]:
                if dist[current] + w < dist[komsu]:
                    dist[komsu] = dist[current] + w
                    prev[komsu] = current

        if dist[end] == math.inf:
            return None, math.inf

        path = []
        temp = end
        while temp is not None:
            path.append(temp)
            temp = prev[temp]
        path.reverse()
        return path, dist[end]

    def get_neighbors(self, node):
        return [n for (n, _) in self.adj_list.get(node, [])]


#####################################
# Yardımcı Fonksiyonlar
#####################################


def insert_bst(root, key):
    if root is None:
        return BSTNode(key)
    if key < root.key:
        root.left = insert_bst(root.left, key)
    elif key > root.key:
        root.right = insert_bst(root.right, key)
    return root


def delete_bst(root, key):
    if root is None:
        return root
    if key < root.key:
        root.left = delete_bst(root.left, key)
    elif key > root.key:
        root.right = delete_bst(root.right, key)
    else:
        if root.left is None:
            return root.right
        elif root.right is None:
            return root.left
        succ = min_value_node(root.right)
        root.key = succ.key
        root.right = delete_bst(root.right, succ.key)
    return root


def min_value_node(node):
    current = node
    while current.left is not None:
        current = current.left
    return current


def inorder_bst(root, res):
    if root is not None:
        inorder_bst(root.left, res)
        res.append(root.key)
        inorder_bst(root.right, res)


def build_queue_from_neighbors(graf, author):
    # A yazarının komşuları (işbirliği yaptığı yazarlar)
    neighbors = graf.get_neighbors(author)
    # Sıralayacağımız array: (yazar_isim, makale_sayısı)
    arr = []
    for n in neighbors:
        arr.append((n, len(graf.dugumler[n].makaleler)))
    # Bubble sort (makale sayısına göre artan)
    for i in range(len(arr)):
        for j in range(0, len(arr) - i - 1):
            if arr[j][1] > arr[j + 1][1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def build_bst_from_queue(q):
    root = None
    for item in q:
        # item[0] yazar_isim (hepsi lower-case)
        key = item[0]
        root = insert_bst(root, key)
    return root


def count_collaborators(graf, author):
    return len(graf.get_neighbors(author))


def find_most_collaborative_author(graf):
    max_degree = -1
    max_author = None
    for a in graf.adj_list:
        deg = len(graf.adj_list[a])
        if deg > max_degree:
            max_degree = deg
            max_author = a
    return max_author, max_degree


def longest_path_from_author(graf, start):
    visited = set()
    best_path = []

    def dfs(current, path):
        nonlocal best_path
        visited.add(current)
        for n, w in graf.adj_list[current]:
            if n not in visited:
                dfs(n, path + [n])
        if len(path) > len(best_path):
            best_path = path
        visited.remove(current)

    dfs(start, [start])
    return best_path


#####################################
# Veriyi Okuma ve Graf Oluşturma
#####################################

try:
    df = pd.read_excel(data_path)
    print(f"'{data_path}' başarıyla okundu.")
except FileNotFoundError:
    print(f"'{data_path}' dosyası bulunamadı.")
    exit()
except Exception as e:
    print(f"Bir hata oluştu: {e}")
    exit()

required_columns = {'paper_title', 'author_name', 'coauthors'}
missing = required_columns - set(df.columns)
if missing:
    print(f"Gerekli sütunlar eksik: {missing}")
    exit()

df.dropna(subset=['paper_title', 'author_name', 'coauthors'], inplace=True)

graf = Graf()

for _, row in df.iterrows():
    # Makale başlığını normal alıyoruz, yazar adını normalize:
    makale_baslik = str(row['paper_title']).strip()
    author_name = str(row['author_name']).strip().lower()

    try:
        coauthors_raw = ast.literal_eval(row['coauthors'])
        # coauthors_raw liste olsun
        coauthors = []
        for c in coauthors_raw:
            coauthors.append(c.strip().lower())
    except:
        continue

    yazarlar_isim = [author_name] + coauthors
    makale_yazarlari = []

    # Her isme karşılık Yazar nesnesi oluştur
    for yazar_adi in yazarlar_isim:
        if yazar_adi not in graf.dugumler:
            yazar_nesne = Yazar(yazar_adi)
            graf.dugum_ekle(yazar_nesne)
        makale_yazarlari.append(graf.dugumler[yazar_adi])

    # Makale nesnesi oluştur
    makale = Makale(makale_baslik, makale_yazarlari)

    # Yazarın makaleler listesine ekle
    for y in makale_yazarlari:
        y.makaleler.append(makale_baslik)

    # Kenarları ve ağırlıkları güncelle
    for y1, y2 in combinations(makale_yazarlari, 2):
        graf.kenar_ekle(y1, y2)
        key = tuple(sorted([y1.isim, y2.isim]))
        graf.weights[key] = graf.weights.get(key, 0) + 1

graf.build_adj_list()

#####################################
# Graf Görselleştirme
#####################################


def create_graph_html(df, highlight_nodes=None):
    if highlight_nodes is None:
        highlight_nodes = []    

    # PyVis ağı oluştur
    net = Network(height="750px", width="100%", directed=False, notebook=True)

    nodes = {}
    edges = defaultdict(int)
    author_paper_count = defaultdict(int)  # Yazar başına makale sayısını tutacağız

    for index, row in df.iterrows():
        orcid = row['orcid']
        author_name = row['author_name']
        coauthors = eval(row['coauthors'])  # List olarak değerlendirilmesi için
        paper_title = row['paper_title']
        doi = row['doi']

        # Yazarın makale sayısını güncelle
        author_paper_count[orcid] += 1

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
            # Ortak yazar düğümünü kontrol et ve ekle
            if coauthor not in nodes:
                nodes[coauthor] = {
                    "name": coauthor,
                    "papers": []
                }
                net.add_node(coauthor, label=coauthor, title=f"Yazar: {coauthor}")

            # Kenar ekle ve ağırlığını artır
            edge = (orcid, coauthor)
            edges[edge] += 1

    # Kenarları ekle
    for (orcid, coauthor), weight in edges.items():
        net.add_edge(orcid, coauthor, value=weight)  # Ağırlığı "value" parametresiyle belirtiyoruz

    # Düğüm boyutlarını ve renklerini belirle
    average_paper_count = sum(author_paper_count.values()) / len(author_paper_count)

    # İşlem sırasına göre düğümleri vurgulamak için renk güncelleme
    highlighted_nodes = []

    for orcid, data in nodes.items():
        papers_html = "<br>".join(data["papers"])
        orcid_link = f"https://orcid.org/{orcid}"  # ORCID bağlantısı
        net.get_node(orcid)["title"] = f"<b>Yazar:</b> {data['name']}<br><b>Makaleler:</b><br>{papers_html}"

        # Makale sayısına göre boyut ve renk belirle
        paper_count = author_paper_count[orcid]
        if paper_count > average_paper_count * 1.2:
            size = 20  # Büyük düğüm
            color = 'purple'  # Koyu renk
        elif paper_count < average_paper_count * 0.8:
            size = 10  # Küçük düğüm
            color = 'pink'  # Açık renk
        else:
            size = 15  # Ortalama boyut
            color = 'gray'  # Orta renk

        # İşlem sırasına göre düğümleri vurgulamak için renk güncelleme
        highlighted_nodes.append(orcid)  # Tıklama sırasında bu düğüm vurgulanacak

        # Düğüm özelliklerini güncelle
        net.get_node(orcid)["size"] = size
        net.get_node(orcid)["color"] = color

     
    temp_path = os.path.join(template_path, 'graph.html')
    html_content = net.generate_html()
    with open(temp_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(html_content)

 # Toplam düğüm sayısını yazdır
    print(f"Toplam düğüm sayısı: {len(net.nodes)}")

    # Sadece ORCID'lerden gelen düğüm sayısını hesapla
    orcid_node_count = sum(1 for node in net.nodes if '-' in node['id'] and len(node['id']) == 19)
    print(f"Sadece ORCID'lerden gelen düğüm sayısı: {orcid_node_count}")

    # Kenar sayısını yazdır
    print(f"Kenar sayısı: {len(net.edges)}")


#####################################
# Global Değişkenler
#####################################
global_queue = None

#####################################
# Flask Routes
#####################################

@app.route('/graph')
def graph():
    create_graph_html(df)
    return send_file('templates/graph.html')


@app.route('/')
def index():
    create_graph_html(df)
    return render_template('index.html', output_text="Hoşgeldiniz. Solda çıktılar, sağda isterler, ortada graf.")


@app.route('/run_ister', methods=['POST'])
def run_ister():
    ister_no = request.form.get('ister_no')
    if ister_no == '1':
        msg = '1. İster seçildi. Lütfen A ve B yazar ID\'lerini virgülle ayırarak girin (örn: "yazar1,yazar2").'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '2':
        msg = '2. İster seçildi. Lütfen A yazarının ID\'sini girin.'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '3':
        msg = '3. İster seçildi. (Önce 2. isterde oluşturulan kuyruk). Lütfen BST\'den silmek istediğiniz Yazar ID\'sini girin.'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '4':
        msg = '4. İster seçildi. Lütfen A yazarının ID\'sini girin.'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '5':
        msg = '5. İster seçildi. Lütfen A yazarının ID\'sini girin.'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '6':
        msg = '6. İster seçildi. En çok işbirliği yapan yazar belirlenecek. ID girmeye gerek yok.'
        return jsonify({'status':'ok','message':msg})
    elif ister_no == '7':
        msg = '7. İster seçildi. Lütfen başlangıç yazar ID\'sini girin.'
        return jsonify({'status':'ok','message':msg})
    else:
        return jsonify({'status':'error','message':'Geçersiz ister numarası.'})


@app.route('/submit_id', methods=['POST'])
def submit_id():
    global global_queue
    ister_no = request.form.get('ister_no')
    yazar_idler = request.form.get('yazar_idler')
    output_lines = []

    # Kullanıcı girişini normalize (lower + strip)
    # Eğer iki yazar birden istenecekse virgülle ayrılmış
    # her birini teker teker normalize edelim.
    # Ör: " B. Rajakumar " -> "b. rajakumar"
    if yazar_idler:
        yazar_idler = yazar_idler.strip().lower()
        

    if ister_no == '1':
        ids = [x.strip() for x in yazar_idler.split(',')]
        print("Girilen ID'ler:", ids)  # DEBUG: Kullanıcı girişini kontrol edin
     
        if len(ids) != 2:
           return jsonify({'status': 'error', 'message': 'Lütfen A,B formatında girin.'})
    
        A, B = ids[0], ids[1]
        print(f"Kontrol edilen ID'ler: A={A}, B={B}")  # DEBUG: Kontrol edin

        if A not in graf.dugumler or B not in graf.dugumler:
           print("Graf düğümleri:", graf.dugumler)  # DEBUG: Mevcut düğümleri yazdırın
           msg = "Girilen yazarlar grafta bulunamadı."
           output_lines.append(msg)
           output_lines.append("1. İster seçildi. Lütfen A ve B ID'lerini virgülle ayırarak girin (Örneğin: \"YazarA,YazarB\").")
           return jsonify({'status': 'ok', 'message': '<br>'.join(output_lines)})

        path, dist = graf.shortest_path(A, B)
        if path is None:
           msg = f"{A} ile {B} arasında yol yok."
           output_lines.append(msg)
           create_graph_html()
           return jsonify({'status': 'ok', 'message': '<br>'.join(output_lines)})
        else:
           msg = f"{A} ile {B} arasındaki en kısa yol: {' -> '.join(path)}, Mesafe: {dist}"
           output_lines.append(msg)
           # Yolun grafiksel gösterimi = highlight_nodes=path
           create_graph_html(highlight_nodes=path)
           return jsonify({'status': 'ok', 'message': '<br>'.join(output_lines)})


    elif ister_no == '2':
        A = yazar_idler
        if not A or A not in graf.dugumler:
            return jsonify({'status':'error','message':'Yazar grafta yok.'})

        # Kuyruk oluşturuyoruz
        output_lines.append("2. İster: Kuyruk Oluşturma...")
        output_lines.append("Kuyruk (A yazarının komşuları, makale sayısına göre artan):")

        q = build_queue_from_neighbors(graf, A)
        global_queue = q

        # Adım adım ekleme
        for item in q:
            output_lines.append(f"Eklendi -> {item[0]}, Makale sayısı: {item[1]}")

        create_graph_html(highlight_nodes=[A]+[x[0] for x in q])
        return jsonify({'status':'ok','message':'<br>'.join(output_lines)})

    elif ister_no == '3':
        to_delete = yazar_idler
        if global_queue is None:
            return jsonify({'status':'error','message':'Önce 2. ister çalışmalı (kuyruk).'})

        output_lines.append("3. İster: BST oluşturma ve silme işlemi.")
        root = build_bst_from_queue(global_queue)
        root = delete_bst(root, to_delete)

        res = []
        inorder_bst(root, res)
        output_lines.append("BST içinde inorder sıralama (silme sonrası):")
        output_lines.append(", ".join(res))
        create_graph_html()
        return jsonify({'status':'ok','message':'<br>'.join(output_lines)})

    elif ister_no == '4':
        A = yazar_idler
        if not A or A not in graf.dugumler:
            return jsonify({'status':'error','message':'Yazar grafta yok.'})

        # Altgraf = A + komşuları + komşuların komşuları
        neighbors = set(graf.get_neighbors(A))
        second_neighbors = set()
        for n in neighbors:
            second_neighbors.update(graf.get_neighbors(n))
        sub_nodes = set([A]) | neighbors | second_neighbors

        dist = graf.dijkstra(A)
        output_lines.append(f"{A} yazarı altgraf düğümleri ve en kısa mesafeler:")
        for node in sub_nodes:
            d = dist[node]
            if d == math.inf:
                d = "Ulaşılmaz"
            output_lines.append(f"{A} -> {node}: {d}")

        create_graph_html(highlight_nodes=list(sub_nodes))
        return jsonify({'status':'ok','message':'<br>'.join(output_lines)})

    elif ister_no == '5':
        A = yazar_idler
        if not A or A not in graf.dugumler:
            return jsonify({'status':'error','message':'Yazar grafta yok.'})
        c = count_collaborators(graf, A)
        msg = f"{A} yazarının işbirliği yaptığı yazar sayısı: {c}"
        create_graph_html(highlight_nodes=[A]+graf.get_neighbors(A))
        return jsonify({'status':'ok','message':msg})

    elif ister_no == '6':
        a, deg = find_most_collaborative_author(graf)
        msg = f"En çok işbirliği yapan yazar: {a}, işbirliği sayısı: {deg}"
        create_graph_html(highlight_nodes=[a])
        return jsonify({'status':'ok','message':msg})

    elif ister_no == '7':
        A = yazar_idler
        if not A or A not in graf.dugumler:
            return jsonify({'status':'error','message':'Yazar grafta yok.'})
        path = longest_path_from_author(graf, A)
        msg = f"{A} yazarından başlayarak bulunabilen en uzun yol: {' -> '.join(path)} (Uzunluk: {len(path)})"
        create_graph_html(highlight_nodes=path)
        return jsonify({'status':'ok','message':msg})

    else:
        return jsonify({'status':'error','message':'Geçersiz ister.'})

if __name__ == '__main__':
    app.run(debug=True)
