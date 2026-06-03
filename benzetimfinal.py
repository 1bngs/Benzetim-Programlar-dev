import streamlit as st
import matplotlib.pyplot as plt
import random
import time
import pandas as pd


# PAGE CONFIG

st.set_page_config(
    page_title="AI Smart Traffic",
    layout="wide"
)

st.title("🚦 AI-Powered Smart City Traffic Simulation")


# SESSION STATE INITIALIZATION

defaults = {
    "running": False,
    "vehicles": [],
    "light": "green",
    "timer": 0,
    "step": 0,
    "history": [],
    "wait_history": [],
    "pedestrian_mode": False,
    "pedestrian_timer": 0,
    "pedestrians": [],
    "passed": 0,
    "total_wait": 0,
    "ai_decision": "Normal Akış",
    "pedestrian_requested": False  
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# BUTTON CALLBACK FUNCTIONS

def start_sim():
    st.session_state.running = True

def stop_sim():
    st.session_state.running = False

def trigger_pedestrian():
    st.session_state.pedestrian_requested = True

def spawn_emergency_ambulance():
    lane = random.choice([0, 1])
    initial_y = 0.4 if lane == 0 else -0.4 
    st.session_state.vehicles.append({
        "x": 0.0, "lane": lane, "current_y": initial_y, "speed": 2.5, "base_speed": 2.5, "wait": 0,
        "type": "ambulance", "emoji": "🚑", "color": "white"
    })

def spawn_emergency_firetruck():
    lane = random.choice([0, 1])
    initial_y = 0.4 if lane == 0 else -0.4 
    st.session_state.vehicles.append({
        "x": 0.0, "lane": lane, "current_y": initial_y, "speed": 2.2, "base_speed": 2.2, "wait": 0,
        "type": "firetruck", "emoji": "🚒", "color": "red"
    })


# SIDEBAR

ROAD_LENGTH = st.sidebar.slider("Yol Uzunluğu", 80, 250, 140)
MAX_CARS = st.sidebar.slider("Maksimum Araç", 10, 100, 45)
SIM_SPEED = st.sidebar.slider("Simülasyon Hızı (Saniye)", 0.01, 0.5, 0.02)

col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
with col_btn1: st.button("▶️ Başlat", on_click=start_sim)
with col_btn2: st.button("⛔ Durdur", on_click=stop_sim)
with col_btn3:
    if st.button("🔄 Sıfırla"):
        st.session_state.running = False
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.sidebar.button("🚑 Ambulans Çağır", on_click=spawn_emergency_ambulance)
st.sidebar.button("🚒 İtfaiye Çağır", on_click=spawn_emergency_firetruck)
st.sidebar.button("🚶 Yaya Butonu", on_click=trigger_pedestrian)

# CONSTANTS & CONFIG

LIGHT_POS = ROAD_LENGTH // 2
LANES = [0.4, -0.4]  
SAFE_DISTANCE = 6.0  # Takip mesafesi akış için hafifçe optimize edildi
ANIMATION_SPEED = 0.20 # Şerit değiştirme görsel hızı artırıldı

VEHICLE_TYPES = [
    {"type": "car", "emoji": "🚗", "color": "blue", "min_speed": 0.8, "max_speed": 1.4, "weight": 80},
    {"type": "ambulance", "emoji": "🚑", "color": "white", "min_speed": 2.5, "max_speed": 2.8, "weight": 4},
    {"type": "police", "emoji": "🚓", "color": "black", "min_speed": 1.6, "max_speed": 2.0, "weight": 6},
    {"type": "firetruck", "emoji": "🚒", "color": "red", "min_speed": 2.2, "max_speed": 2.5, "weight": 4}
]


# 🧠 DYNAMIC AI TRAFFIC LIGHT ALGORITHM

def update_light_ai():
    has_critical = any([v["type"] in ["ambulance", "firetruck"] for v in st.session_state.vehicles])
    priority_emergency = any([
        v["type"] in ["ambulance", "firetruck"] and 0 < LIGHT_POS - v["x"] < 60 
        for v in st.session_state.vehicles
    ])
    
    if priority_emergency:
        st.session_state.pedestrian_mode = False
        st.session_state.pedestrians = []
        
        if st.session_state.light != "green":
            st.session_state.light = "green"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🚨🚨 ACİL DURUM ÖNCELİĞİ: Yaya Geçidi Kilitlendi, Işık Yeşile Çevrildi!"
        else:
            st.session_state.ai_decision = "🚨🚨 ACİL DURUM ÖNCELİĞİ: Geçiş koridoru açık tutuluyor."
        return

    if st.session_state.pedestrian_requested and not has_critical:
        st.session_state.pedestrian_mode = True
        st.session_state.pedestrian_requested = False  
        st.session_state.pedestrian_timer = 0

    if st.session_state.pedestrian_mode:
        st.session_state.light = "red"
        st.session_state.pedestrian_timer += 1
        st.session_state.ai_decision = f"🚶 Yaya Geçişi Aktif ({20 - st.session_state.pedestrian_timer}sn kaldı)"
        if st.session_state.pedestrian_timer > 20:
            st.session_state.pedestrian_mode = False
            st.session_state.light = "green"
            st.session_state.pedestrian_timer = 0
        return

    police_near = any([v["type"] == "police" and 0 < LIGHT_POS - v["x"] < 35 for v in st.session_state.vehicles])
    if police_near:
        if st.session_state.light != "green":
            st.session_state.light = "green"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🚓 POLİS ÖNCELİĞİ: Işık Yeşile Çevrildi."
        return

    st.session_state.timer += 1
    waiting_vehicles = [v for v in st.session_state.vehicles if LIGHT_POS - 20 <= v["x"] <= LIGHT_POS]
    queue_count = len(waiting_vehicles)
    total_queue_wait = sum([v["wait"] for v in waiting_vehicles])

    base_green_time = 15
    dynamic_green_bonus = min(20, queue_count * 2) 
    max_green_allowed = base_green_time + dynamic_green_bonus

    if st.session_state.light == "green":
        if st.session_state.timer > max_green_allowed:
            st.session_state.light = "yellow"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🟡 Trafik Azaldı, Sarı Işığa Geçiliyor."
        else:
            st.session_state.ai_decision = f"🟢 Akıllı Yeşil Işık (Süre optimize ediliyor: {max_green_allowed}sn)"

    elif st.session_state.light == "yellow":
        if st.session_state.timer > 3:
            st.session_state.light = "red"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🔴 Kırmızı Işık Dönemi Başladı."

    elif st.session_state.light == "red":
        if total_queue_wait > 80 or queue_count > 6:
            st.session_state.light = "green"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🧠 AI KARARI: Aşırı Yoğunluk Tespit Edildi, Kırmızı Erken Bitirildi!"
        elif st.session_state.timer > 20:
            st.session_state.light = "green"
            st.session_state.timer = 0
            st.session_state.ai_decision = "🟢 Normal Döngü: Yeşil Işığa Geçildi."
        else:
            st.session_state.ai_decision = f"🔴 Kırmızı Işık Bekleniyor (AI optimize ediyor, Kuyruk Gecikmesi: {total_queue_wait})"


# SPAWN - ANIMATION UPDATES

def update_pedestrians():
    has_critical = any([v["type"] in ["ambulance", "firetruck"] for v in st.session_state.vehicles])
    if has_critical:
        st.session_state.pedestrian_mode = False
        st.session_state.pedestrians = []
        return

    if st.session_state.pedestrian_mode and len(st.session_state.pedestrians) == 0:
        for _ in range(5):
            st.session_state.pedestrians.append({
                "x": LIGHT_POS + random.uniform(-1.5, 1.5), "y": -0.9
            })
    for p in st.session_state.pedestrians: p["y"] += 0.08
    
    st.session_state.pedestrians = [p for p in st.session_state.pedestrians if p["y"] < 1.0]

def spawn_vehicle():
    if len(st.session_state.vehicles) >= MAX_CARS: return
    if random.random() < 0.35:
        selected = random.choices(VEHICLE_TYPES, weights=[v["weight"] for v in VEHICLE_TYPES])[0]
        lane = random.choice([0, 1])
        blocked = any([v["lane"] == lane and v["x"] < 14 for v in st.session_state.vehicles])
        if not blocked:
            speed = random.uniform(selected["min_speed"], selected["max_speed"])
            st.session_state.vehicles.append({
                "x": 0.0, "lane": lane, "current_y": LANES[lane], "speed": speed, "base_speed": speed,
                "wait": 0, "type": selected["type"], "emoji": selected["emoji"], "color": selected["color"]
            })

def move_vehicles():
    vehicles = sorted(st.session_state.vehicles, key=lambda v: v["x"], reverse=True)
    has_critical = any([v["type"] in ["ambulance", "firetruck"] for v in vehicles])

    for vehicle in vehicles:
        x = vehicle["x"]
        lane = vehicle["lane"]
        is_priority = (vehicle["type"] in ["ambulance", "firetruck"])
        is_police = (vehicle["type"] == "police")
        can_move = True
        
        current_speed = vehicle["base_speed"]

        # Görsel şerit geçiş yumuşatma motoru
        target_y = LANES[vehicle["lane"]]
        if vehicle["current_y"] < target_y: vehicle["current_y"] = min(target_y, vehicle["current_y"] + ANIMATION_SPEED)
        elif vehicle["current_y"] > target_y: vehicle["current_y"] = max(target_y, vehicle["current_y"] - ANIMATION_SPEED)

        # ⚡ GELİŞTİRİLMİŞ YAN ŞERİT KONTROLLÜ FERMUAR MOTORU
        if has_critical and not is_priority:
            for e in vehicles:
                # Eğer arkadan bir acil durum aracı yaklaşıyorsa (Menzil: 35 birim)
                if e["type"] in ["ambulance", "firetruck"] and 0 < x - e["x"] < 35:
                    # 1. Öncelik: Hızlanarak alanı genişlet
                    current_speed = vehicle["base_speed"] * 1.50
                    
                    # 2. Öncelik: Eğer ambulansla aynı şeritteyse "YAN ŞERİT MÜSAİTLİK" kontrolü yap
                    if e["lane"] == lane:
                        other_lane = 1 - lane
                        
                        # Yan şeridin bu aracın hizasında (önünde veya arkasında araç var mı?) müsait olup olmadığını kontrol et
                        # Mesafe filtresi daha esnek (4.5) yapılarak yoğun trafikte bile geçiş alanı tanındı.
                        lane_is_free = not any([
                            check["lane"] == other_lane and abs(check["x"] - x) < 4.5 
                            for check in vehicles
                        ])
                        
                        # Yan şerit müsait olduğu an tereddüt etmeden şeridini değiştirir!
                        if lane_is_free:
                            vehicle["lane"] = other_lane

        # Kırmızı Işık Kuralları 
        if not is_priority and not is_police and st.session_state.light == "red" and (LIGHT_POS - 4 <= x <= LIGHT_POS):
            is_pushed = any([e["type"] in ["ambulance", "firetruck"] and 0 < x - e["x"] < 30 for e in vehicles])
            if not is_pushed:
                can_move = False

        # Yaya Geçidi Kuralları
        if st.session_state.pedestrian_mode and (LIGHT_POS - 5 <= x <= LIGHT_POS + 1):
            if not is_priority:
                can_move = False

        # 🛑 Çarpışma Filtresi
        for other in vehicles:
            if other == vehicle: continue
            if other["lane"] == vehicle["lane"]:
                distance = other["x"] - x
                
                if 0 < distance <= SAFE_DISTANCE:
                    if is_priority:
                        current_speed = min(vehicle["base_speed"], other["speed"] * 0.95)
                        if distance <= 3.5: 
                            current_speed = max(0.1, other["speed"] * 0.5)
                    else:
                        # Normal sürüş esnasında önü tıkanan aracın sollama şerit kontrolü
                        other_lane = 1 - lane
                        if not any([test["lane"] == other_lane and abs(test["x"] - x) < 6 for test in vehicles]):
                            vehicle["lane"] = other_lane
                        else:
                            can_move = False

        if can_move: 
            vehicle["speed"] = current_speed
            vehicle["x"] += float(current_speed)
        else:
            vehicle["speed"] = 0
            vehicle["wait"] += 1
            st.session_state.total_wait += 1

    st.session_state.passed += len([v for v in vehicles if v["x"] >= ROAD_LENGTH])
    st.session_state.vehicles = [v for v in vehicles if v["x"] < ROAD_LENGTH]


# LAYOUT & INTERFACE PLACEHOLDERS

ai_text_slot = st.empty()
warning = st.empty()
chart = st.empty()
stats = st.empty()

col_graph1, col_graph2 = st.columns(2)
with col_graph1:
    st.write("📈 Anlık Araç Yoğunluğu Grafiği")
    graph_density = st.empty()
with col_graph2:
    st.write("⏳ Birikimli Gecikme Süresi Grafiği")
    graph_wait = st.empty()


# MAIN SIMULATION RUNNER

while st.session_state.running:
    st.session_state.step += 1
    
    update_light_ai()
    update_pedestrians()
    spawn_vehicle()
    move_vehicles()

    total = len(st.session_state.vehicles)
    density = total / ROAD_LENGTH
    speeds = [v["speed"] for v in st.session_state.vehicles]
    avg_speed = sum(speeds) / total if total > 0 else 0
    queue = len([v for v in st.session_state.vehicles if LIGHT_POS - 15 <= v["x"] <= LIGHT_POS])

    st.session_state.history.append(total)
    st.session_state.wait_history.append(st.session_state.total_wait)

    ai_text_slot.markdown(f"**🤖 AI Sinyalizasyon Merkezi Durumu:** `{st.session_state.ai_decision}`")
    
    has_critical = any([v["type"] in ["ambulance", "firetruck"] for v in st.session_state.vehicles])
    if has_critical:
        warning.error("🚨 KRİTİK SEVİYE: Ambulans/İtfaiye Geçiyor! Araçlar müsait yan şeride kaçıyor ve hızlanıyor.")
    elif st.session_state.pedestrian_requested:
        warning.info("⏳ YAYA İSTEĞİ ALINDI: Yapay zeka ilk güvenli boşlukta trafiği durdurup yayalara yol verecek.")
    elif st.session_state.pedestrian_mode:
        warning.warning("🚶 Akıllı Yaya Geçidi Aktif. Araçlar güvenli mesafede bekletiliyor.")
    else:
        warning.success("✅ AI Trafik Yönetim Sistemi Aktif: Akış optimize ediliyor.")

    # DRAW (MATPLOTLIB)
    fig, ax = plt.subplots(figsize=(16, 4))
    bg, road = "#eef9ff", "#444444"
    ax.set_facecolor(bg)
    fig.patch.set_facecolor(bg)

    ax.fill_between([0, ROAD_LENGTH], -0.8, 0.8, color=road)
    for line in range(0, ROAD_LENGTH, 12):
        ax.plot([line, line + 6], [0, 0], color="white", linewidth=1.5, alpha=0.8)
    ax.plot([0, ROAD_LENGTH], [0.8, 0.8], color="#aaaaaa", linewidth=2)
    ax.plot([0, ROAD_LENGTH], [-0.8, -0.8], color="#aaaaaa", linewidth=2)
    
    for z in range(-4, 5):
        ax.vlines(LIGHT_POS + z, -0.8, 0.8, colors="white", linewidth=3, alpha=0.6)

    ax.scatter(LIGHT_POS, 1.1, c=st.session_state.light, s=650, edgecolors="black", zorder=5)

    for v in st.session_state.vehicles:
        ax.scatter(v["x"], v["current_y"], c=v["color"], s=280, edgecolors="black", zorder=4)
        ax.text(v["x"], v["current_y"] + 0.02, v["emoji"], fontsize=13, ha="center", va="center", zorder=5)

    for p in st.session_state.pedestrians:
        ax.text(p["x"], p["y"], "🚶", fontsize=14, ha="center", zorder=6)

    ax.set_xlim(0, ROAD_LENGTH)
    ax.set_ylim(-1.4, 1.6)
    ax.axis("off")
    
    chart.pyplot(fig)
    plt.close(fig)

    stats.dataframe(pd.DataFrame([{
        "Simülasyon Adımı": st.session_state.step,
        "Yoldaki Aktif Araç": total,
        "Anlık Işık Rengi": st.session_state.light.upper(),
        "Yol Doluluk Oranı": f"{min(100, int(density * 100))}%",
        "Ortalama Akış Hızı": f"{round(avg_speed, 2)} br/sn",
        "Işıktaki Kuyruk (Araç)": queue,
        "Sistemden Tahliye Olan": st.session_state.passed,
        "Sistem Toplam Gecikmesi": st.session_state.total_wait
    }]), hide_index=True)

    graph_density.line_chart(st.session_state.history, color="#FF4B4B")
    graph_wait.line_chart(st.session_state.wait_history, color="#0068C9")

    time.sleep(SIM_SPEED)