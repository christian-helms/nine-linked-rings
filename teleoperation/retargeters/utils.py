from mediapipe.python.solutions.hands import HandLandmark

HAND_LANDMARK_TO_MANUS = {
    HandLandmark.WRIST: 'wrist',
    HandLandmark.THUMB_CMC: 'thumb_metacarpal',
    HandLandmark.THUMB_MCP: 'thumb_proximal',
    HandLandmark.THUMB_IP: 'thumb_distal',
    HandLandmark.THUMB_TIP: 'thumb_tip',
    HandLandmark.INDEX_FINGER_MCP: 'index_proximal',
    HandLandmark.INDEX_FINGER_PIP: 'index_intermediate',
    HandLandmark.INDEX_FINGER_DIP: 'index_distal',
    HandLandmark.INDEX_FINGER_TIP: 'index_tip',
    HandLandmark.MIDDLE_FINGER_MCP: 'middle_proximal',
    HandLandmark.MIDDLE_FINGER_PIP: 'middle_intermediate',
    HandLandmark.MIDDLE_FINGER_DIP: 'middle_distal',
    HandLandmark.MIDDLE_FINGER_TIP: 'middle_tip',
    HandLandmark.RING_FINGER_MCP: 'ring_proximal',
    HandLandmark.RING_FINGER_PIP: 'ring_intermediate',
    HandLandmark.RING_FINGER_DIP: 'ring_distal',
    HandLandmark.RING_FINGER_TIP: 'ring_tip',
    HandLandmark.PINKY_MCP: 'little_proximal',
    HandLandmark.PINKY_PIP: 'little_intermediate',
    HandLandmark.PINKY_DIP: 'little_distal',
    HandLandmark.PINKY_TIP: 'little_tip',
}

