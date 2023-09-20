import music21 as m21
from fractions import Fraction

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
    

# not used
def find_closest_fraction(num):
    """
    float -> (numerator, denominator)
    """
    if num == 0.0:
        return (0, 1)
    else:
        numer = round(num*64)
        denom = 64
        divisor = gcd(numer, denom)
        return (round(numer / divisor), round(denom / divisor))
def gcd(p, q):
    """
    Returns the greatest common divisor.
    """
    if p % q == 0:
        return q
    else:
        return gcd(q, p % q)


def read_musicXML_file(file_path):
    """
    Returns (xml_data, a list of meters)
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


def get_tempos_from_xml(xml):
    """
    Returns the metronome marks found in the score (by looking at only one part).
    
    xml -> a list of tuples: [(MetronomeMark1, measure1), (MetronomeMark2, measure2), ...]
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
            #if type(obj) == m21.expressions.TextExpression:
               #tempos.append((obj, measure))
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
        position = Fraction((note.beat-1) * beat_length)
        first_col = str(note.measure) + "+" + str(position.numerator) + "/" + str(position.denominator)
            # second column:
        cumulative_time = calculate_cumulative_time(note.measure, position, meters)
        second_col = str(cumulative_time.numerator) + "/" + str(cumulative_time.denominator)
        lines.append((first_col, second_col, 90, int(note.midi), 80))
        
        # ---Out notes---
        end = Fraction((note.beat-1) * beat_length) + Fraction(note.duration)
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

#name = "C major arpeggio contrary motion"
#name = "C major scale contrary motion"
#name = "C major scale with both hands"
#name = "Chopin_-_Raindrop_Prelude"
#name = "Chord Etude"
#name = "Debussy_Prelude_Bk_1_No_3_Le_Vent_dans_la_plaine"
name = "JSBach_No._1_in_C_Major,_BWV_846_Fugue"
#name = "Rachmaninov_Etude-Tableau_op._39_no._6"
#name = "Sonata_No._18_Mvt_2_Mozart"
#name = "Sonate_No._14_Moonlight_1st_Movement"
#name = "TheBlues"
#name = "TheEntertainer"

    
path = "/Users/yjiang3/Documents/SV-PianoPrecision/Scores/"


xml_path = path + name + "/" + name + ".mxl"
meter_path = path + name + "/" + name + ".meter"
tempo_path = path + name + "/" + name + ".tempo"
output_path = path + name + "/" + name + ".solo"

########### Read MusicXML file

xml_data = read_musicXML_file(xml_path)
# xml_data.show("text")
meters = get_meters_from_xml(xml_data)
tempos = get_tempos_from_xml(xml_data)

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
    position = Fraction((marking.beat-1) * beat_length)
    if (marking.numberImplicit):
        print("WARNING in writing .tempo: numberImplicit is True!")
    print(str(measure) + "+" + str(position.numerator) + '/'+ str(position.denominator),
          marking.number, marking.referent.quarterLength)
    file.write(str(measure)+ "+" + str(position.numerator) + '/'+ str(position.denominator)+
               "\t"+str(marking.number)+"\t"+str(marking.referent.quarterLength)+"\n")
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
