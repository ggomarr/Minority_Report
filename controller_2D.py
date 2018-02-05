'''
Created on Jan 22, 2016

@author: ggomarr
'''

#!/usr/bin/env python

#IMPORTS

import numpy as np
import freenect
import pygame
import math
from bisect import bisect
from datetime import datetime, timedelta
import dbus
import jsonrpclib

#FUNCTIONS

def rect_to_polar(rect_vect):
    modulus=math.sqrt(rect_vect[0]**2+rect_vect[1]**2)
    angle=math.atan2(rect_vect[1],rect_vect[0])
    if angle<0:
        angle=angle+2*math.pi
    return [modulus,angle]

def polar_to_rect(polar_vec):
    x=polar_vec[0]*math.cos(polar_vec[1])
    y=polar_vec[0]*math.sin(polar_vec[1])
    return [x,y]

def paint_controller(rect_vect):
    pygame.draw.circle(screen,BLUE,(rect_vect[0],rect_vect[1]),2)
    pygame.draw.circle(screen,BLUE,(rect_vect[0],rect_vect[1]),r_small,2)
    pygame.draw.circle(screen,BLUE,(rect_vect[0],rect_vect[1]),r_medium,2)
    pygame.draw.circle(screen,BLUE,(rect_vect[0],rect_vect[1]),r_large,2)
    for limit in limits[action_set]:
        p1=polar_to_rect([r_medium,limit])
        p2=polar_to_rect([r_large,limit])
        pygame.draw.line(screen,BLUE,(rect_vect[0]+int(p1[0]),rect_vect[1]-int(p1[1])),(rect_vect[0]+int(p2[0]),rect_vect[1]-int(p2[1])),2)

def perform(action_set,action):
    if action_set==0:
        if action=="Play/Pause":
            banshee.PlayPause()
        elif action=="Next":
            banshee.Next()
        elif action=="Previous":
            banshee.Previous()
        elif action=="VolUp":
            volume=pm.Get(dbus_property_collection, 'Volume')
            goal_volume=min(1.0,volume+0.10)
            pm.Set(dbus_property_collection, 'Volume', dbus.Double(goal_volume, variant_level=1))
        elif action=="VolDown":
            volume=pm.Get(dbus_property_collection, 'Volume')
            goal_volume=max(0.0,volume-0.10)
            pm.Set(dbus_property_collection, 'Volume', dbus.Double(goal_volume, variant_level=1)) 
    elif action_set==1:
        if action=="Select":
            player=xbmc.Player.GetActivePlayers()
            if len(player)==0:
                xbmc.Input.Select()
            else:
                xbmc.Player.PlayPause(player[0]['playerid'])
        if action=="Up":
            xbmc.Input.Up()
        if action=="Down":
            xbmc.Input.Down()
        if action=="Left":
            xbmc.Input.Left()
        if action=="Right":
            xbmc.Input.Right()
        if action=="Back":
            player=xbmc.Player.GetActivePlayers()
            if len(player)==0:
                xbmc.Input.Back()
            else:
                xbmc.Player.Stop(player[0]['playerid'])

#BANSHEE

dbus_start_name='org.bansheeproject.Banshee'
#dbus_start_path='/org/bansheeproject/Banshee/PlayerEngine'
#dbus_control_name='org.mpris.MediaPlayer2.banshee'
dbus_control_path='/org/mpris/MediaPlayer2'
dbus_properties_name='org.freedesktop.DBus.Properties'
dbus_property_collection='org.mpris.MediaPlayer2.Player'

bus = dbus.SessionBus()
banshee=bus.get_object(dbus_start_name,dbus_control_path)
pm = dbus.Interface(banshee, dbus_properties_name)

opening_banshee=True
while opening_banshee:
    try:
        volume=pm.Get(dbus_property_collection, 'Volume')
        opening_banshee=False
    except dbus.exceptions.DBusException:
        opening_banshee=True

while volume==0:
    pm.Set(dbus_property_collection, 'Volume', dbus.Double(0.75, variant_level=1))
    volume=pm.Get(dbus_property_collection, 'Volume')

#XBMC

xbmc=jsonrpclib.Server('http://192.168.1.3:8080/jsonrpc')

#PYGAME

#RGB Color tuples
BLACK = (0,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)

pygame.init() #Initiates pygame
xSize,ySize = 640,480 #Sets size of window
screen = pygame.display.set_mode((xSize,ySize),pygame.RESIZABLE) #creates main surface

#KINECT

depth_raw=None

num_to_track=1000 #Number of points to use to determine where the closest 'thing' is
x_grid,y_grid=np.ogrid[0:xSize,0:ySize]

ctx=freenect.init() #Start up the kinect
dev=freenect.open_device(ctx,freenect.LED_OFF) #Pointer to the device itself used for led handling
freenect.set_led(dev,0) #Turn led off
freenect.close_device(dev) #Release the kinect

#CONTROLLER

r_small=15
r_medium=75
r_large=125

r_central_button=50
z_main_action=50
z_switch_controller=50

huge_motion_limit=40
active_area_limit=50
exclusion_zone_limit=50

hold_it_limit=timedelta(0,1)
action_less_limit=timedelta(0,3)
center_setting_limit=timedelta(0,2)

hold_it=False
center_set=False
active_area=False
exclusion_zone=False
trying_to_set_center=False

old_xy=[xSize/2,ySize/2]
exclusion_xy=[xSize/2,ySize/2]
center_xy=[xSize/2,ySize/2]
center_z=0

limits=[[a*math.pi for a in [0.25,0.75,1.25,1.75]],
        [b*math.pi for b in [0.25,0.625,0.875,1.25,1.75]],
        [c*math.pi for c in [0.5,1.5]]]
actions=[['Next', 'VolUp', 'Previous', 'VolDown', 'Next', 'Play/Pause', 'Banshee'],
         ['Right', 'Up', 'Back', 'Left', 'Down', 'Right', 'Select', 'XBMC'],
         ['HAM','EGG','HAM', 'Bulls eye', 'EGG & HAM']
        ]
action_is_digital=[[True, False, True, False, True, True, True],
                   [True, True, True, True, True, True, True],
                   [True, True, True, True, True]]
leds=[[freenect.LED_BLINK_GREEN,freenect.LED_GREEN,freenect.LED_RED],
      [freenect.LED_BLINK_GREEN,freenect.LED_RED,freenect.LED_GREEN],
      [freenect.LED_GREEN,freenect.LED_RED,freenect.LED_OFF]]
action_set=0
action_num=None

#MAIN LOOP

ts=0
old_ts=ts

def process_depth(dev,data,timestamp):
    global depth_raw, ts
    depth_raw=data
    ts=timestamp

def body(dev,ctx):
    global hold_it_start, action_less_start, setting_center_start
    global hold_it, center_set, active_area, exclusion_zone, trying_to_set_center
    global old_ts, old_xy, center_xy, center_z, exclusion_xy
    global action_set, action_num

    if ts<>old_ts:

        #pygame and freenect use different indexing and origin
        depth=np.flipud(depth_raw.transpose())
        #eliminate low objects
        #depth[:,240:]=2047

        if active_area:
            mask=(x_grid-old_xy[0])**2+(y_grid-old_xy[1])**2>active_area_limit**2
            depth[mask]=2047

        depth_flat=depth.ravel()
        depth_flat=np.sort(depth_flat)
        itemindex=np.where(depth<=depth_flat[num_to_track])
        final_xy=[int(itemindex[0][:num_to_track].mean()),int(itemindex[1][:num_to_track].mean())]
        final_z=int(depth_flat[0:num_to_track].mean())

        dist_xy=rect_to_polar([final_xy[0]-old_xy[0],-(final_xy[1]-old_xy[1])])
        rel_xy=rect_to_polar([final_xy[0]-center_xy[0],-(final_xy[1]-center_xy[1])])
        rel_z=center_z-final_z

        rightnow=datetime.now()

        if dist_xy[0]>huge_motion_limit:
            hold_it=False
            center_set=False
            freenect.set_led(dev,freenect.LED_OFF) #Turn led off
            active_area=False
        elif center_set:
            if hold_it:
                if action_is_digital[action_set][action_num]:
                    if rightnow-hold_it_start>hold_it_limit:
                        if rel_xy[0]<r_medium:
                            hold_it=False
                            freenect.set_led(dev,leds[action_set][1])
                            action_less_start=rightnow
                        elif rel_xy[0]>r_medium and rel_xy[0]<r_large:
                            hold_it=False
                            action_less_start=rightnow
                        else:
                            hold_it=False
                            center_set=False
                            freenect.set_led(dev,freenect.LED_OFF) #Turn led off
                            active_area=False
                else:
                    if rel_xy[0]<r_medium:
                        hold_it=False
                        freenect.set_led(dev,leds[action_set][1])
                        action_less_start=rightnow
                    elif rel_xy[0]>r_medium and rel_xy[0]<r_large:
                        if action_num==bisect(limits[action_set],rel_xy[1]) and rightnow-hold_it_start>hold_it_limit:
                            perform(action_set,actions[action_set][action_num])
                        else:
                            hold_it=False
                            action_less_start=rightnow
                    else:
                        hold_it=False
                        center_set=False
                        freenect.set_led(dev,freenect.LED_OFF) #Turn led off
                        active_area=False
#   elif rel_z<-z_switch_controller and dist_xy[0]<r_central_button:
#    action_num=-1
#    action_set=action_set+1
#    if action_set==len(actions):
#     action_set=0
#    freenect.set_led(dev,leds[action_set][1])
#    hold_it=True
#    hold_it_start=rightnow
            elif rel_z>z_main_action and dist_xy[0]<r_central_button:
                action_num=-2
                perform(action_set,actions[action_set][action_num])
                hold_it=True
                hold_it_start=rightnow
            elif rel_xy[0]>r_medium:
                action_num=bisect(limits[action_set],rel_xy[1])
                freenect.set_led(dev,leds[action_set][2])
                perform(action_set,actions[action_set][action_num])
                hold_it=True
                hold_it_start=rightnow
            elif rightnow-action_less_start>action_less_limit:
                center_set=False
                freenect.set_led(dev,freenect.LED_OFF) #Turn led off
                exclusion_zone=True
                exclusion_xy=final_xy
                active_area=False
        elif trying_to_set_center:
            if rightnow-setting_center_start>center_setting_limit:
                trying_to_set_center=False
                center_set=True
                freenect.set_led(dev,leds[action_set][1]) #Turn led solid
                active_area=True
                center_xy=final_xy
                center_z=final_z
                action_less_start=rightnow
            elif dist_xy[0]>r_small:
                trying_to_set_center=False
                freenect.set_led(dev,freenect.LED_OFF) #Turn led off
        elif dist_xy[0]<r_small:
            if (not exclusion_zone) or (rect_to_polar([final_xy[0]-exclusion_xy[0],final_xy[1]-exclusion_xy[1]])[0]>exclusion_zone_limit):
                trying_to_set_center=True
                freenect.set_led(dev,leds[action_set][0]) #Turn led blinking
                setting_center_start=rightnow
                exclusion_zone=False

        old_xy=final_xy
        old_ts=ts

        #PAINTING

        screen.fill(BLACK) #Make the window black
        pygame.draw.circle(screen,(255,min(255,max(0,255*(1000.0-final_z)/500)),0),(final_xy[0],final_xy[1]),10)
        if center_set:
            paint_controller(center_xy)
        if active_area:
            pygame.draw.circle(screen,YELLOW,(old_xy[0],old_xy[1]),active_area_limit,2)
        if exclusion_zone:
            pygame.draw.circle(screen,RED,(exclusion_xy[0],exclusion_xy[1]),exclusion_zone_limit,2)
        font = pygame.font.Font(None, 48)
        if hold_it:
            ftext=actions[action_set][action_num]+"! Holding for "+str((rightnow-hold_it_start).seconds)+" / "+str(hold_it_limit.seconds)
        elif center_set:
            ftext="Set for "+str((rightnow-action_less_start).seconds)+" / "+str(action_less_limit.seconds)+" "+str(int(rel_xy[0]))+" / "+str(r_medium)
        elif trying_to_set_center:
            ftext="Trying for "+str((rightnow-setting_center_start).seconds)+" / "+str(center_setting_limit.seconds)
        else:
            ftext="Searching..."

        text = font.render(ftext,1,YELLOW)
        screen.blit(text, (20,20))

        screen.blit(screen,(0,0)) #Updates the main screen --> screen
        pygame.display.flip() #Updates everything on the window

        for e in pygame.event.get(): #Iterates through current events
            if e.type is pygame.QUIT: #If the close button is pressed, the while loop ends
                raise freenect.Kill

freenect.runloop(depth=process_depth,
                 body=body)