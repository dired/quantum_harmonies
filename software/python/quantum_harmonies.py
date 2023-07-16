import paho.mqtt.client as mqtt
import json
import mido
import time
import sys
import math
from collections import deque
import rtmidi
midiout_1 = rtmidi.MidiOut()
midiout_2 = rtmidi.MidiOut()
midiout_3 = rtmidi.MidiOut()
midiout_4 = rtmidi.MidiOut()
available_ports = midiout_1.get_ports()

if available_ports:
    midiout_1.open_port(4)
    midiout_2.open_port(5)
    midiout_3.open_port(6)
    midiout_4.open_port(7)
def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

current_synth = 0
midiouts = [midiout_1,midiout_2,midiout_3,midiout_4]

midi_notes = {
    'theta': 1,
    'phi': 2,
    'lambda': 3,
    # left sliders
    'left_slider_n': 4,# 'valuesI': 0 # note
    'left_slider_amp': 5,# 'valuesI': 0 
    'left_slider_oct': 6,# 'valuesI': 0 # octave # 5 á [1-120]
    'left_slider_rate': 7,# 'valuesI': 0
    'left_slider_size': 8,# 'valuesI': 0
    'left_slider_overlap': 9,# 'valuesI': 0
    'left_slider_begin': 10,# 'valuesI': 0
    'left_slider_end': 11,# 'valuesI': 0
    'left_slider_modi': 12,# 'valuesI': 0
    'left_slider_harm': 13,# 'valuesI': 0
    'left_slider_depth': 14,# 'valuesI': 0
    'left_slider_reverb': 15,# 'valuesI': 0
    'left_slider_delay': 16,# 'valuesI': 0
    'left_slider_crush': 17,# 'valuesI': 0
    'left_slider_pan': 18,# 'valuesI': 0
    'left_slider_hicut': 19,# 'valuesI': 0
    'left_slider_locut': 20,# 'valuesI': 0
    # right sliders
    'right_slider_n': 21,# 'valuesI': 1 # note
    'right_slider_amp': 22,# 'valuesI': 1 
    'right_slider_oct': 23,# 'valuesI': 1 # octave
    'right_slider_rate': 24,# 'valuesI': 1
    'right_slider_size': 25,# 'valuesI': 1
    'right_slider_overlap': 26,# 'valuesI': 1
    'right_slider_begin': 27,# 'valuesI': 1
    'right_slider_end': 28,# 'valuesI': 1
    'right_slider_modi': 29,# 'valuesI': 1
    'right_slider_harm': 30,# 'valuesI': 1
    'right_slider_depth': 31,# 'valuesI': 1
    'right_slider_reverb': 32,# 'valuesI': 1
    'right_slider_delay': 33,# 'valuesI': 1
    'right_slider_crush': 34,# 'valuesI': 1
    'right_slider_pan': 35,# 'valuesI': 1
    'right_slider_hicut': 36,# 'valuesI': 1
    'right_slider_locut': 37,# 'valuesI': 1
    # env
    'env_a': 38,
    'env_d': 39,
    'env_s': 40,
    'env_r': 41,
    # modEnv
    'moda': 42,
    'modd': 43,
    'mods': 44,
    'modr': 45,
    # TODO: presets
    'preset0': 46,
    'preset1': 47,
    'preset2': 48,
    'preset3': 49,
    'preset4': 50,
    'preset5': 51,
    'preset6': 52,
    'preset7': 53,
    # Actions
    'play': 54,
    'measure': 55,
    'randomise': 56,
    'config': 57,
    'volume': 58,
}
def midi_note(parameter,value,debug=False):
    global midi_notes
    base_note = [176, 0, 0]
    base_note[1] = midi_notes[parameter]
    base_note[2] = value
    if(debug):
        print("Sending parameter",parameter,base_note[1],"with Value:",base_note[2])
    return base_note


quantized_notes = {
   "generic_scalescale": [0]
}

timestamps = []

group_properties = {
   "q0_pulses": 0,
   "q0_freqs": [0,0], # index in midi_notes_octaves
   "q0_freqs_set": [False,False],
   "q0_playing": False,
   "q0_inclinations": [0,0,0],
   "q0_measured": False,
   "q0_collapsed_result": 0,
   "q1_pulses": 0,
   "q1_freqs": [0,0],
   "q1_freqs_set": [False,False],
   "q1_playing": False,
   "q1_inclinations": [0,0,0],
   "q1_measured": False,
   "q1_collapsed_result": 0,
   "q2_pulses": 0,
   "q2_freqs": [0,0],
   "q2_freqs_set": [False,False],
   "q2_playing": False,
   "q2_inclinations": [0,0,0],
   "q2_measured": False,
   "q2_collapsed_result": 0,
   "q3_pulses": 0,
   "q3_freqs": [0,0],
   "q3_freqs_set": [False,False],
   "q3_playing": False,
   "q3_inclinations": [0,0,0],
   "q3_measured": False,
   "q3_collapsed_result": 0,
}
recorded_durations = [] 
own_durations = []
def sort_into_pulse_durations(duration):
  global recorded_durations
  recorded_durations.append(duration)
  recorded_durations.sort(reverse=True)
  for i, duration_value in enumerate(recorded_durations):
    if duration_value == duration:
      return i

sievert_averages = []
initial_significance_level = 0.05#0.5#0.05
significance_level = 0.05#0.5#0.05
def calculate_sievert_average_diff(pulses, time_interval): # CPM*scale_factor
  global sievert_averages
  geiger_muller_tube_scale_factor = 0.00812
  time_scale_factor = (1000000*60)/time_interval
  pulses_per_minute = pulses * time_scale_factor
  average_sievert = pulses_per_minute*geiger_muller_tube_scale_factor 
  sievert_averages.append(average_sievert)
  diff = 0
  for average in sievert_averages:
     diff = diff + math.fabs(average - average_sievert)
  diff_average = diff/len(sievert_averages)
  if len(sievert_averages) == 1:
     return 1
  else:
    return diff_average  

material_half_lifes = [] # to know upper and lower limit to map to release and reverb
midi_notes_octaves = {'C0': [[176, 6, 1], [176, 4, 1]], 'D0': [[176, 6, 1], [176, 4, 19]], 'D#0': [[176, 6, 1], [176, 4, 37]], 'F0': [[176, 6, 1], [176, 4, 55]], 'G0': [[176, 6, 1], [176, 4, 74]], 'A0': [[176, 6, 1], [176, 4, 92]], 'B0': [[176, 6, 1], [176, 4, 110]], 'C1': [[176, 6, 31], [176, 4, 1]], 'D1': [[176, 6, 31], [176, 4, 19]], 'D#1': [[176, 6, 31], [176, 4, 37]], 'F1': [[176, 6, 31], [176, 4, 55]], 'G1': [[176, 6, 31], [176, 4, 74]], 'A1': [[176, 6, 31], [176, 4, 92]], 'B1': [[176, 6, 31], [176, 4, 110]], 'C2': [[176, 6, 61], [176, 4, 1]], 'D2': [[176, 6, 61], [176, 4, 19]], 'D#2': [[176, 6, 61], [176, 4, 37]], 'F2': [[176, 6, 61], [176, 4, 55]], 'G2': [[176, 6, 61], [176, 4, 74]], 'A2': [[176, 6, 61], [176, 4, 92]], 'B2': [[176, 6, 61], [176, 4, 110]], 'C3': [[176, 6, 91], [176, 4, 1]], 'D3': [[176, 6, 91], [176, 4, 19]], 'D#3': [[176, 6, 91], [176, 4, 37]], 'F3': [[176, 6, 91], [176, 4, 55]], 'G3': [[176, 6, 91], [176, 4, 74]], 'A3': [[176, 6, 91], [176, 4, 92]], 'B3': [[176, 6, 91], [176, 4, 110]], 'C4': [[176, 6, 121], [176, 4, 1]], 'D4': [[176, 6, 121], [176, 4, 19]], 'D#4': [[176, 6, 121], [176, 4, 37]], 'F4': [[176, 6, 121], [176, 4, 55]], 'G4': [[176, 6, 121], [176, 4, 74]], 'A4': [[176, 6, 121], [176, 4, 92]], 'B4': [[176, 6, 121], [176, 4, 110]]}

def reset():
  for midiout in midiouts:
    midiout.send_message(midi_note('left_slider_modi',1))
    midiout.send_message(midi_note('left_slider_harm',1))
    midiout.send_message(midi_note('right_slider_modi',1))
    midiout.send_message(midi_note('right_slider_harm',1))
    midiout.send_message(midi_note('left_slider_amp',120))
    midiout.send_message(midi_note('right_slider_amp',120))
    midiout.send_message(midi_note('right_slider_reverb',64))
    midiout.send_message(midi_note('right_slider_delay',64))
    midiout.send_message(midi_note('left_slider_reverb',64))
    midiout.send_message(midi_note('left_slider_delay',64))

chord_factor = 2
def get_new_lowest_frequency(index_in_midi_notes_octaves):
  global midi_notes_octaves, group_properties, chord_factor
  index_is_taken = False
  first_index = 0
  first_index_set = False
  for i in range(4):
    for j in range(2):
      if group_properties['q'+str(i)+'_freqs_set'][j]:
        if group_properties['q'+str(i)+"_freqs"][j] == index_in_midi_notes_octaves:
          if group_properties['q'+str(i)+"_measured"]:
            if group_properties['q'+str(i)+"_measured"] == j:
              index_is_taken = True
        if not first_index_set:
          first_index = group_properties['q'+str(i)+"_freqs"][j]
        first_index_set = True
  if index_is_taken == True:
    index_in_midi_notes_octaves = index_in_midi_notes_octaves+chord_factor #third
    if chord_factor == 2:
      chord_factor = 5
    else:
      chord_factor = 2
  else:
    amounts_of_indices_between_frequencies = 0
    if (first_index > index_in_midi_notes_octaves):
      amounts_of_indices_between_frequencies = first_index-index_in_midi_notes_octaves
    else:
      amounts_of_indices_between_frequencies = index_in_midi_notes_octaves-first_index
    if (amounts_of_indices_between_frequencies%3)==0 or (amounts_of_indices_between_frequencies%3)==0:
      return index_in_midi_notes_octaves
    else:
      if (first_index > index_in_midi_notes_octaves):
        index_in_midi_notes_octaves = index_in_midi_notes_octaves+1
      else:
        index_in_midi_notes_octaves = index_in_midi_notes_octaves-1
  while (index_is_taken == True):
    index_is_taken = False
    for i in range(4):
      for j in range(2):
        if group_properties['q'+str(i)+'_freqs_set'][j]:
          if group_properties['q'+str(i)+"_freqs"][j] == index_in_midi_notes_octaves:
            if group_properties['q'+str(i)+"_measured"]:
              if group_properties['q'+str(i)+"_measured"] == j:
                index_is_taken = True
    if index_is_taken == True:
      index_in_midi_notes_octaves = index_in_midi_notes_octaves+chord_factor #third
      if chord_factor == 2:
        chord_factor = 5
      else:
        chord_factor = 2    
    # converges to an untaken note in a musical chord
  return index_in_midi_notes_octaves

def get_new_highest_frequency(index_in_midi_notes_octaves):
  global midi_notes_octaves, group_properties, chord_factor
  index_is_taken = False
  first_index = 0
  first_index_set = False
  for i in range(4):
    for j in range(2):
      if group_properties['q'+str(i)+'_freqs_set'][j]:
        if group_properties['q'+str(i)+"_freqs"][j] == index_in_midi_notes_octaves:
          if group_properties['q'+str(i)+"_measured"]:
            if group_properties['q'+str(i)+"_measured"] == j:
              index_is_taken = True
        if not first_index_set:
          first_index = group_properties['q'+str(i)+"_freqs"][j]
        first_index_set = True
  if index_is_taken == True:
    index_in_midi_notes_octaves = index_in_midi_notes_octaves-chord_factor #third
    if chord_factor == 2:
      chord_factor = 5
    else:
      chord_factor = 2
  else:
    amounts_of_indices_between_frequencies = 0
    if (first_index > index_in_midi_notes_octaves):
      amounts_of_indices_between_frequencies = first_index-index_in_midi_notes_octaves
    else:
      amounts_of_indices_between_frequencies = index_in_midi_notes_octaves-first_index
    if (amounts_of_indices_between_frequencies%3)==0 or (amounts_of_indices_between_frequencies%3)==0:
      return index_in_midi_notes_octaves
    else:
      if (first_index > index_in_midi_notes_octaves):
        index_in_midi_notes_octaves = index_in_midi_notes_octaves+1
      else:
        index_in_midi_notes_octaves = index_in_midi_notes_octaves-1
  while (index_is_taken == True):
    index_is_taken = False
    for i in range(4):
      for j in range(2):
        if group_properties['q'+str(i)+'_freqs_set'][j]:
          if group_properties['q'+str(i)+"_freqs"][j] == index_in_midi_notes_octaves:
            if group_properties['q'+str(i)+"_measured"]:
              if group_properties['q'+str(i)+"_measured"] == j:
                index_is_taken = True
    if index_is_taken == True:
      index_in_midi_notes_octaves = index_in_midi_notes_octaves-chord_factor #third
      if chord_factor == 2:
        chord_factor = 5
      else:
        chord_factor = 2    
    # converges to an untaken note in a musical chord
  return index_in_midi_notes_octaves

timestamp_of_last_measurement_for_2= 0
timestamp_of_last_measurement_for_all= 0
def on_message(client, userdata, msg):
  global current_synth, midiouts, midi_notes, timestamps, group_properties, sievert_averages, significance_level, own_durations, recorded_durations, material_half_lifes, timestamp_of_last_measurement_for_2, timestamp_of_last_measurement_for_all
  if is_json(msg.payload.decode('utf-8')):
      midiout = midiouts[current_synth]
      msg = json.loads(msg.payload.decode('utf-8'))
      if not timestamps:
        for timestamp in msg['timestamps']:
          timestamps.append(timestamp)
          print("First timestamp received")
        group_properties['q'+str(current_synth)+'_pulses'] = group_properties['q'+str(current_synth)+'_pulses'] + msg['length']
      else:
        previous_timestamp = timestamps[-1]
        for timestamp in msg['timestamps']:
          timestamps.append(timestamp)
          timestamps.sort()
        group_properties['q'+str(current_synth)+'_pulses'] = group_properties['q'+str(current_synth)+'_pulses'] + msg['length']
        time_elapsed_during_last_measurement_for_2 = time.time() - timestamp_of_last_measurement_for_2
        time_elapsed_during_last_measurement_for_all = time.time() - timestamp_of_last_measurement_for_all
        print("Pulse received for qubit:", current_synth)
        if (material_half_lifes):
          print("\tCounts for the current episode:", group_properties['q'+str(current_synth)+'_pulses'],"(maximum recorded:",max(material_half_lifes),", minimum:",min(material_half_lifes),")")
        if time_elapsed_during_last_measurement_for_all > 7: # for in between meta-episodes
          if not group_properties['q'+str(current_synth)+'_playing']:
            midiout.send_message(midi_note('play',1))
            group_properties['q'+str(current_synth)+'_playing'] = True
        if time_elapsed_during_last_measurement_for_2 > 7: # for when the fourth qubit is sounding
          # artistic choice ("echo") - 
          if (current_synth == 3):
            for i in range(3): # third qubit needs to be played after it completed its measurement
              # artistic choice to alternate between sounding and not
              midiouts[i].send_message(midi_note('play',1))
              group_properties['q'+str(current_synth)+'_playing'] = True
          # - end
        current_timestamp = timestamps[-1]
        duration = current_timestamp - previous_timestamp
        index_in_durations = sort_into_pulse_durations(duration) # index in overall durations
        if len(recorded_durations) == 1:
          relative_position_in_durations = 0
        else:
          relative_position_in_durations = (index_in_durations)/(len(recorded_durations)-1) # index in overall durations
        index_in_midi_notes_octaves = math.floor(relative_position_in_durations*(len(midi_notes_octaves)-1))
        print("\tDuration of the pulse:",duration,"(maximum recorded:",max(recorded_durations),", minimum:",min(recorded_durations),")")
        own_durations.append(duration)
        own_durations.sort(reverse=True)
        for i, duration_value in enumerate(own_durations):
          if duration_value == duration:
            if i == 0 or len(own_durations) > 4 and i < 2:
              index_in_midi_notes_octaves = get_new_lowest_frequency(index_in_midi_notes_octaves)
              print("\tNew lowest frequency for",str(current_synth),":",list(midi_notes_octaves)[index_in_midi_notes_octaves])
              group_properties['q'+str(current_synth)+'_freqs'][0] = index_in_midi_notes_octaves
              midiout.send_message(list(midi_notes_octaves.values())[index_in_midi_notes_octaves][0]) # oct
              midiout.send_message(list(midi_notes_octaves.values())[index_in_midi_notes_octaves][1]) # note
              group_properties['q'+str(current_synth)+'_freqs_set'][0] = True
            elif i == (len(own_durations)-1):
              index_in_midi_notes_octaves = get_new_highest_frequency(index_in_midi_notes_octaves)
              print("\tNew highest frequency for",str(current_synth),":",list(midi_notes_octaves)[index_in_midi_notes_octaves])
              group_properties['q'+str(current_synth)+'_freqs'][1] = index_in_midi_notes_octaves
              note_oct = list(midi_notes_octaves.values())[index_in_midi_notes_octaves][0]
              note_oct[1] = 23 # for right slider oct
              midiout.send_message(note_oct) # oct
              note_note = list(midi_notes_octaves.values())[index_in_midi_notes_octaves][1]
              note_note[1] = 21 # for right slider note
              midiout.send_message(note_note) # note
              group_properties['q'+str(current_synth)+'_freqs_set'][1] = True

        # Representing qubits in Superposition
        group_properties['q'+str(current_synth)+'_freqs_set'][0]
        theta_midi_value = msg['timestamps'][0] & 0b1111111
        phi_midi_value = msg['timestamps'][0] >> 7 & 0b1111111
        lambda_midi_value = msg['timestamps'][0] >> 14 & 0b1111111
        midiout.send_message(midi_note('theta',theta_midi_value))
        midiout.send_message(midi_note('phi',phi_midi_value))
        midiout.send_message(midi_note('lambda',lambda_midi_value))
        group_properties['q'+str(current_synth)+'_inclinations'][0], group_properties['q'+str(current_synth)+'_inclinations'][1], group_properties['q'+str(current_synth)+'_inclinations'][2] = theta_midi_value, phi_midi_value, lambda_midi_value

        # calculate µS
        time_interval = timestamps[-1]-timestamps[0]
        confidence = calculate_sievert_average_diff(group_properties['q'+str(current_synth)+'_pulses'],time_interval)
        if len(own_durations) > 10:
          lowering_significance_amount = math.floor(len(own_durations)/10)
          print("\tMore than 10 pulses were received within the episode, the value of the confidence level is increased by",lowering_significance_amount*0.01) # todo: wenn zu lange keine konfidenz hergestellt wird das signifikanzlevel erhöhen
          significance_level = significance_level + lowering_significance_amount*0.01 
        print("\tAC:",confidence,", CL:",significance_level,", upper freq found:", group_properties['q'+str(current_synth)+'_freqs_set'][0] ,", lower freq found:",group_properties['q'+str(current_synth)+'_freqs_set'][1])
        if (confidence < significance_level and group_properties['q'+str(current_synth)+'_freqs_set'][0] and group_properties['q'+str(current_synth)+'_freqs_set'][1]):
          # reset confidence and other stuff for within qubit
          last_ts = timestamps[-1]
          timestamps = []
          timestamps.append(last_ts)
          own_durations = []
          sievert_averages = []
          group_properties['q'+str(current_synth)+'_freqs_set'][0] = False
          group_properties['q'+str(current_synth)+'_freqs_set'][1] = False
          significance_level = initial_significance_level
          print("\t*Measurement")
          # -> own measurement algorithm
          measurement_collapses_into = 0
          if(round(abs((64-theta_midi_value+1)/64),0)): # collapses to 1
            measurement_collapses_into = 1
          else:
            measurement_collapses_into = 0
          # Entanglement
          if current_synth != 0:
            if group_properties['q'+str(current_synth-1)+'_collapsed_result'] == 1: # CNOT
              print("\t\t*Entanglement takes place through CNOT between",str(current_synth),"and",str(current_synth-1))
              if measurement_collapses_into == 1:
                measurement_collapses_into = 0 
              else:
                measurement_collapses_into = 1
          group_properties['q'+str(current_synth)+'_collapsed_result'] = measurement_collapses_into
          group_properties['q'+str(current_synth)+'_measured'] = True
          # carrying out the measuremnt to the instrument:
          print("The episode ended. Collapse of qubit",current_synth,"result in it's basic state of", measurement_collapses_into)
          if measurement_collapses_into == 1:
            midiout.send_message(midi_note('theta',1))
            midiout.send_message(midi_note('phi',1))
            midiout.send_message(midi_note('lambda',1))
          else:
            midiout.send_message(midi_note('theta',64))
            midiout.send_message(midi_note('phi',1))
            midiout.send_message(midi_note('lambda',1))
          

          # Half-life
          current_count = group_properties['q'+str(current_synth)+'_pulses']
          material_half_lifes.append(current_count)
          group_properties['q'+str(current_synth)+'_pulses'] = 0
          material_half_lifes.sort()
          index_in_overall_counts = 0
          occurence_in_overall_counts = 0
          for i, count in enumerate(material_half_lifes):
            if count == current_count:
              occurence_in_overall_counts = occurence_in_overall_counts + 1
              index_in_overall_counts = i
          if occurence_in_overall_counts == 1:
            occurence_in_overall_counts = index_in_overall_counts
          else:
            occurence_in_overall_counts = round(occurence_in_overall_counts / 2)
          if len(material_half_lifes) == 1:
            relative_position_in_counts = 0
          else:
            relative_position_in_counts = (occurence_in_overall_counts)/(len(material_half_lifes)-1)
          release_and_reverb_midi_value = relative_position_in_counts*120
          # print("material_half_lifes",material_half_lifes)
          # print("occurence_in_overall_counts",occurence_in_overall_counts)
          # print("relative_position_in_counts",relative_position_in_counts)
          # print("release_and_reverb_midi_value",release_and_reverb_midi_value)
          midiout.send_message(midi_note('left_slider_reverb',release_and_reverb_midi_value))
          midiout.send_message(midi_note('left_slider_delay',release_and_reverb_midi_value))
          midiout.send_message(midi_note('right_slider_reverb',release_and_reverb_midi_value))
          midiout.send_message(midi_note('right_slider_delay',release_and_reverb_midi_value))
          


          # end cases
          # still necessary fix (! exact poles not reachable via midi 0?): 
          time.sleep(2)
          if measurement_collapses_into == 1:
            midiout.send_message(midi_note('theta',1))
            midiout.send_message(midi_note('phi',1))
            midiout.send_message(midi_note('lambda',1))
          else:
            midiout.send_message(midi_note('theta',64))
            midiout.send_message(midi_note('phi',1))
            midiout.send_message(midi_note('lambda',1))
          midiout.send_message(midi_note('measure',1))
          group_properties['q'+str(current_synth)+'_playing'] = False

          # advancing to the next episode
          current_synth = current_synth+1
          if (current_synth == 3): # artistic choice ("echo") to make chord sound for longer
            timestamp_of_last_measurement_for_2 = time.time()
          if (current_synth == 4): # wir haben nur 4
            print("The meta-episode ends\n")
            for i in range(4):
              group_properties['q'+str(i)+'_measured'] = False
              # group_properties['q'+str(i)+'_measured'] = False
              midiouts[i].send_message(midi_note('measure',1))
              group_properties['q'+str(i)+'_playing'] = False
              timestamp_of_last_measurement_for_all = time.time()
            # reset()
            current_synth = 0
  else:
      print("received not a json")

def on_connect(client, userdata, flags, rc):
    print("Connected to the MQTT broker")
    client.subscribe("test")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
reset()
client.connect("192.168.0.3", 1883, 60)
client.loop_forever()