import matplotlib.pyplot as plt

x = [1, 2, 3, 4, 5]
y = [10, 20, 25, 30, 35]

plt.plot(x, y, label='Örnek Veri')
plt.xlabel('X Ekseni')
plt.ylabel('Y Ekseni')
plt.title('Matplotlib ile İlk Grafik')
plt.legend()
plt.show()
