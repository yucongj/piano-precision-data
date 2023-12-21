import music21 as m21
from fractions import Fraction
import re

## Created by Yucong Jiang on Feb 5, 2022

## Note: Unfortunately, it still needs manual correction for pickup measures.


class Note:
    def __init__(self, measure, beat, duration, midi):
        self.measure = measure
        self.beat = beat # a Fraction
        self.duration = duration # quarter note = 0.25
        self.midi = int(midi)
    def __str__(self):
        return "measure: " + str(self.measure) + "\tbeat: " + str(self.beat) +\
               "\tduration: " + str(self.duration) + "\tmidi: " + str(self.midi)
    

class SPOSX_Event:
    def __init__(self, elid, tick, label, fraction):
        self.elid = elid # int
        self.tick = tick # int
        self.label = label # e.g., "2+1/8"
        self.fraction = fraction # e.g., "9/8"
    def __str__(self):
        return "<event elid=\"" + str(self.elid) + "\" position=\"" + str(self.tick) +\
               "\" label=\"" + self.label + "\" fraction=\"" + self.fraction + "\"/>"

class SOLO_Event:
    def __init__(self, tempo, tick, label, fraction):
        self.tempo = tempo # default tempo is "quarter note = 120."
        self.tick = tick # float
        self.label = label # e.g., "2+1/8"
        self.fraction = fraction # e.g., "9/8"
    def __str__(self):
        return "tempo: " + str(self.tempo) + "\ttick: " + str(self.tick) +\
               "\tlabel: " + self.label + "\tfraction: " + self.fraction

### NOT USED
##def find_closest_fraction(num):
##    """
##    float -> (numerator, denominator)
##    """
##    if num == 0.0:
##        return (0, 1)
##    else:
##        numer = round(num*64)
##        denom = 64
##        divisor = gcd(numer, denom)
##        return (round(numer / divisor), round(denom / divisor))
##def gcd(p, q):
##    """
##    Returns the greatest common divisor.
##    """
##    if p % q == 0:
##        return q
##    else:
##        return gcd(q, p % q)


def read_musicXML_file(file_path):
    """
    Returns xml_data
    """
    xml_data = m21.converter.parse(xml_path)
    return xml_data
    

def get_meters_from_xml(xml):
    """
    Returns the time signatures found in the score (by looking at only one part).
    
    xml -> a list of tuples: [(meter1, measure1), (meter2, measure2), ...]
    """
    time_signatures = []
    if (len(xml.parts) == 0):
        print("No parts found in xml_to_meters.")
        return []
    
    # Assuming all parts share the same time signature, of course.
    part = xml.parts[0]
    for measure in part.getElementsByClass(m21.stream.Measure):
        if measure.timeSignature:
            time_signatures.append((measure.timeSignature, measure))
    return time_signatures


def get_tempos_from_xml(xml, defined_tempo):
    """
    Returns the metronome marks / tempo texts found in the score.
    Note: It looks at only one part, which might not be sufficient.
    
    xml, dic -> a list of tuples: [(MetronomeMark1, measure1), (MetronomeMark2, measure2), ...]
    """
    tempos = []
    if (len(xml.parts) == 0):
        print("No parts found in get_tempos_from_xml.")
        return []
    
    # Assuming all parts share the same tempo, of course.
    part = xml.parts[0]
    for measure in part.getElementsByClass(m21.stream.Measure):
        for obj in measure:
            if type(obj) == m21.tempo.MetronomeMark:
               tempos.append((obj, measure))
            if type(obj) == m21.expressions.TextExpression:
                if obj.content in defined_tempo:
                    tempos.append((obj, measure))
                if obj.content == "a tempo":
                    print((obj, measure))
    return tempos


def extract_individual_notes(xml_data):
    """
    Returns a list of notes in the score.
    """
    notes = []
    xml_data = xml_data.stripTies() # with ties stripped

    for part in xml_data.parts:
        for measure in part.getElementsByClass(m21.stream.Measure):
            for note in measure.flatten().notes:
                if note.isChord:
                    beat = Fraction(note.beat)
                    duration = note.quarterLength
                    for chord_note in note.pitches:
                        midi = chord_note.ps
                        notes.append(Note(measure.number, beat, duration/4, midi))
                else:
                    beat = Fraction(note.beat)
                    duration = note.quarterLength
                    midi = note.pitch.ps
                    notes.append(Note(measure.number, beat, duration/4, midi))
        notes = sorted(notes, key=lambda x: (x.measure, x.beat, x.midi))
    return notes


def calculate_cumulative_time(measure, position, meters):
    """
    Returns the cumulative time given the measure number, position, and meters.

    int, Fraction, a list of meter tuples -> Fraction
    """
    i = 0
    # meters[stopping_index] is the largest meter that's not later than measure
    while i < len(meters):
        if meters[i][1].number > measure:
            stopping_index = i - 1
            break
        elif meters[i][1].number == measure:
            stopping_index = i
            break
        else:
            i += 1
    if i == len(meters):
        stopping_index = len(meters) - 1

    # add distance between ith meter and (i+1)th meter:
    time = 0
    i = 0
    while (i + 1) <= stopping_index:
        measures = meters[i+1][1].number - meters[i][1].number
        meter = meters[i]
        time += measures * Fraction(meter[0].numerator, meter[0].denominator)
        i += 1
    meter = meters[i]
    time += (measure - meters[stopping_index][1].number) * Fraction(meter[0].numerator, meter[0].denominator)
    time += position

    return Fraction(time)


def find_meter_of_measure(measure, meters):
    """
    Returns the meter of the given measure.

    int, a list of meters --> meter as a tuple (Meter, Measure)
    """
    i = 0
    while i < len(meters):
        if measure == meters[i][1].number:
            return meters[i]
        elif measure < meters[i][1].number:
            return meters[i - 1]
        else:
            i += 1
    return meters[len(meters) - 1]
    

def construct_lines_of_solo(notes, meters):
    """
    Returns a list of tuples: (first column, second column, 90, midi, in/out)
    """
    lines = []
    print(meters)
    
    
    for note in notes:
        meter = find_meter_of_measure(note.measure, meters)[0]
        beat_length = Fraction(1, meter.denominator)
        #print(note)
        # ---In notes---
            # first column:
        position = Fraction( (note.beat-1) * Fraction(meter.beatDuration.quarterLength) * Fraction(1, 4) )
        first_col = str(note.measure) + "+" + str(position.numerator) + "/" + str(position.denominator)
            # second column:
        cumulative_time = calculate_cumulative_time(note.measure, position, meters)
        second_col = str(cumulative_time.numerator) + "/" + str(cumulative_time.denominator)
        lines.append((first_col, second_col, 90, int(note.midi), 80))
        
        # ---Out notes---
        end = position + Fraction(note.duration)
        new_measure = note.measure + int(end // Fraction(meter.numerator/meter.denominator))
        new_position = end % Fraction(meter.numerator, meter.denominator)
            # first column:
        first_col = str(new_measure) + "+" + str(new_position.numerator) + "/" + str(new_position.denominator)
            # second column:
        cumulative_time = calculate_cumulative_time(new_measure, new_position, meters)
        second_col = str(cumulative_time.numerator) + "/" + str(cumulative_time.denominator)
        lines.append((first_col, second_col, 90, int(note.midi), 0))

    lines = sorted(lines, key=lambda x: (eval(x[1]), x[4], x[3]))
    return lines
    
    
########### Input and output files
name = "Beethoven Sonata Op. 31 No. 3 (The Hunt) Movement I"
#name = "Beethoven Sonata Op. 110 Movement I"
name = "Chopin Nocturne Op. 27 No. 2"
#name = "J. S. Bach Fugue in C Major, BWV 846"
#name = "Mozart Sonata No. 18 Movement II"
#name = "Rachmaninov Etude-Tableau, Op. 39 No. 6"
#name = "Schubert Impromptu Op. 90 No. 1"
#name = "Schubert Impromptu Op. 90 No. 3"

 
path = "/Users/yjiang3/Documents/PianoPrecision/Scores/"


xml_path = path + name + "/" + name + ".mxl"
meter_path = path + name + "/" + name + ".meter"
tempo_path = path + name + "/" + name + ".tempo"
output_path = path + name + "/" + name + ".solo"

########### Read defined tempo values
defined_tempo_values = {}
with open('TextTempoValue.txt') as file:
    for line in file.readlines():
        pair = line.split('\t')
        defined_tempo_values[pair[0]] = pair[1].strip()

########### Read MusicXML file

xml_data = read_musicXML_file(xml_path)
# xml_data.show("text")
meters = get_meters_from_xml(xml_data)
tempos = get_tempos_from_xml(xml_data, defined_tempo_values)

########### Write to METER file

file = open(meter_path, "w")
for meter in meters:    
    file.write(str(meter[1].measureNumber)+
               "\t"+str(meter[0].numerator)+"/"+str(meter[0].denominator)+"\n")
file.close()

########### Write to TEMPO file

file = open(tempo_path, "w")
for tempo in tempos:
    marking = tempo[0]
    measure = tempo[1].measureNumber
    meter = find_meter_of_measure(measure, meters)[0]
    beat_length = Fraction(1, meter.denominator) 
    position = Fraction( (marking.beat-1) * Fraction(meter.beatDuration.quarterLength) * Fraction(1, 4) )
    if type(marking) == m21.tempo.MetronomeMark:
        #if (marking.numberImplicit):
            #print("WARNING in writing .tempo: numberImplicit is True!")
        print(str(measure) + "+" + str(position.numerator) + '/'+ str(position.denominator),
              marking.number, marking.referent.quarterLength)
        file.write(str(measure)+ "+" + str(position.numerator) + '/'+ str(position.denominator)+
                   "\t"+str(marking.number)+"\t"+str(marking.referent.quarterLength)+"\n")
    if type(marking) == m21.expressions.TextExpression:
        print(str(measure) + "+" + str(position.numerator) + '/'+ str(position.denominator),
              float(defined_tempo_values[marking.content]), beat_length*4.0)
        file.write(str(measure)+ "+" + str(position.numerator) + '/'+ str(position.denominator)+
                   "\t"+str(defined_tempo_values[marking.content])+"\t"+str(beat_length*4.0)+"\n")
file.close()


########### Construct lines for SOLO file

notes = extract_individual_notes(xml_data)
lines = construct_lines_of_solo(notes, meters)

########### Write to SOLO file

file = open(output_path, "w")
for line in lines:
    # print(line)
    file.write(str(line[0])+"\t"+str(line[1])+"\t"+str(line[2])+"\t"+str(line[3])+"\t"+str(line[4])+"\n")
file.close()

########### Create SPOSX file

sposx_events = [] # from SPOS file
with open(path + name + "/" + name + ".spos") as file:
    for line in file.readlines():
        if len(line) > 17 and "<event elid=" in line:
            r = re.match(r'<event elid="(\d+)" position="(\d+)"/>', line.strip())
            sposx_events.append(SPOSX_Event(int(r.group(1)), int(r.group(2)), "", ""))

solo_events = []; seen_fractions = []
with open(output_path) as file:
    for line in file.readlines():
        elements = line.split('\t')
        if elements[1] not in seen_fractions:
            seen_fractions.append(elements[1])
            solo_events.append(SOLO_Event(120., -1, elements[0], elements[1]))
# Apply any tempo changes to relevant events
tempo_changes = []
with open(path + name + "/" + name + ".tempo") as file:
    for line in file.readlines():
        tempo_changes.append(line.strip().split("\t"))
for count in range(len(tempo_changes)-1):
    start = tempo_changes[count]
    end = tempo_changes[count+1]
    for event in solo_events:
        if eval(event.label) >= eval(start[0]) and eval(event.label) < eval(end[0]):
            event.tempo = float(start[1]) * float(start[2])
if len(tempo_changes) > 0:
    last = tempo_changes[-1]
    for event in solo_events:
        if eval(event.label) >= eval(last[0]):
            event.tempo = float(last[1]) * float(last[2])
# Calculate the tick for each solo_event
last_change = 0
for i in range(len(solo_events)):
    if i == 0:
        last_tempo = solo_events[0].tempo
        f = Fraction(solo_events[0].fraction)
        current_tick = f.numerator * 2000. * (120. / last_tempo) / f.denominator
        last_change_tick = current_tick
    else:
        current_tempo = solo_events[i].tempo
        duration = Fraction(solo_events[i].fraction) - Fraction(solo_events[last_change].fraction)
        current_tick =last_change_tick + duration.numerator * 2000. * (120. / last_tempo) / duration.denominator
        if abs(current_tempo - last_tempo) > .001:
            last_tempo = current_tempo
            last_change = i
            last_change_tick = current_tick
    solo_events[i].tick = current_tick
# Find solo events for sposx events (simply finding the closest ticks)
last_solo_i = 0
for e in sposx_events:
    distance = abs(solo_events[last_solo_i].tick - e.tick)
    while (last_solo_i+1) < len(solo_events) and abs(solo_events[last_solo_i+1].tick - e.tick) < distance:
        last_solo_i += 1
        distance = abs(solo_events[last_solo_i].tick - e.tick)
    e.label = solo_events[last_solo_i].label
    e.fraction = solo_events[last_solo_i].fraction
# Write events to SPOSX file
event_count = 0
with open(path + name + "/" + name + ".spos") as file:
    with open(path + name + "/" + name + ".sposx", 'w') as w_file:
        for line in file.readlines():
            if len(line) > 17 and "<event elid=" in line:
                w_file.write(" "*8 + str(sposx_events[event_count]) + "\n")
                event_count += 1
            else:
                w_file.write(line)
