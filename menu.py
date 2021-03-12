import argparse
import os
import pygame
import pygame_menu

import detect
import classify
import kit_display


#teal = 25B6BB
color_teal = (37,182,187)
#CORAL = FF5E4D
color_coral = (255,94,77)
#CORAL_LIGHT = FFE2DE
color_coral_light = (255,226,222)
#GREY = E7E6E4
color_grey = (231,230,228)
color_black = (33,33,33)



def show_menu():
    menu.add_button('Image classifier', start_classifier).set_selected(True)
    menu.add_button('Object detector', start_detector)
    menu.add_button('Face detector', start_face_detector)
    menu.add_button('Quit', pygame_menu.events.EXIT)
    # Must redraw when returning from a model
    menu.draw(surface)
    pygame.display.flip()

def show_loading(label):
    menu.clear()
    menu.add_label("Loading " + label + "...",
                   font=pygame_menu.font.FONT_OPEN_SANS,
                   font_size=32, color=color_black, background_color=(255,255,255),
                   selected_color=color_black)
    menu.draw(surface)
    pygame.display.flip()

def start_classifier():
    print('Start classifier')
    show_loading("image classifier")
    menu.disable()
    classify.start()
    menu.enable()
    menu.clear()
    show_menu()
    
def start_detector():
    print('Start detector')
    show_loading("object detector")
    model = 'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
    labels = 'coco_labels.txt'
    menu.disable()
    detect.start(model, labels)
    menu.enable()
    menu.clear()
    show_menu()
    
def start_face_detector():
    print('Start face detector')
    show_loading("face detector")
    model = 'mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite'
    labels = 'coco_labels.txt'
    menu.disable()
    detect.start(model, labels)
    menu.enable()
    menu.clear()
    show_menu()
    

def quit():
    print('QUIT')

import digitalio
import board

buttonA = digitalio.DigitalInOut(board.D17)
buttonA.switch_to_input()
pad_up = digitalio.DigitalInOut(board.D23)
pad_up.switch_to_input()
pad_down = digitalio.DigitalInOut(board.D27)
pad_down.switch_to_input()
pad_up_hold = False
pad_down_hold = False
buttonA_hold = False
#event_apply = pygame.event.Event(pygame.KEYDOWN, key=

def joystick_listener():
    print('MENU LISTENER!')
    if not menu.is_enabled():
        return
    global pad_up_hold
    global pad_down_hold
    global buttonA_hold
    
    # The buttons are active low, so "not value" means it's pressed
    if not buttonA.value:
        print('MENU BUTTON')
        if not buttonA_hold:
            menu.get_selected_widget().apply()
            buttonA_hold = True
    else:
        buttonA_hold = False
        
        
    if not pad_up.value: 
        print('MENU UP')
        if not pad_up_hold:
            menu._select(menu._index - 1)
            pad_up_hold = True
    else:
        pad_up_hold = False
        
    if not pad_down.value:
        print('MENU DOWN')
        if not pad_down_hold:
            menu._select(menu._index + 1)
            pad_down_hold = True
    else:
        pad_down_hold = False   


THEME_CORAL = pygame_menu.themes.Theme(
    background_color=(255, 255, 255),

    selection_color=(37,182,187),  # text and border color
    
    title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
    title_shadow=False,
    title_background_color=(62, 149, 195),
    title_font_color=(255,94,77),
    title_font_size=60,
    title_offset=(92,30),
    focus_background_color=(255,226,222,99),
    title_font=pygame_menu.font.FONT_OPEN_SANS,
    widget_font=pygame_menu.font.FONT_OPEN_SANS,
    widget_font_color=color_black,
    widget_font_size=42,
    menubar_close_button=False,
)



def main():
    global menu
    global surface
   # parser = argparse.ArgumentParser()
   # parser.add_argument('-f', help='Run the display at fullscreen',
   #                     action="store_true", default=False)
    #args = parser.parse_args()
   # print(args.f)
    
    pygame.init()
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    height = 480
    width = 480
    
    surface = kit_display.SharedDisplay(size=(width,height), fullscreen=True)
    args = None
    menu = pygame_menu.Menu(height,
                            width,
                            mouse_enabled=False,
                            mouse_visible=False,
                            theme=THEME_CORAL,
                            title='Coral AI kit')
    show_menu()
    menu.mainloop(surface, bgfun=joystick_listener)
    

if __name__ == '__main__':
    main()