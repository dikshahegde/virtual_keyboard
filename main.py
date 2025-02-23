import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import subprocess
import pygetwindow as gw
import time

# Initialize MediaPipe Hand model
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Define a real keyboard layout
keyboard_layout = [
    ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'],
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
    ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
    ['Caps', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', '\'', 'Enter'],
    ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Shift'],
    ['Ctrl', 'Alt', 'Space', 'Alt', 'Ctrl']
]

# Keyboard layout positioning
key_width, key_height = 60, 60
start_x, start_y = 50, 200  

# Track double-tap state
last_tap_time = 0
double_tap_threshold = 0.3  # 300ms for double-tap
last_tapped_key = None

def get_key_from_position(finger_x, finger_y):
    """Map finger position to the keyboard layout"""
    row_index = (finger_y - start_y) // key_height
    col_index = (finger_x - start_x) // key_width
    
    if 0 <= row_index < len(keyboard_layout) and 0 <= col_index < len(keyboard_layout[row_index]):
        return keyboard_layout[row_index][col_index]
    return None

# Open Notepad and wait for it to load
notepad_process = subprocess.Popen("notepad.exe")
time.sleep(2)

def focus_notepad():
    """Ensure Notepad is active before typing"""
    notepad_window = gw.getWindowsWithTitle("Untitled - Notepad")
    if notepad_window:
        notepad_window[0].activate()

# Focus Notepad before starting
focus_notepad()

# Start webcam
cap = cv2.VideoCapture(0)
cap.set(3,1280)
cap.set(4,720)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)  # Flip horizontally
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    # Draw keyboard layout
    for i, row in enumerate(keyboard_layout):
        for j, key in enumerate(row):
            x, y = start_x + j * key_width, start_y + i * key_height
            cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (255, 255, 255), 2)  # Transparent white border
            cv2.putText(frame, key, (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Detect hand landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get index finger and thumb positions
            index_finger_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            
            # Convert to pixel coordinates
            finger_x, finger_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
            thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)

            # Calculate distance between index finger and thumb
            distance = np.linalg.norm(np.array([finger_x, finger_y]) - np.array([thumb_x, thumb_y]))
            
            # Detect double-tap
            key_pressed = get_key_from_position(finger_x, finger_y)
            current_time = time.time()

            if distance < 30 and key_pressed:
                if key_pressed == last_tapped_key and (current_time - last_tap_time) < double_tap_threshold:
                    focus_notepad()  # Ensure Notepad is active before typing
                    
                    # Handle special keys
                    if key_pressed == "Space":
                        pyautogui.write(" ")
                    elif key_pressed == "Backspace":
                        pyautogui.press("backspace")
                    elif key_pressed == "Enter":
                        pyautogui.press("enter")
                    else:
                        pyautogui.write(key_pressed.lower())

                    last_tapped_key = None  # Reset after typing
                else:
                    last_tapped_key = key_pressed
                    last_tap_time = current_time

    cv2.imshow("Virtual Keyboard", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
