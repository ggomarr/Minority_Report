#!/usr/bin/env python
import numpy as np
from freenect import sync_get_depth as get_depth
import pygame
import random
import math
from datetime import datetime

#RGB Color tuples
BLACK = (0,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)
pygame.init() #Initiates pygame
xSize,ySize = 640,480 #Sets size of window
screen = pygame.display.set_mode((xSize,ySize),pygame.RESIZABLE) #creates main surface

num_to_track=1000
num_of_particles=100
use_filter=True
max_v=25

v_xy=[0,0]
old_xy=[xSize/2,ySize/2]

v_noise=10
sense_noise=10

# Initialize particles
p=[[],[]]
for i in range(num_of_particles):
	p[0].append(random.random()*xSize)
	p[1].append(random.random()*ySize)

#Initialize counters to measure durations
avgtime1=datetime.now()
avg_cycle_s=0
loc_cycle_s=0
cycle_cnt=0
loc_cycle_s_list=30*[0]

#Initialize lists to control the quality of the signals
filtered_error_list=30*[0]
sensed_error_list=30*[0]
old_sensed_xy=[xSize/2,ySize/2]
f_err=0

done = False #Iterator boolean --> Tells program when to terminate
while not done:

	(depth,_)=get_depth()
	#depth[240:,:]=2047 #Filters low objects

	depth_flat=depth.ravel()
	depth_flat=np.sort(depth_flat)
	itemindex=np.where(depth<=depth_flat[num_to_track])
	sensed_x=xSize-int(itemindex[1][:num_to_track].mean())
	sensed_y=int(itemindex[0][:num_to_track].mean())
	sensed_z=int(depth_flat[0:num_to_track].mean())
	sensed_xy=[sensed_x,sensed_y]

	screen.fill(BLACK) #Make the window black

	loctime1=datetime.now() #Start counting for the inner cycle

	if use_filter:

		# motion update (prediction)
		p_aux=[[],[]]
		for i in range(num_of_particles):
			p_aux[0].append(p[0][i]+random.gauss(v_xy[0], v_noise))
			p_aux[1].append(p[1][i]+random.gauss(v_xy[1], v_noise))
		p=p_aux

		# measurement update
		w = []
		for i in range(num_of_particles):
			prob=( math.exp(-((p[0][i]-sensed_xy[0])**2)/(sense_noise**2)/2.0) / math.sqrt(2.0*math.pi*(sense_noise**2)) *
          math.exp(-((p[1][i]-sensed_xy[1])**2)/(sense_noise**2)/2.0) / math.sqrt(2.0*math.pi*(sense_noise**2)) )
			w.append(prob)

		# resampling
		p_aux=[[],[]]
		index=int(random.random()*num_of_particles)
		beta=0.0
		mw=2.0*max(w)
		for i in range(num_of_particles):
			beta += random.random()*mw
			while beta>w[index]:
				beta -= w[index]
				index=(index+1) % num_of_particles
			p_aux[0].append(p[0][index])
			p_aux[1].append(p[1][index])
		p=p_aux

		filtered_xy=[max(min(xSize,int(np.array(p[0]).mean())),0),max(min(ySize,int(np.array(p[1]).mean())),0)]
		v_xy=[filtered_xy[0]-old_xy[0],filtered_xy[1]-old_xy[1]]
		v_xy=[cmp(v_xy[0],0)*min(abs(v_xy[0]),max_v),cmp(v_xy[1],0)*min(abs(v_xy[1]),max_v)]

		#Compute errors
		filtered_error=math.sqrt((filtered_xy[0]-old_xy[0])**2+(filtered_xy[1]-old_xy[1])**2)
		filtered_error_list=filtered_error_list[1:]+[filtered_error]
		sensed_error=math.sqrt((sensed_xy[0]-old_sensed_xy[0])**2+(sensed_xy[1]-old_sensed_xy[1])**2)
		sensed_error_list=sensed_error_list[1:]+[sensed_error]

		old_xy=filtered_xy
		old_sensed_xy=sensed_xy

		final_xy=filtered_xy
	else:
		final_xy=sensed_xy

	#Compute the duration of the cycles
	cycle_cnt+=1
	loctime2=datetime.now()
	loc_ms_cycle=loctime2.microsecond-loctime1.microsecond
	loc_cycle_s_list=loc_cycle_s_list[1:]+[int(1.0/(loc_ms_cycle/1000000.0))]
	if (loctime2-avgtime1).seconds >= 1:
		avgtime1=loctime2
		avg_cycle_s=cycle_cnt
		cycle_cnt=0
		loc_cycle_s=int(np.array(loc_cycle_s_list).mean())
		f_err=int(np.array(filtered_error_list).mean())
		s_err=int(np.array(sensed_error_list).mean())

	pygame.draw.circle(screen,(255,min(255,255*(1000.0-sensed_z)/500),0),(final_xy[0],final_xy[1]),10)

	if pygame.font:
		font = pygame.font.Font(None, 48)
		if use_filter:
			ftext='ON'
		else:
			ftext='OFF'
		text = font.render(ftext, 1, BLUE)
		screen.blit(text, (20,20))

		ftext=str(loc_cycle_s)+" "+str(avg_cycle_s)
		text = font.render(ftext, 1, GREEN)
		screen.blit(text, (20,120))

		ftext=str(f_err)+" "+str(s_err)
		text = font.render(ftext, 1, YELLOW)
		screen.blit(text, (20,220))

	screen.blit(screen,(0,0)) #Updates the main screen --> screen
	pygame.display.flip() #Updates everything on the window

	for e in pygame.event.get(): #Itertates through current events
		if e.type is pygame.QUIT: #If the close button is pressed, the while loop ends
			done = True
		if e.type is pygame.KEYDOWN:
			if e.key == pygame.K_SPACE:
				use_filter = not use_filter
