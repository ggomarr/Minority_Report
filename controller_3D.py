'''
Created on Jan 22, 2016

@author: ggomarr
'''

#!/usr/bin/env python

#IMPORTS
import freenect
import numpy as np
import cv, cv2  
import pygame
import visual

#PARAMETERS
#  POINTS BEING TRACKED
num_to_track=500
#  DISPLAYS
display_bg=False #Display background
display_fg=False #Display foreground
display_pygame=True #Display pygame
display_visual=True #Display visual 3D; does not work together with fg or bg!
#    CV
cv_size=(480,640)
#    PYGAME
BLACK = (0,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)
py_size=(640,480)
#    VISUAL
vi_size=(640,480)
grid=[[1,0,1,0,1,0,1],
      [0,1,0,1,0,1,0],
      [1,0,1,0,1,0,1],
      [0,1,0,1,0,1,0],
      [1,0,1,0,1,0,1],
      [0,1,0,1,0,1,0],
      [1,0,1,0,1,0,1]]
tile_size=100
tile_thk=0.1
offset=-600
b_radius=50
b_opacity=0.5
s_center=(320,240,0)
s_forward=(0,0.1,1)
s_up=(0,-1,0)
s_range=(500,500,500)
#  MEDIAN BLUR
apply_median_blur=True
median_blur_k=3 #Median blur kernel radius
#  SUBSTRACT BACKGROUND
subtract_bg=True
init_bg=50 #Frames to initialize background image
sigma_bg=20 #Distance from background to consider foreground
#    ADAPTATIVE BACKGROUND
adaptative_bg=True #Learn background continuously
adoption_rate=0.0001 #Rate of learning
#    ERODE AND DILATE
erode_n_dilate=True #Erode and dilate background mask
erode_num=15 #Erode steps
erode_k=3 #Erode kernel radius
dilate_num=25 #Dilate steps
dilate_k=3 #Dilate kernel radius

#INITIALIZING
#  BACKGROUND IMAGE
bg=np.zeros(cv_size,np.float32)
for i in range(init_bg):
    if apply_median_blur:
        bg=bg+cv2.medianBlur(freenect.sync_get_depth()[0],median_blur_k)/init_bg
    else:
        bg=bg+freenect.sync_get_depth()[0]/init_bg
#  BACKGROUND SUBSTRACTION MASKS
fg_mask=np.zeros(cv_size,np.uint8)
lower_b=np.zeros(cv_size,np.uint16)
upper_b=np.ones(cv_size,np.uint16)*2047
#  ERODE AND DILATE KERNELS
erode_kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(erode_k,erode_k),(-1,-1))
dilate_kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(dilate_k,dilate_k),(-1,-1))
#  PYGAME
if display_pygame:
    pygame.init()
    screen=pygame.display.set_mode(py_size,pygame.RESIZABLE)
#  VISUAL
if display_visual:
    rows = len(grid)
    cols = len(grid[0]) 
    for row in range(rows):      
        for col in range(cols):
            if grid[row][col] == 1:
                visual.box(pos=(col*tile_size,vi_size[1],row*tile_size+offset),size=(tile_size,tile_thk,tile_size))
    ball=visual.sphere(radius=b_radius, pos=(vi_size[0]/2,vi_size[1]/2,offset), color=visual.color.yellow, opacity=b_opacity)
    visual.scene.autoscale=False
    visual.scene.center=s_center
    visual.scene.forward=s_forward
    visual.scene.up=s_up
    visual.scene.range=s_range

#LOOP
cflag=True
while cflag:

#SENSE
    if apply_median_blur:
        depth=cv2.medianBlur(freenect.sync_get_depth()[0],median_blur_k)
    else:
        depth=freenect.sync_get_depth()[0]

#PROCESS ijd
    if subtract_bg:
        if adaptative_bg:
            cv2.accumulateWeighted(depth,bg,adoption_rate)
        upper_b=bg.astype(np.uint16)-sigma_bg
        cv2.inRange(depth,lower_b,upper_b,fg_mask)
        fg_mask=fg_mask/255
        if erode_n_dilate:
            cv2.erode(fg_mask,erode_kernel,fg_mask,(-1,-1),erode_num)
            cv2.dilate(fg_mask,dilate_kernel,fg_mask,(-1,-1),dilate_num)
        depth=np.maximum(depth,np.logical_not(fg_mask)*2047)

    if np.count_nonzero(depth-2047)>num_to_track:
        depth_flat=depth.ravel()
        depth_flat=np.sort(depth_flat)
        itemindex=np.where(depth<=depth_flat[num_to_track])
        sensed_a=int(itemindex[0][:num_to_track].mean())
        sensed_b=int(itemindex[1][:num_to_track].mean())
        sensed_c=int(depth_flat[0:num_to_track].mean())
    else:
        sensed_a=cv_size[0]/2
        sensed_b=cv_size[1]/2
        sensed_c=500

#ACTIONS

#DISPLAY
    key=-1
    if display_bg:
        bgimg=bg/8.
        cv2.imshow('BG',bgimg.astype(np.uint8))
        key=cv2.waitKey(5)
    if display_fg:
        fgimg=depth/8.
        center_cv=(sensed_b,sensed_a)
        cv2.circle(fgimg, center_cv, 5, 0, -1)
        cv2.imshow('FG',fgimg.astype(np.uint8))
        key=cv2.waitKey(5)
    if display_pygame:
        screen.fill(BLACK)
        pygame.draw.circle(screen,(255,min(255,max(0,255*(1000.0-sensed_c)/500)),0),(sensed_b,sensed_a),5)
        screen.blit(screen,(0,0))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type is pygame.QUIT:
                key=0
    if display_visual:
        ball.pos=(sensed_b,sensed_a,sensed_c)

    if key!=-1:
        cflag=False