import random
from paho.mqtt import client as mqtt_client
import json
import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit
import time
import Adafruit_PCA9685
import tkinter
from tkinter import *
import customtkinter as ctk
import threading

# Initialize ServoKit
kit = ServoKit(channels=16)
# ---------------------------------------------------------------- EVENING PILL CLASS AND LIST
# Define and initialize an empty array to hold the evening pills
evening_pills = []

class Evening:
    def __init__(self, Ename: str, Econtainer: str, Edosage: int, Equantity: int, Edescription: str, Efrequency: str):
        self.Ename = Ename
        self.Econtainer = Econtainer
        self.Edosage = Edosage
        self.Equantity = Equantity
        self.Echannel = None
        self.Edescription = Edescription
        self.Efrequency = Efrequency

# Variables to track scans and pill information
scanCount = 0
name = None
description = None
dosage = None
frequency = None
current_color = None
quantity = None

# --------------------------------------------------------------- MQTT SETTINGS
broker = 'mqtt.things.ph'
port = 1883
topic = "pibot"
client_id = f'publish-{random.randint(0, 1000)}'
username = '66b49ce0c762db171066c05a'
password = 'A1Zhqr0MKXUz7GXdCRAx5FVD'

# MQTT connection
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global description, dosage, frequency, quantity, name, scanCount
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        scanCount += 1
        
        data = json.loads(msg.payload.decode())
        description = data.get("description")
        dosage = data.get("dosage")
        quantity = data.get("quantity")
        name = data.get("name")
        frequency = data.get("frequency")
        current_color = data.get("currentColor")

        print(name, description, dosage, frequency, current_color, quantity)
        
        if scanCount < 3:
            process_med_info(name, current_color, description, dosage, quantity, frequency, evening_pills)
        else:
            evening_pills.clear()
            scanCount = 0
            process_med_info(name, current_color, description, dosage, quantity, frequency, evening_pills)

    client.subscribe(topic)
    client.on_message = on_message
    print("Exiting out of subscribe...")

def process_med_info(name, current_color, description, dosage, quantity, frequency, evening_pills):
    if frequency.lower() in ["daily", "everyday", "once"]:
        pill = Evening(name, current_color, dosage, quantity, description, frequency)
        evening_pills.append(pill)
        print("New Evening Pill Added:", pill.__dict__)
    else:
        pill = Evening(name, current_color, dosage, quantity, description, frequency)
        evening_pills.append(pill)
        print("New Evening Pill Added:", pill.__dict__)
# ------------------------------------------------------------------------- DISPENSING MECHANISMS
def set_servos():
    for pill in evening_pills:
        if pill.Econtainer == "blue":
            pill.Echannel = 0
        elif pill.Econtainer == "red":
            pill.Echannel = 4
        elif pill.Econtainer == "green":
            pill.Echannel = 8
        elif pill.Econtainer == "purple":
            pill.Echannel = 12
    for pill in evening_pills:
        print(f"Container: {pill.Econtainer}, GPIO Pin: {pill.Echannel}")

def pulse_width_to_pwm(pulse_width_us):
    return int(pulse_width_us * 4096 / 20000)

def stop_servos():
    neutral_pwm_value = pulse_width_to_pwm(0)
    for channel in range(16):
        pwm.set_pwm(channel, 0, neutral_pwm_value)

pwm = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
pwm.set_pwm_freq(60)

GPIO.setmode(GPIO.BCM)
led_pin = 19
Buzzer = 21
SENSOR_PIN1 = 4
SENSOR_PIN2 = 17
SENSOR_PIN3 = 22
SENSOR_PIN4 = 18

GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(Buzzer, GPIO.OUT)
GPIO.setup(SENSOR_PIN1, GPIO.IN)
GPIO.setup(SENSOR_PIN2, GPIO.IN)
GPIO.setup(SENSOR_PIN3, GPIO.IN)
GPIO.setup(SENSOR_PIN4, GPIO.IN)

Buzz = GPIO.PWM(Buzzer, 1000)
GPIO.output(led_pin, GPIO.LOW)

def set_throttle(channel, throttle_value):
    pwm_value = 409 if throttle_value == 1 else 204 if throttle_value == -1 else 0
    pwm.set_pwm(channel, 0, pwm_value)

def set_throttle2(channel, throttle_value):
    pwm_value2 = int(throttle_value)
    pwm.set_pwm(channel, 0, pwm_value2)

def pillOut(index):
    set_throttle(evening_pills[index].Echannel, -1)
    time.sleep(0.25)
    print("Shook the container on channel", evening_pills[index].Echannel)
    set_throttle(evening_pills[index].Echannel, 1)
    time.sleep(10)
    stop_servos()
# ---------------------------------------------------------------- GUI DISPlAY
count = 0
streakCount = 0
button1_clicked = False

# GUI Setup
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title('PillPal GUI')
window.geometry("800x480")

# Streak Frame
streakframe = ctk.CTkFrame(window, width=800, height=480)
streakframe.pack(padx=5, pady=5)
streakframe.pack_propagate(False)

streak = ctk.CTkLabel(streakframe, height=800, width=800, text=f"You're on a \n {streakCount} day streak!", font=('Sans-Serif', 40, 'bold'), fg_color='#ffb9d5')
streak.pack()

hi = ctk.CTkLabel(streakframe, width=800, height=80, text="Hi, PillPal User", fg_color='#ffff9c', text_color='black', font=('Sans-Serif', 30, 'bold'))
hi.place(relx=0.5, rely=0.08, anchor=tkinter.CENTER)

# Ready Frame
readyframe = ctk.CTkFrame(window, width=800, height=480)
readyframe.pack(padx=5, pady=5)
readyframe.pack_propagate(False)

label1 = ctk.CTkLabel(readyframe, width=800, height=500, text="It's time to take your medication.", text_color='black', font=('Sans-Serif', 35, 'bold'), fg_color='#ffb9d5')
label1.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)

# Dispense Frame
dispenseframe = ctk.CTkFrame(window, width=800, height=480)
dispenseframe.pack(padx=5, pady=5)
dispenseframe.pack_propagate(False)

label2 = ctk.CTkLabel(dispenseframe, width=800, height=500, text="Dispensing...", text_color='black', font=('Sans-Serif', 40, 'bold'), fg_color='#ffb9d5')
label2.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

# Alert Frame
alertframe = ctk.CTkFrame(window, width=800, height=480)
alertframe.pack(padx=5, pady=5)
alertframe.pack_propagate(False)
alertframe.pack_forget()  # Hide the alert frame initially

alertlabel = ctk.CTkLabel(alertframe, width=800, height=500, text="You have {days} day(s) of {name} left", text_color='black', font=('Sans-Serif', 40, 'bold'), fg_color='#ffb9d5')
alertlabel.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

hi = ctk.CTkLabel(alertframe, width=800, height=80, text="Hi, PillPal User", fg_color='#ffff9c', text_color='black', font=('Sans-Serif', 30, 'bold'))
hi.pack(padx=10, pady=10)

# Button to switch pages
def next_page():
    global count, button1_clicked
    #count = (count + 1) % len(pages)
    #testing if this works below!!!
    show_page(2)
    
    #set flag to true when button is clicked
    button1_clicked = True
    print("button clicked!")

def show_page(page_index):
    for frame in pages:
        frame.pack_forget()
    pages[page_index].pack(padx=5, pady=5)

button1 = ctk.CTkButton(readyframe, text="Dispense", font=('Sans-Serif', 20, 'bold'), width=300, height=75, fg_color='#ff78ae', border_width=5, border_color='red', hover_color='red', command=next_page)
button1.place(relx=0.5, rely=0.65, anchor=tkinter.CENTER)

pages = [streakframe, readyframe, dispenseframe, alertframe]

evening_pills.append(Evening(Ename="pill1", Econtainer="blue", Edosage=2, Equantity=10, Edescription="with food", Efrequency ="twice"))
def run_background_tasks():
    global streakCount, button1_clicked
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    
    while True:
        #wait for the appropriate amount of time for a scan to occur
        time.sleep(10)
        set_servos()
        print("Assigned the pill objects to servos!")
        
        show_page(1)  # Show Ready Page
        print("Ready to Dispense!")
        GPIO.output(led_pin, GPIO.HIGH)
        Buzz.start(20)
        #time.sleep(5)

        if button_clicked == True:
            
            print("Time to dispense!")
            GPIO.output(led_pin, GPIO.LOW)
            Buzz.stop()
        
            for i in range(len(evening_pills)):
                print(evening_pills[i].Econtainer + " dispensing")
                for j in range(evening_pills[i].Edosage):
                    print(str(evening_pills[i].Edosage) + " pills dispensing")
                    print("Calling pillOut(), dispensing has started.")
                    pillOut(i)
                    print("Exit completed. Next pill is dispensing...")
                
                    # Show alert frame
                    alertlabel.configure(text=f"You have {evening_pills[i].Equantity - j - 1} day(s) of {evening_pills[i].Ename} left")
                    show_page(3)  # Show Alert Page
                    window.update_idletasks()
                    time.sleep(5)  # Keep the alert frame visible for 5 seconds
                    show_page(2)  # Return to the dispensing frame
                
                print("Next container is dispensing...")
                time.sleep(2)
            streakCount += 1
            streak.configure(text=f"You're on a \n {streakCount} day streak!")
            print("Finished Dispensing!")
            show_page(0)
            button1_clicked = False

# Start background tasks in a separate thread
threading.Thread(target=run_background_tasks, daemon=True).start()

window.mainloop()
GPIO.cleanup()
