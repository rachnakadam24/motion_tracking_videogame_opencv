
# This script merges your full Punch n Pop game and punch detection controller
# Run this on your Raspberry Pi after installing dependencies:
# pip install pygame opencv-python pyserial numpy

# === PUNCH N POP GAME WITH SERIAL + VISION CONTROLLER ===

# === SERIAL + CAMERA THREAD SETUP ===
import pygame
import cv2
import numpy as np
import threading
import serial
import time
import random
import math
import sys
import json
import os

# Set up serial port
ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
punch_detected = None
ball_positions = {"orange": None, "green": None}

# Define HSV Ranges for ball tracking
lower_green1 = np.array([40, 70, 70])
upper_green1 = np.array([60, 255, 255])
lower_green2 = np.array([61, 100, 70])
upper_green2 = np.array([85, 255, 255])
lower_orange1 = np.array([5, 100, 100])
upper_orange1 = np.array([12, 255, 255])
lower_orange2 = np.array([13, 80, 80])
upper_orange2 = np.array([25, 255, 255])

# Ball detection helper
def detect_ball(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 300:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            if radius > 10:
                return (int(x), int(y)), y
    return None, None

# Serial thread
def serial_listener():
    global punch_detected
    while True:
        try:
            line = ser.readline().decode().strip()
            if "ID: 1 | Data: 100" in line:
                punch_detected = 'orange'
                # print("Orange Punch")
            elif "ID: 1 | Data: 200" in line:
                punch_detected = 'green'
                # print("Green Punch")
        except Exception as e:
            print(f"[ERROR] Serial read error: {e}")

# Camera thread
def vision_tracking():
    global ball_positions
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame_height = frame.shape[0]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask_g1 = cv2.inRange(hsv, lower_green1, upper_green1)
        mask_g2 = cv2.inRange(hsv, lower_green2, upper_green2)
        mask_green = cv2.bitwise_or(mask_g1, mask_g2)

        mask_o1 = cv2.inRange(hsv, lower_orange1, upper_orange1)
        mask_o2 = cv2.inRange(hsv, lower_orange2, upper_orange2)
        mask_orange = cv2.bitwise_or(mask_o1, mask_o2)

        _, y_g = detect_ball(mask_green)
        if y_g:
            ball_positions["green"] = y_g / frame_height
        _, y_o = detect_ball(mask_orange)
        if y_o:
            ball_positions["orange"] = y_o / frame_height

# Start threads
threading.Thread(target=serial_listener, daemon=True).start()
threading.Thread(target=vision_tracking, daemon=True).start()

#Adding stickman

import pygame
import sys
import random
import math
import time
import json
import os
pygame.init()

global username
highscore_file = "highscore.txt"
# Window setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Red Balloons")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
DARK_ORANGE = (240, 95, 0)
LIGHT_ORANGE = (255, 180, 130)
DARK_GREEN  = (86, 171, 21)
LIGHT_GREEN = (191, 247, 148)
ORANGE = (240, 95, 0)
GREEN = (86, 171, 21)

image_path = "processedimage.jpg" if os.path.exists("processedimage.jpg") else "black.png"
head_img = pygame.image.load(image_path).convert_alpha()


COLOR_LIST = [DARK_ORANGE, LIGHT_ORANGE, DARK_GREEN, LIGHT_GREEN]

KEY_COLOR_MAP = {
    pygame.K_q: LIGHT_ORANGE,
    pygame.K_w: DARK_ORANGE,
    pygame.K_e: LIGHT_GREEN,
    pygame.K_r: DARK_GREEN,
}

def capture_and_crop_face():
    import cv2

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    face_img = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Press C to Capture, Q to Quit", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5)

            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_img = frame[y:y+h, x:x+w]
                cv2.imwrite("processedimage.jpg", face_img)
                print("Face captured and saved as processedimage.jpg")
                break
            else:
                print("No face detected. Try again.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Balloon properties
balloon_radius = 50
string_length = 50
offset = balloon_radius + string_length // 2
screen_balloon_spawn_percent = 0.35

# Spawn settings
balloons_per_second = 0.5
spawn_interval = 1.0 / balloons_per_second

def reset_game():
    global balloons, score, lives, last_spawn_time
    balloons = []
    score = 0
    lives = 5
    last_spawn_time = time.time()

reset_game()

max_lives = 5
clock = pygame.time.Clock()

def draw_balloon(center_x, center_y, radius, color):
    pygame.draw.circle(screen, color, (center_x, center_y), radius)
    pygame.draw.line(screen, color, (center_x, center_y + radius),
                     (center_x, center_y + radius + string_length), 3)

def draw_shard_burst(center_x, center_y, burst_color):
    shard_count = 10
    for i in range(shard_count):
        angle = i * (360 / shard_count)
        length = 40 + random.randint(0, 20)
        tip_x = center_x + int(length * math.cos(math.radians(angle)))
        tip_y = center_y + int(length * math.sin(math.radians(angle)))
        base1_x = center_x + int(10 * math.cos(math.radians(angle + 20)))
        base1_y = center_y + int(10 * math.sin(math.radians(angle + 20)))
        base2_x = center_x + int(10 * math.cos(math.radians(angle - 20)))
        base2_y = center_y + int(10 * math.sin(math.radians(angle - 20)))
        pygame.draw.polygon(screen, burst_color, [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)])

def draw_heart(surface, x, y, size=20, filled=True):
    color = (255, 0, 0) if filled else GREY
    radius = size // 2
    pygame.draw.circle(surface, color, (x - radius+4, y - radius+ 20), radius)
    pygame.draw.circle(surface, color, (x + radius-4, y - radius+20), radius)
    points = [
        (x - size+4, y - radius+4+20),
        (x + size-4, y - radius+4+20),
        (x, y + size-16+20)
    ]
    pygame.draw.polygon(surface, color, points)

def spawn_balloon():
    min_x = int(screen.get_width() * screen_balloon_spawn_percent) + balloon_radius
    max_x = screen.get_width() - balloon_radius
    x = random.randint(min_x, max_x)  # only spawn in right 75% of screen
    y = screen.get_height() + balloon_radius  # start just below bottom edge
    color = random.choice(COLOR_LIST)
    return {'x': x, 'y': y, 'color': color, 'burst': False}


# ===================== Stickman =====================
def draw_stickman(surface, x, y, scale=1.0, left_up=False, right_up=False):
    head_radius = int(40 * scale)
    neck_length = int(10 * scale)
    body_length = int(120 * scale)
    body_width_bottom = int(30 * scale)
    limb_length = int(100 * scale)
    arm_width = 8
    leg_width = 10
    foot_width = int(50 * scale)
    foot_height = int(15 * scale)
    arm_offset = int(30 * scale)

    head_size = head_radius * 2
    scaled_img = pygame.transform.smoothscale(head_img, (head_size, head_size))
    mask_surface = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (head_radius, head_radius), head_radius)
    circular_head = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
    circular_head.blit(scaled_img, (0, 0))
    circular_head.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(circular_head, (x - head_radius, y - head_radius))
    pygame.draw.circle(surface, WHITE, (x, y), head_radius, 3)

    neck_top = (x, y + head_radius)
    neck_bottom = (x, y + head_radius + neck_length)
    pygame.draw.line(surface, WHITE, neck_top, neck_bottom, 4)

    base_left = (x - body_width_bottom, neck_bottom[1])
    base_right = (x + body_width_bottom, neck_bottom[1])
    tip = (x, neck_bottom[1] + body_length)
    pygame.draw.polygon(surface, WHITE, [base_left, base_right, tip])

    shoulder_y = neck_bottom[1] + 10
    left_hand = (x - head_radius - arm_offset, y - arm_offset) if left_up else (x - limb_length, shoulder_y + 30)
    right_hand = (x + head_radius + arm_offset, y - arm_offset) if right_up else (x + limb_length, shoulder_y + 30)

    pygame.draw.line(surface, WHITE, (x, shoulder_y), left_hand, arm_width)
    pygame.draw.line(surface, WHITE, (x, shoulder_y), right_hand, arm_width)
    pygame.draw.circle(surface, GREEN, left_hand, 25)
    pygame.draw.circle(surface, ORANGE, right_hand, 25)

    hip_y = tip[1]
    left_leg = (x - limb_length // 2, hip_y + limb_length)
    right_leg = (x + limb_length // 2, hip_y + limb_length)
    pygame.draw.line(surface, WHITE, (x - 20, hip_y), left_leg, leg_width)
    pygame.draw.line(surface, WHITE, (x + 20, hip_y), right_leg, leg_width)
    pygame.draw.ellipse(surface, WHITE, (left_leg[0] - 25, left_leg[1] - 10, foot_width, foot_height))
    pygame.draw.ellipse(surface, WHITE, (right_leg[0] - 25, right_leg[1] - 10, foot_width, foot_height))

# ===================== Stickwoman =====================
def draw_stickwoman(surface, x, y, scale=1.0, left_up=False, right_up=False):
    head_radius = int(40 * scale)
    neck_length = int(10 * scale)
    body_length = int(120 * scale)
    body_width_bottom = int(30 * scale)
    limb_length = int(100 * scale)
    arm_width = 8
    leg_width = 10
    foot_width = int(50 * scale)
    foot_height = int(15 * scale)
    arm_offset = int(30 * scale)

    head_size = head_radius * 2
    scaled_img = pygame.transform.smoothscale(head_img, (head_size, head_size))
    mask_surface = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (head_radius, head_radius), head_radius)
    circular_head = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
    circular_head.blit(scaled_img, (0, 0))
    circular_head.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(circular_head, (x - head_radius, y - head_radius))
    pygame.draw.circle(surface, WHITE, (x, y), head_radius, 3)

    # Braids
    braid_color = WHITE
    oval_w, oval_h = int(12 * scale), int(20 * scale)
    triangle_h, triangle_w = int(10 * scale), int(16 * scale)
    base_y = y + int(0.2 * head_radius)
    left_x = x - head_radius - 5
    right_x = x + head_radius - oval_w + 5

    for bx in [left_x, right_x]:
        pygame.draw.ellipse(surface, braid_color, (bx, base_y, oval_w, oval_h))
        pygame.draw.ellipse(surface, braid_color, (bx, base_y + oval_h - 4, oval_w, oval_h))
        tip_x = bx + oval_w // 2
        tip_y = base_y + 2 * oval_h + triangle_h
        braid_tri = [
            (tip_x - triangle_w // 2, tip_y - 10),
            (tip_x + triangle_w // 2, tip_y - 10),
            (tip_x, tip_y - triangle_h - 10)
        ]
        pygame.draw.polygon(surface, braid_color, braid_tri)

    neck_top = (x, y + head_radius)
    neck_bottom = (x, y + head_radius + neck_length)
    pygame.draw.line(surface, WHITE, neck_top, neck_bottom, 4)

    top_center = neck_bottom
    bottom_left = (x - body_width_bottom, top_center[1] + body_length)
    bottom_right = (x + body_width_bottom, top_center[1] + body_length)
    pygame.draw.polygon(surface, WHITE, [top_center, bottom_left, bottom_right])

    shoulder_y = top_center[1] + 10
    left_hand = (x - head_radius - arm_offset, y - arm_offset) if left_up else (x - limb_length, shoulder_y + 30)
    right_hand = (x + head_radius + arm_offset, y - arm_offset) if right_up else (x + limb_length, shoulder_y + 30)

    pygame.draw.line(surface, WHITE, (x, shoulder_y), left_hand, arm_width)
    pygame.draw.line(surface, WHITE, (x, shoulder_y), right_hand, arm_width)
    pygame.draw.circle(surface, GREEN, left_hand, 25)
    pygame.draw.circle(surface, ORANGE, right_hand, 25)

    hip_y = y + head_radius + neck_length + body_length
    left_leg = (x - limb_length // 2, hip_y + limb_length)
    right_leg = (x + limb_length // 2, hip_y + limb_length)
    pygame.draw.line(surface, WHITE, (x - 20, hip_y), left_leg, leg_width)
    pygame.draw.line(surface, WHITE, (x + 20, hip_y), right_leg, leg_width)
    pygame.draw.ellipse(surface, WHITE, (left_leg[0] - 25, left_leg[1] - 10, foot_width, foot_height))
    pygame.draw.ellipse(surface, WHITE, (right_leg[0] - 25, right_leg[1] - 10, foot_width, foot_height))
                
# ===================== Character Selection =====================
def character_selection():
    font_title = pygame.font.SysFont(None, 64)
    font_button = pygame.font.SysFont(None, 36)

    while True:
        screen.fill(BLACK)
        current_width = screen.get_width()
        current_height = screen.get_height()

        # Buttons under characters
        male_button = pygame.Rect(0, 0, 100, 50)
        female_button = pygame.Rect(0, 0, 100, 50)
        male_button.center = (current_width // 4, current_height // 2 + 140)
        female_button.center = (3 * current_width // 4, current_height // 2 + 140)

        # Title
        title = font_title.render("CHOOSE A CHARACTER", True, WHITE)
        screen.blit(title, (current_width // 2 - title.get_width() // 2, 50))

        # Draw characters
        draw_stickman(screen, current_width // 4, current_height // 2 - 50, scale=1.0)
        draw_stickwoman(screen, 3 * current_width // 4, current_height // 2 - 50, scale=1.0)

        # Buttons
        pygame.draw.rect(screen, (200, 200, 200), male_button)
        pygame.draw.rect(screen, WHITE, male_button, 2)
        male_text = font_button.render("Punchy", True, BLACK)
        screen.blit(male_text, male_text.get_rect(center=male_button.center))

        pygame.draw.rect(screen, (200, 200, 200), female_button)
        pygame.draw.rect(screen, WHITE, female_button, 2)
        female_text = font_button.render("Popy", True, BLACK)
        screen.blit(female_text, female_text.get_rect(center=female_button.center))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if male_button.collidepoint(event.pos):
                        return "male"
                    elif female_button.collidepoint(event.pos):
                        return "female"

def show_selected_character(character, username):
    font = pygame.font.SysFont(None, 48)
    font_button = pygame.font.SysFont(None, 36)

    button_width, button_height = 160, 50
    next_button = pygame.Rect(0, 0, button_width, button_height)

    while True:
        screen.fill(BLACK)
        current_width = screen.get_width()
        current_height = screen.get_height()

        # Title
        label_text = font.render(f"This is you - {username}", True, WHITE)
        screen.blit(label_text, (current_width // 2 - label_text.get_width() // 2, 40))

        # Key controls
        keys = pygame.key.get_pressed()
        left_up = keys[pygame.K_a]
        right_up = keys[pygame.K_k]

        # Character render
        if character == "male":
            draw_stickman(screen, current_width // 2, current_height // 2 - 50, scale=1.2,
                          left_up=left_up, right_up=right_up)
        else:
            draw_stickwoman(screen, current_width // 2, current_height // 2 - 50, scale=1.2,
                            left_up=left_up, right_up=right_up)

        # Next button (bottom right)
        next_button.bottomright = (current_width - 20, current_height - 20)
        pygame.draw.rect(screen, (200, 200, 200), next_button)
        pygame.draw.rect(screen, WHITE, next_button, 2)
        next_text = font_button.render("Next", True, BLACK)
        screen.blit(next_text, next_text.get_rect(center=next_button.center))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and next_button.collidepoint(event.pos):
                    return
                
def load_highscore():
    if not os.path.exists(highscore_file):
        return {"score": 0, "username": "None"}
    with open(highscore_file, "r") as f:
        return json.load(f)

def save_highscore(score, username):
    data = {"score": score, "username": username}
    with open(highscore_file, "w") as f:
        json.dump(data, f)


def show_game_over():
    button_width, button_height = 200, 60
    button_color = (200, 200, 200)
    button_hover = (230, 230, 230)
    text_color = (0, 0, 0)
    border_color = (50, 50, 50)

    font_title = pygame.font.SysFont(None, 72)
    font_button = pygame.font.SysFont(None, 36)

    # Load current high score data
    highscore_data = load_highscore()
    is_new_high = score > highscore_data["score"]

    if is_new_high:
        save_highscore(score, username)
        highscore_data = {"score": score, "username": username}

    while True:
        current_width = screen.get_width()
        current_height = screen.get_height()

        restart_button = pygame.Rect(0, 0, button_width, button_height)
        exit_button = pygame.Rect(0, 0, button_width, button_height)
        restart_button.center = (current_width // 2, current_height // 2 + 80)
        exit_button.center = (current_width // 2, current_height // 2 + 160)

        screen.fill(BLACK)

        # GAME OVER Title
        title_surf = font_title.render("GAME OVER", True, (255, 255, 0))
        screen.blit(title_surf, title_surf.get_rect(center=(current_width // 2, current_height // 2 - 120)))

        # Current score
        current_score_txt = font_button.render(f"Your Score: {score}", True, WHITE)
        screen.blit(current_score_txt, current_score_txt.get_rect(center=(current_width // 2, current_height // 2 - 40)))

        # High score
        high_score_txt = font_button.render(f"High Score: {highscore_data['score']} ({highscore_data['username']})", True, WHITE)
        screen.blit(high_score_txt, high_score_txt.get_rect(center=(current_width // 2, current_height // 2)))

        # Restart button
        mouse_pos = pygame.mouse.get_pos()
        restart_hover = restart_button.collidepoint(mouse_pos)
        restart_color = button_hover if restart_hover else button_color
        pygame.draw.rect(screen, restart_color, restart_button)
        pygame.draw.rect(screen, border_color, restart_button, 2)
        restart_text = font_button.render("Restart", True, text_color)
        screen.blit(restart_text, restart_text.get_rect(center=restart_button.center))

        # Exit button
        exit_hover = exit_button.collidepoint(mouse_pos)
        exit_color = button_hover if exit_hover else button_color
        pygame.draw.rect(screen, exit_color, exit_button)
        pygame.draw.rect(screen, border_color, exit_button, 2)
        exit_text = font_button.render("Exit", True, text_color)
        screen.blit(exit_text, exit_text.get_rect(center=exit_button.center))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if restart_button.collidepoint(event.pos):
                    return True
                elif exit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    return True

def show_start_screen(screen):
    title_font = pygame.font.SysFont(None, 80)
    button_font = pygame.font.SysFont(None, 40)

    button_width, button_height = 200, 60
    start_button = pygame.Rect(0, 0, button_width, button_height)
    quit_button = pygame.Rect(0, 0, button_width, button_height)

    while True:
        screen_width, screen_height = screen.get_width(), screen.get_height()

        start_button.center = (screen_width // 2, screen_height // 2)
        quit_button.center = (screen_width // 2, screen_height // 2 + 100)

        screen.fill(BLACK)

        title_text = title_font.render("Punch n Pop", True, WHITE)
        title_rect = title_text.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_text, title_rect)

        pygame.draw.rect(screen, (200, 200, 200), start_button)
        pygame.draw.rect(screen, WHITE, start_button, 3)
        start_text = button_font.render("Start", True, BLACK)
        screen.blit(start_text, start_text.get_rect(center=start_button.center))

        pygame.draw.rect(screen, (200, 200, 200), quit_button)
        pygame.draw.rect(screen, WHITE, quit_button, 3)
        quit_text = button_font.render("Quit", True, BLACK)
        screen.blit(quit_text, quit_text.get_rect(center=quit_button.center))
    
        

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    return True
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

def show_username_entry(screen):
    font = pygame.font.SysFont(None, 48)
    username = ""
    active = True

    while active:
        screen_width, screen_height = screen.get_width(), screen.get_height()
        input_box = pygame.Rect(screen_width // 2 - 100, screen_height // 2, 200, 50)

        screen.fill(BLACK)

        prompt = font.render("Enter Username", True, WHITE)
        screen.blit(prompt, (screen_width // 2 - prompt.get_width() // 2, screen_height // 2 - 80))

        pygame.draw.rect(screen, WHITE, input_box, 2)
        text_surface = font.render(username, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    username += event.unicode
    return username


# Main loop
show_start_screen(screen)
username = show_username_entry(screen)
character = character_selection()
# capture_and_crop_face()
image_path = "static_face.jpg"
# Reload the face image after capture
#image_path = "processedimage.jpg"
head_img = pygame.image.load(image_path).convert_alpha()
show_selected_character(character, username)
highscore_data = load_highscore()

running = True
while running:
    screen.fill(BLACK)
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in KEY_COLOR_MAP:
                for balloon in balloons:
                    if balloon['color'] == KEY_COLOR_MAP[event.key]:
                        balloon['burst'] = True
                        if balloon['color'] in [DARK_ORANGE, DARK_GREEN]:
                            score += 10
                        else:
                            score += 5
                        break
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    
    if punch_detected:
        pos = ball_positions[punch_detected]
        if pos is not None:
            key = None
            char_x = int(screen.get_width() * screen_balloon_spawn_percent) // 2
            char_y = screen.get_height() // 2 - 50
            if punch_detected == 'orange':
                # key = pygame.K_q if pos < 0.5 else pygame.K_w
                if pos < 0.5:
                    key = pygame.K_q
                    print("Orange Punch UP")
                    # if character == "male":
                        # draw_stickman(screen, char_x, char_y, scale=1.0,
                                    # left_up=True, right_up=False)
                    # else:
                        # draw_stickwoman(screen, char_x, char_y, scale=1.0,
                                        # left_up=True, right_up=False)
                else:
                    key = pygame.K_w
                    print("Orange Punch DOWN")
                    # if character == "male":
                        # draw_stickman(screen, char_x, char_y, scale=1.0,
                                    # left_up=False, right_up=False)
                    # else:
                        # draw_stickwoman(screen, char_x, char_y, scale=1.0,
                                        # left_up=False, right_up=False)
            elif punch_detected == 'green':
                #key = pygame.K_e if pos < 0.5 else pygame.K_r
                if pos < 0.5:
                    key = pygame.K_e
                    print("Gree Punch UP")
                    # if character == "male":
                        # draw_stickman(screen, char_x, char_y, scale=1.0,
                                    # left_up=False, right_up=True)
                    # else:
                        # draw_stickwoman(screen, char_x, char_y, scale=1.0,
                                        # left_up=False, right_up=True)
                else:
                    key = pygame.K_r
                    print("Gree Punch DOWN")
                    # if character == "male":
                        # draw_stickman(screen, char_x, char_y, scale=1.0,
                                    # left_up=False, right_up=False)
                    # else:
                        # draw_stickwoman(screen, char_x, char_y, scale=1.0,
                                        # left_up=False, right_up=False)

            if key in KEY_COLOR_MAP:
                for balloon in balloons:
                    if balloon['color'] == KEY_COLOR_MAP[key] and not balloon['burst']:
                        balloon['burst'] = True
                        if balloon['color'] in [DARK_ORANGE, DARK_GREEN]:
                            score += 10
                        else:
                            score += 5
                        break
        punch_detected = None

    if current_time - last_spawn_time >= spawn_interval:
        balloons.append(spawn_balloon())
        last_spawn_time = current_time

    for balloon in balloons[:]:
        if balloon['burst']:
            draw_shard_burst(balloon['x'], balloon['y'], balloon['color'])
            balloons.remove(balloon)
            continue

        draw_balloon(balloon['x'], balloon['y'], balloon_radius, balloon['color'])
        balloon['y'] -= 5

        if balloon['y'] < -balloon_radius:
            balloons.remove(balloon)
            lives -= 1
            if lives <= 0:
                if show_game_over():
                    reset_game()

    # Score display
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Player: {username}    Score: {score}", True, GREY)
    screen.blit(score_text, (screen.get_width() - 350, 10))

    # Lives display
    for i in range(max_lives):
        draw_heart(screen, 25 + i * 40, 10, filled=(i < lives))

    # Draw grey border for balloon spawn area
    spawn_left = int(screen.get_width() * screen_balloon_spawn_percent)
    spawn_top = 0
    spawn_width = screen.get_width() - spawn_left
    spawn_height = screen.get_height()
    pygame.draw.rect(screen, GREY, (spawn_left, spawn_top, spawn_width, spawn_height), 2)

    # Draw stickperson in left 35% of the screen
    # Draw stickperson in left 35% of the screen with arm logic
    char_x = int(screen.get_width() * screen_balloon_spawn_percent) // 2
    char_y = screen.get_height() // 2 - 50

    # These lines MUST be inside the while loop, just before drawing the character
    keys = pygame.key.get_pressed()
    left_up = keys[pygame.K_q]               # raise green (left)
    right_up = keys[pygame.K_e]              # raise orange (right)

    if character == "male":
        draw_stickman(screen, char_x, char_y, scale=1.0,
                    left_up=left_up, right_up=right_up)
    else:
        draw_stickwoman(screen, char_x, char_y, scale=1.0,
                        left_up=left_up, right_up=right_up)


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()


# === CONTINUE GAME CODE HERE ===
# Paste your full game code exactly below this block
# Replace the punch handling section with this:
#
#     if punch_detected:
#         pos = ball_positions[punch_detected]
#         if pos is not None:
#             key = None
#             if punch_detected == 'orange':
#                 key = pygame.K_q if pos < 0.5 else pygame.K_w
#             elif punch_detected == 'green':
#                 key = pygame.K_e if pos < 0.5 else pygame.K_r
#
#             if key in KEY_COLOR_MAP:
#                 for balloon in balloons:
#                     if balloon['color'] == KEY_COLOR_MAP[key] and not balloon['burst']:
#                         balloon['burst'] = True
#                         if balloon['color'] in [DARK_ORANGE, DARK_GREEN]:
#                             score += 10
#                         else:
#                             score += 5
#                         break
#         punch_detected = None
#
# This way, your game remains untouched except for input triggers
