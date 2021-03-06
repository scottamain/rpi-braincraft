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

"""A demo to run the detector in a Pygame camera stream."""
import argparse
import collections
from collections import deque
import common
import io
import numpy as np
import os
import pathlib
import pygame
import pygame.camera
from pygame.locals import *
import re
import sys
import tflite_runtime.interpreter as tflite
import time

import menu
import kit_display
import kit_input

Object = collections.namedtuple('Object', ['id', 'score', 'bbox'])

def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

def input_tensor(interpreter):
    """Returns input tensor view as numpy array of shape (height, width, 3)."""
    tensor_index = interpreter.get_input_details()[0]['index']
    return interpreter.tensor(tensor_index)()[0]

def set_interpreter(interpreter, data):
    input_tensor(interpreter)[:,:] = np.reshape(data, (common.input_image_size(interpreter)))
    interpreter.invoke()

class BBox(collections.namedtuple('BBox', ['xmin', 'ymin', 'xmax', 'ymax'])):
    """Bounding box.
    Represents a rectangle which sides are either vertical or horizontal, parallel
    to the x or y axis.
    """
    __slots__ = ()

def get_output(interpreter, score_threshold, top_k, image_scale=1.0):
    """Returns list of detected objects."""
    boxes = common.output_tensor(interpreter, 0)
    class_ids = common.output_tensor(interpreter, 1)
    scores = common.output_tensor(interpreter, 2)

    def make(i):
        ymin, xmin, ymax, xmax = boxes[i]
        return Object(
            id=int(class_ids[i]),
            score=scores[i],
            bbox=BBox(xmin=np.maximum(0.0, xmin),
                      ymin=np.maximum(0.0, ymin),
                      xmax=np.minimum(1.0, xmax),
                      ymax=np.minimum(1.0, ymax)))

    return [make(i) for i in range(top_k) if scores[i] >= score_threshold]


def main():
    script_dir = pathlib.Path(__file__).parent.absolute()
    default_model_dir = os.path.join(script_dir, 'models')
    default_model = 'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
    default_labels = 'coco_labels.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    parser.add_argument('--top_k', type=int, default=5,
                        help='number of categories with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='classifier score threshold')
    args = parser.parse_args()
    start(args.model, args.labels, args.top_k)

def start(model, labels, top_k=5, threshold=0.5):
    script_dir = pathlib.Path(__file__).parent.absolute()
    model_dir = os.path.join(script_dir, 'models')
    model = os.path.join(model_dir, model)
    labels = os.path.join(model_dir, labels)

    face_detector = True if "face" in model else False
    
    cam_w, cam_h = 480, 480

    interpreter = common.make_interpreter(model)
    interpreter.allocate_tensors()
    labels = load_labels(labels)

    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 50)

    pygame.camera.init()
    camlist = pygame.camera.list_cameras()

    w, h, _ = common.input_image_size(interpreter)

    print('By default using camera: ', camlist[0])
    camera = pygame.camera.Camera(camlist[0], (cam_w, cam_h))
    try:
      display = kit_display.SharedDisplay()
    except pygame.error as e:
      sys.stderr.write("\nERROR: Unable to open a display window. Make sure a monitor is attached and that "
            "the DISPLAY environment variable is set. Example: \n"
            ">export DISPLAY=\":0\" \n")
      raise e

    red = pygame.Color(255, 0, 0)

    camera.start()
    stop = False
    try:
        last_time = time.monotonic()
        while not stop:
            mysurface = camera.get_image()
            imagen = pygame.transform.scale(mysurface, (w, h))
            input = np.frombuffer(imagen.get_buffer(), dtype=np.uint8)
            start_time = time.monotonic()
            common.input_tensor(interpreter)[:,:] = np.reshape(input, (common.input_image_size(interpreter)))
            interpreter.invoke()
            results = get_output(interpreter, score_threshold=threshold, top_k=top_k)
            stop_time = time.monotonic()
            inference_ms = (stop_time - start_time)*1000.0
            fps_ms = 1.0 / (stop_time - last_time)
            last_time = stop_time
#            annotate_text = 'Inference: {:5.2f}ms FPS: {:3.1f}'.format(inference_ms, fps_ms)

            annotate_text = 'FPS: {:3.1f}'.format(inference_ms, fps_ms)
            for result in results:
               x0, y0, x1, y1 = list(result.bbox)
               rect = pygame.Rect(x0 * cam_w, y0 * cam_h, (x1 - x0) * cam_w, (y1 - y0) * cam_h)
               pygame.draw.rect(mysurface, red, rect, 8)
               label = '{:.0f}% {}'.format(100*result.score, labels.get(result.id, result.id))
               text = font.render(label, True, red)
               print(label, ' ', end='')
               if not face_detector:
                   mysurface.blit(text, (x0 * cam_w , y0 * cam_h))
            text = font.render(annotate_text, True, red)
            print(annotate_text)
            #mysurface.blit(text, (0, 0))
            display.blit(mysurface, (0, 0))
            pygame.display.flip()
            
            for event in pygame.event.get():
              if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                stop = True
            if kit_input.get_joystick_event() == kit_input.EVENT_APPLY:
                stop = True
    finally:
        camera.stop()


if __name__ == '__main__':
    main()
