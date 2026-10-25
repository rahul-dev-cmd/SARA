import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

RED, BLUE, GREEN, GRAY = "#c62828", "#1565c0", "#2e7d32", "#616161"
fig, ax = plt.subplots(figsize=(22, 12.4))
ax.set_xlim(0, 230); ax.set_ylim(0, 130); ax.axis("off")

def box(x, y, w, h, text, fc="#f5f5f5", fs=9.5, bold=False, ec="#424242"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1", fc=fc, ec=ec, lw=1.3, zorder=3))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            zorder=4, linespacing=1.25)

def arrow(p, q, c=RED, lw=2.4):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=c, lw=lw, mutation_scale=15), zorder=5)

def panel(x, y, w, h, title):
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec="#9e9e9e", lw=1.2, zorder=1))
    ax.add_patch(Rectangle((x, y + h - 5), w, 5, fc="#37474f", ec="#37474f", zorder=2))
    ax.text(x + 2, y + h - 2.5, title, color="white", fontsize=11.5, fontweight="bold", va="center", zorder=3)

def table(x, y_top, cols, header, rows, rh, fs=8.6, hfc="#cfd8dc"):
    w = cols[-1]
    ax.add_patch(Rectangle((x, y_top - rh), w, rh, fc=hfc, ec="#78909c", lw=0.8, zorder=2))
    for i, h in enumerate(header):
        ax.text(x + cols[i] + 1, y_top - rh/2, h, fontsize=fs, fontweight="bold", va="center", zorder=4)
    for r, row in enumerate(rows):
        yy = y_top - rh * (r + 2)
        ax.add_patch(Rectangle((x, yy), w, rh, fc="#fafafa" if r % 2 else "white", ec="#cfd8dc", lw=0.6, zorder=2))
        for i, t in enumerate(row):
            ax.text(x + cols[i] + 1, yy + rh/2, t, fontsize=fs, va="center", zorder=4, linespacing=1.15)
    for c in cols[1:-1]:
        ax.plot([x + c, x + c], [y_top - rh * (len(rows) + 1), y_top], color="#cfd8dc", lw=0.6, zorder=3)

ax.text(1, 128.3, "SARA - Pin assignment and power distribution (planned design, not yet wired or tested)",
        fontsize=16, fontweight="bold", color="#263238", va="center")

# ======================= 1. POWER =======================
panel(1, 60, 92, 65, "1. POWER DISTRIBUTION AND REGULATION")
for x, t, fc in ((3, "2x 18650\nin series\n6.0 - 8.4 V", "#ffcdd2"), (25, "2S BMS\n(over-charge,\nover-discharge,\nshort-circuit)", "#ffcdd2"),
                 (47, "Fuse\n10 A", "#ffcdd2"), (69, "Main\nswitch", "#ffcdd2")):
    box(x, 107, 20, 11, t, fc, fs=8.8, bold=(x == 3))
for x in (23, 45, 67): arrow((x, 112.5), (x + 2, 112.5))
ax.plot([79, 79, 12], [107, 102, 102], color=RED, lw=3.4, zorder=5, solid_capstyle="round")
ax.text(46, 104.2, "7.4 V RAIL  (nominal; 6.0 - 8.4 V)", color=RED, fontsize=9.5, fontweight="bold", ha="center")
for x, t, fc in ((3, "TB6612 VM  (6 modules)\n\n12x N20 gear motors\n12 V-rated, run at\n7.4 V (slower)", "#ffe0b2"),
                 (33, "Buck 5 V / 3 A\n(set to about 5.1 V)\n\nPi Zero 2 W (pin 2)\nESP32 VIN\nMH-Z19B, LED string", "#ffcdd2"),
                 (63, "Buck 6 V / 5 A\n(set to 6.0 V)\n\nPCA9685 V+\n8x MG90S servos", "#ffcdd2")):
    box(x, 80, 28, 19, t, fc, fs=8.2)
for x in (17, 47, 77): arrow((x, 102), (x, 99))
box(3, 62, 87, 14, "3.3 V logic:  ESP32 on-board regulator  ->  PCA9685 VCC, 2x MCP23017 VDD + RESET, 6x TB6612 VCC\n"
                   "Pi Zero 3.3 V pins  ->  MLX90640, INMP441        |        GND: one common ground at battery negative\n"
                   "Design intent: 470 - 1000 uF on each buck output, 100 nF at every IC, 100 nF across each motor",
    "#e8f5e9", fs=7.9)
ax.annotate("", xy=(33, 79), xytext=(33, 76), arrowprops=dict(arrowstyle="-", color="none"))

# ======================= 2. ESP32 =======================
panel(95, 60, 71, 65, "2. ESP32 DEVKIT PIN ASSIGNMENT")
rows = [
    ("I2C SDA / SCL", "GPIO21 / 22", "PCA9685, MCP23017 x2"),
    ("UART2 RX", "GPIO16", "Pi TXD (GPIO14, pin 8)"),
    ("UART2 TX", "GPIO17", "Pi RXD (GPIO15, pin 10)"),
    ("MOTOR_EN", "GPIO27", "STBY of all 6 TB6612\n(10 k pull-down: off at boot)"),
    ("CO2 PWM input", "GPIO34", "MH-Z19B PWM out"),
    ("Battery NTC x2", "GPIO35, 36", "divider (10 k + NTC), ADC"),
    ("12 motor PWM", "4, 5, 13, 14, 15,\n18, 19, 23, 25, 26,\n32, 33", "TB6612 PWMA / PWMB\n(see motor map, panel 4)"),
    ("Power", "VIN / 3V3 / GND", "5 V from buck / 3.3 V out /\ncommon ground"),
]
y0 = 119
table(95, y0, [0, 21, 38, 71], ("Function", "GPIO", "Connects to"), rows, 5.6, fs=8)
# make tall rows readable: overlay note
ax.text(96, 62.4, "Avoided: GPIO0, 2, 12 (boot pins). GPIO5 and 15 are boot-strapping pins: check at bring-up.",
        fontsize=7.4, color=GRAY, style="italic")

# ======================= 3. PI =======================
panel(168, 60, 61, 65, "3. RASPBERRY PI ZERO 2 W CONNECTIONS")
rows = [
    ("Pin 2 (5V), 6 (GND)", "Buck 5 V (via fuse), GND"),
    ("CSI port", "Camera OV5647 (ribbon)"),
    ("Pin 3 / 5\nGPIO2 SDA / GPIO3 SCL", "MLX90640 (I2C 0x33)\nVIN: pin 1 (3.3 V)"),
    ("Pin 12 / 35 / 38\nGPIO18 / 19 / 20", "INMP441 SCK / WS / SD\nL/R to GND, VDD pin 17"),
    ("Pin 8 / 10\nGPIO14 TXD / 15 RXD", "ESP32 GPIO16 / GPIO17\n(3.3 V logic, common GND)"),
    ("Pin 32 (GPIO12)", "logic-level MOSFET gate ->\n4 LEDs, 100 ohm each, 5 V"),
    ("USB OTG port", "USB-Ethernet adapter\n(tether, design TBD)"),
]
table(168, y0, [0, 26, 61], ("Pi pin", "Connects to"), rows, 6.8, fs=7.8)

# ======================= 4. MOTOR MAP =======================
panel(1, 2, 118, 55, "4. MOTOR CHANNEL MAP (12 belts, 6 TB6612 drivers, 2 MCP23017)")
names = ["M1 left", "M1 right", "M1 top", "M1 bottom", "M2 left", "M2 right", "M2 top", "M2 bottom",
         "M3 left", "M3 right", "M3 top", "M3 bottom"]
pwm = [4, 5, 13, 14, 15, 18, 19, 23, 25, 26, 32, 33]
mrows = []
for i, n in enumerate(names):
    chip = 1 if i < 8 else 2
    k = (i % 8) if i < 8 else (i - 8)
    port = "A" if k < 4 else "B"
    p = (k % 4) * 2
    mrows.append((n, f"GPIO{pwm[i]}", f"MCP{chip} (0x2{chip-1}) G{port}{p} / G{port}{p+1}", f"TB{i//2+1} ch {'A' if i % 2 == 0 else 'B'}"))
table(1, 51, [0, 24, 46, 88, 118], ("Belt motor", "PWM (ESP32)", "IN1 / IN2 (MCP23017 pin)", "Driver channel"),
      mrows, 3.45, fs=8)

# ======================= 5. BUDGET =======================
panel(121, 2, 108, 55, "5. CURRENT BUDGET (typical datasheet values, NOT measured)")
txt = [
    ("5 V rail (buck 3 A)", "Pi about 0.3 - 1.0 A, ESP32 about 0.1 - 0.25 A, CO2 sensor peak about 0.15 A,\nLEDs about 0.08 A.   Total about 0.7 - 1.5 A  ->  fits.", GREEN),
    ("6 V rail (buck 5 A)", "8x MG90S: stall about 0.7 A each = about 5.6 A worst case, above the 5 A buck.\n->  Firmware must limit how many servos move at once. Risk.", RED),
    ("7.4 V rail (motors)", "12x N20: moving about 0.1 - 0.2 A each (about 1.2 - 2.4 A); all-stalled current is\nmuch higher and unknown. BMS and fuse are 10 A.  ->  soft-start, ramped PWM,\nlimit simultaneous drive. Measure on the bench.", RED),
    ("Not yet decided", "Battery runtime, tether data link, wire gauge through the 4 joints (24 motor wires\n+ power + signals in a 12 mm core hole), and ESP32 spare pins (almost none).", "#ef6c00"),
]
yy = 50
for h, t, c in txt:
    ax.text(123, yy, h, fontsize=9.2, fontweight="bold", color=c, va="top")
    ax.text(123, yy - 3.3, t, fontsize=8.0, va="top", linespacing=1.3)
    yy -= 11.5 if t.count("\n") < 2 else 14
fig.savefig("SARA_Pinout_and_Power.png", dpi=110, bbox_inches="tight", facecolor="white")
print("ok")
