import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import random


# Dataset

data = pd.read_csv(r"C:\Users\Lenovo\Desktop\benzetim programları\TrafficVolumeData.csv")
traffic_data = data["traffic_volume"].values


#Ayarlar

ROAD_LENGTH = 100
MAX_CARS = 25
LIGHT_POSITION = 60

BASE_GREEN = 40
BASE_RED = 30

SIMULATION_TIME = 150


#Durum

cars = []
time_step = 0

current_light = "green"
light_timer = 0

green_time = BASE_GREEN
red_time = BASE_RED

time_data = []
car_count_data = []
waiting_data = []
density_list = []


#Işık Ayarı(yoğunluğa göre)

def update_light_settings(density):
    global green_time, red_time

    if density > 3000:
        green_time = 60
        red_time = 20
    elif density < 1000:
        green_time = 30
        red_time = 40
    else:
        green_time = BASE_GREEN
        red_time = BASE_RED


#Araç Spawn(arkadan gelir)

def spawn_car(density):
    if len(cars) < MAX_CARS:

        # daha stabil spawn
        spawn_prob = min(0.6, density / 5000)

        if random.random() < spawn_prob:
            # ARKADAN doğar (gerçekçi kuyruk)
            cars.append(-random.randint(5, 25))


#Araç Hareket

def update_cars():
    global cars

    new_positions = []
    waiting = 0

    for car in cars:

        if current_light == "red" and car < LIGHT_POSITION:

            #dur
            new_positions.append(car)
            waiting += 1

        else:
            #ilerle (yavaş gerçekçi hareket)
            new_positions.append(car + 0.7)

    #yoldan çıkanları sil
    cars = [c for c in new_positions if c < ROAD_LENGTH]

    return waiting

# Animasyon

def animate(frame):
    global time_step, current_light, light_timer

    time_step += 1

    density = traffic_data[min(time_step, len(traffic_data)-1)]
    density_list.append(density)

    #ışık ayarı(sadece parametre)
    update_light_settings(density)

    #Timer(stabil ışık sistemi)
    light_timer += 1

    if current_light == "green":
        if light_timer >= green_time:
            current_light = "red"
            light_timer = 0
    else:
        if light_timer >= red_time:
            current_light = "green"
            light_timer = 0

    #araç üret
    spawn_car(density)

    #araç hareket
    waiting = update_cars()

    #kayıt
    time_data.append(time_step)
    car_count_data.append(len(cars))
    waiting_data.append(waiting)

    #çizim
    plt.cla()

    plt.hlines(0, 0, ROAD_LENGTH)

    color = "green" if current_light == "green" else "red"
    plt.scatter(LIGHT_POSITION, 0, c=color, s=250, edgecolors="black")

    plt.scatter(cars, [0]*len(cars), c="grey", s=80)

    plt.xlim(0, ROAD_LENGTH)
    plt.ylim(-1, 1)

    plt.title(f"Trafik | Araç: {len(cars)} | Bekleyen: {waiting} | Yoğunluk: {density}")


#Analiz

def analyze():
    print("\n TRAFİK ANALİZİ")
    print("Max yoğunluk:", max(density_list))
    print("Min yoğunluk:", min(density_list))
    print("Ortalama:", sum(density_list)/len(density_list))


#Grafik

def plot_results():
    plt.figure()

    plt.plot(time_data, car_count_data, label="Araç sayısı")
    plt.plot(time_data, waiting_data, label="Bekleyen")

    plt.axhline(sum(waiting_data)/len(waiting_data), linestyle="--", label="Ortalama")

    plt.legend()
    plt.grid()
    plt.title("Trafik Analizi")
    plt.show()


#Çalıştır

fig = plt.figure()

ani = animation.FuncAnimation(
    fig,
    animate,
    frames=SIMULATION_TIME,
    interval=300,
    blit=False
)

#animasyon bitene kadar burada kalır
plt.show()

#animasyon bitince burası çalışır
plt.close('all')

plot_results()
analyze()

plt.show()