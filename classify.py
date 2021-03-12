#    Copyright 2019 Google LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        https://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""A demo to classify Pygame camera stream."""
import argparse
import collections
from collections import deque
import common
import io
import numpy as np
import operator
import os
import pathlib
import pygame
import pygame.camera
from pygame.locals import *
import tflite_runtime.interpreter as tflite
import time

import menu
import kit_display
import kit_input

Category = collections.namedtuple('Category', ['id', 'score'])
restore_menu = False

def input_tensor(interpreter):
    """Returns input tensor view as numpy array of shape (height, width, 3)."""
    tensor_index = interpreter.get_input_details()[0]['index']
    return interpreter.tensor(tensor_index)()[0]

def get_output(interpreter, top_k, score_threshold):
    """Returns no more than top_k categories with score >= score_threshold."""
    scores = common.output_tensor(interpreter, 0)
    categories = [
        Category(i, scores[i])
        for i in np.argpartition(scores, -top_k)[-top_k:]
        if scores[i] >= score_threshold
    ]
    return sorted(categories, key=operator.itemgetter(1), reverse=True)

class Capture(object):
    pygame.font.init()
    
    def __init__(self):
        self.size = (480,480)
        self.font = pygame.font.Font(None, 48)
        # create a display surface. standard pygame stuff
        self.display = kit_display.SharedDisplay()

        # this is the same as what we saw before
        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError("Sorry, no cameras detected.")
        self.cam = pygame.camera.Camera(self.clist[0], self.size)
        self.cam.start()

        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshot = pygame.surface.Surface(self.size, 0, self.display)

    def get_and_flip(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        self.snapshot = self.cam.get_image()

        # blit it to the display surface.  simple!
        self.display.blit(self.snapshot, (0,0))
        pygame.display.flip()
        return self.snapshot

    def get(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        self.snapshot = self.cam.get_image()
        return self.snapshot

    def flip(self, label="No label"):     
        self.display.blit(self.snapshot, (0,0))
        
        text_surface = self.font.render(label, True, (255,0,0))
        text_position = (self.display.get_width()/2 ,
                         self.display.get_height() - self.font.size(label)[1])
        
        self.display.blit(text_surface, text_surface.get_rect(center=text_position))
        pygame.display.flip()
        
    def stop(self):
        self.cam.stop();
        print('camera stopped');

def start():
    restore_menu = True
    main()

def main():
    script_dir = pathlib.Path(__file__).parent.absolute()
    default_model_dir = os.path.join(script_dir, 'models')
    default_model = 'mobilenet_v2_1.0_224_quant_edgetpu.tflite'
    default_labels = 'imagenet_labels.txt'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    args = parser.parse_args()

    with open(args.labels, 'r') as f:
        pairs = (l.strip().split(maxsplit=1) for l in f.readlines())
        labels = dict((int(k), v) for k, v in pairs)

    interpreter = common.make_interpreter(args.model)
    interpreter.allocate_tensors()

    pygame.init()
    pygame.camera.init()
    camlist = pygame.camera.list_cameras()

    print('By default using camera: ', camlist[-1])
    size = (480, 480)
    
    #camera = pygame.camera.Camera(camlist[0], size)
    #surface = pygame.display.set_mode(size, 0)
    #surface.unlock()
    #snapshot = pygame.surface.Surface(size, 0, surface)
    
    capture = Capture()
    stop = False
    
    width, height, channels = common.input_image_size(interpreter)
    #camera.start()
    try:
        fps = deque(maxlen=20)
        fps.append(time.time())
        while not stop:
            #snapshot = camera.get_image()
            snapshot = capture.get()
            imagen = pygame.transform.scale(snapshot, (width, height))
            input = np.frombuffer(imagen.get_buffer(), dtype=np.uint8)
            start_ms = time.time()
            common.input_tensor(interpreter)[:,:] = np.reshape(input, (common.input_image_size(interpreter)))
            interpreter.invoke()
            results = get_output(interpreter, top_k=3, score_threshold=0)
            inference_ms = (time.time() - start_ms)*1000.0
            fps.append(time.time())
            fps_ms = len(fps)/(fps[-1] - fps[0])
            annotate_text = 'Inference: {:5.2f}ms FPS: {:3.1f}'.format(inference_ms, fps_ms)
            for result in results:
               annotate_text += '\n{:.0f}% {}'.format(100*result[1], labels[result[0]])
            print(annotate_text)
            capture.flip(labels[results[0][0]])
#             capture.flip("okay")
            
            for event in pygame.event.get():
              if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                stop = True
            if kit_input.get_joystick_event() == kit_input.EVENT_APPLY:
                stop = True
    finally:
        capture.stop()
            


if __name__ == '__main__':
    main()
