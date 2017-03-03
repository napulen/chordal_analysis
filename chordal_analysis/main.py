import os, music21, json
from natsort import natsorted, ns
import numpy as np
from pylab import *

INPUT_DIR = 'kpcorpus'

PITCH_CLASSES = 12

chord_templates = {
"maj":[0,4,7],
"dom7":[0,4,7,10],
"min":[0,3,7],
"fdim":[0,3,6,9],
"hdim":[0,3,6,10],
"dim":[0,3,6]
}

chord_probabilities = {
"maj":.436,
"dom7":.219,
"min":.194,
"fdim":.044,
"hdim":.037,
"dim":0.018
}

pitch_classes = {
0:'C',
1:'C#',
2:'D',
3:'D#',
4:'E',
5:'F',
6:'F#',
7:'G',
8:'G#',
9:'A',
10:'A#',
11:'B'
}

def get_chord_name(pitch_class, chord_type):
	return '{}_{}'.format(pitch_classes[pitch_class],chord_type)

def score_segment(notes):
	max_score = -inf
	chords = []
	for pitch_class in range(PITCH_CLASSES):
		for chord_type in chord_templates:
			weight = np.array(chord_templates[chord_type])
			weight = (weight + pitch_class) % 12
			positive_intersection = [n for n in notes if n in weight]
			negative_intersection = [n for n in notes if n not in weight]
			P = len(positive_intersection)
			N = len(negative_intersection)
			M = len(weight) - len(set(positive_intersection))
			S = P - (M + N)
			if S > max_score:
				chord = get_chord_name(pitch_class, chord_type)
				chords = [chord]
				max_score = S
			elif S == max_score:
				chord = get_chord_name(pitch_class, chord_type)
				chords.append(chord)
	return max_score,chords


def score_segments(minimal_segments):
	scored_segments = {}
	#print len(minimal_segments)
	for idu,u in enumerate(minimal_segments[:-1]):
		#print idu
		# Initialize the segment tree
		scored_segments[idu] = {}
		segment_tree = scored_segments[idu]
		# Segment starts with the notes of the first minimal segment
		u_notes = [note.pitch.pitchClass for note in u]
		segment_notes = u_notes
		# Then iterate over the rest of minimal segments
		for idv,v in enumerate(minimal_segments[idu+1:]):
			# Initialize this segment
			segment_tree[idu+idv+1] = {}
			segment = segment_tree[idu+idv+1]
			v_notes = [note.pitch.pitchClass for note in v]
			segment_notes.extend(v_notes)
			score,chords = score_segment(segment_notes)
			segment['score'] = score
			segment['chords'] = chords
	return scored_segments

def get_minimal_segments(score):
	chords = score.chordify()
	score.insert(0, chords)
	minimal_segments = chords.recurse().getElementsByClass('Chord')
	return minimal_segments

if __name__ == '__main__':
	files = os.listdir(INPUT_DIR)
	files = [x for x in files if x.endswith('.xml')]
	files = natsorted(files, key=lambda y: y.lower())
	for fname in files:
		#print fname
		fdir = os.path.join(INPUT_DIR,fname)
		score = music21.converter.parse(fdir)
		minimal_segments = get_minimal_segments(score)
		#print len(minimal_segments)
		#minimal_segments.show()
		segments = score_segments(minimal_segments)
		print json.dumps(segments)
		#lyrics = music21.search.lyrics.LyricSearcher(score)

		#s.show()
		#mid.open(os.path.join)
		#mid.read()
		#mid.close()
		#mid = MidiFile(os.path.join(INPUT_DIR,f))
		#print mid
		break
