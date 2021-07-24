#!/usr/bin/env python3
'''

Create an audio stream then call analysis functions on it


'''

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
from queue import Queue
from analysis import *
import params
import time
import threading
import env_data

import mysql.connector
from datetime import datetime
import re, subprocess

from mysql_credentials import jaguar_credentials



#-----------------------------------------------------------
#     Recording Stream

queue = Queue(maxsize=1)
env_queue = Queue(maxsize=1)

#emb = np.empty([0,1024],dtype = params.out_dtype) #Should initialize to fullsize for runtime eventually, fill with zeros
classes_and_indices = np.empty([params.blocks,8],dtype = params.out_dtype)


filename = "env" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
filenamedate = datetime.now().strftime("%Y_%m_%d")
#filename = "new" + filename

count = 0

def air(t, sep):
	env = env_data.env_av(t,sep)
	env_queue.put(env)


values = np.empty([params.blocks, 19], dtype = "float32")
indices = np.empty([params.blocks, 8], dtype = "float32")

try:

	def callback(indata, frames, time, status):
		queue.put(indata.copy())
	with sd.InputStream(channels=1, callback=callback, blocksize=int(params.seconds * params.samplerate), samplerate=params.samplerate):
		while count < params.blocks:
			thread = threading.Thread(target=air, args=(params.seconds, params.interval))
			thread.start()
			timestamp, bioindices, new_indices, _ = analysis(params.gain*queue.get(),params.samplerate)
			newdata = np.append(bioindices, new_indices)
			classes_and_indices[count] = newdata
			print(count*params.seconds/60, "minutes of audio")
			print(newdata)
			thread.join()
			envdata = env_queue.get(1)
			values[count] = envdata
			indices[count] = newdata
			print(envdata)

			count += 1
			#upload = threading.Thread(target=mysqlsend, args=(env_data,newdata))
			#upload.start()
		#np.save(params.save_directory + filename, )
		

		av = np.average(values, axis = 0)
		ind = np.average(indices, axis = 0)
		alldata = np.append(av, ind)
		try:
			savedata = np.load(params.save_directory + filenamedate + ".npy")
			savedata = np.vstack([savedata, alldata])
			print("updated")
		except FileNotFoundError:
			savedata = alldata
			print("new")
		np.save(params.save_directory + filenamedate + ".npy",savedata)
		print("updated and saved")
		print(savedata.shape)



		print("connecting...")
		db_connection = jaguar_credentials()
		my_database = db_connection.cursor()
		SQLquery = """INSERT INTO Environment (PM1std, PM25std, PM10std, PM1env, PM25env, PM10env, 3um, 5um, 10um, 25um, 50um, 100um, CO2, CO2Temp, CO2RH, 680Temp, 680VOC, 680RH, 680Pr, ACI, BI, AEI, ADI, NewACI, NewBI, NewAEI, NewADI) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
		insert_tuple = (float(av[0]), float(av[1]), float(av[2]), float(av[3]), float(av[4]), float(av[5]), float(0.0), float(av[7]), float(av[8]), float(av[9]), float(av[10]), float(av[11]), float(av[12]), float(av[13]), float(av[14]), float(av[15]), float(av[16]), float(av[17]), float(av[18]), float(ind[0]), float(ind[1]), float(ind[2]), float(ind[3]), float(ind[4]), float(ind[5]), float(ind[6]), float(ind[7]))
		my_database.execute(SQLquery, insert_tuple)
		print("ready...")
		db_connection.commit()
		

#-----------------------------------------------------------
#   Error handling

except KeyboardInterrupt:
#	displayoff()
	#print("\nwriting datafile...")
	#np.savez_compressed(params.save_directory + filename, embeddings=emb, scores_indices=classes_and_indices)
	print("done")
except Exception as e:
	print(type(e).__name__ + ': ' + str(e))
#	displayoff()
	print("\nquitting...")

print("sent")
