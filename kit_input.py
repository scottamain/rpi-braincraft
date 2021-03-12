import digitalio
import board

EVENT_UP = 0
EVENT_DOWN = 1
EVENT_APPLY = 2

buttonA = digitalio.DigitalInOut(board.D17)
buttonA.switch_to_input()
pad_up = digitalio.DigitalInOut(board.D23)
pad_up.switch_to_input()
pad_down = digitalio.DigitalInOut(board.D27)
pad_down.switch_to_input()
pad_up_hold = False
pad_down_hold = False
#event_apply = pygame.event.Event(pygame.KEYDOWN, key=

def get_joystick_event():
    print('CHECK EVENT')
    global pad_up_hold
    global pad_down_hold
    # The buttons are active low, so "not value" means it's pressed
    if not buttonA.value:
        print('BUTTON')
        return EVENT_APPLY
        
    if not pad_up.value:  # just button A pressed
        print('UP')
        if not pad_up_hold:
            pad_up_hold = True
            return EVENT_UP
    else:
        pad_up_hold = False
        
    if not pad_down.value:
        print('DOWN')
        if not pad_down_hold:
            pad_down_hold = True
            return EVENT_DOWN
    else:
        pad_down_hold = False
    return None