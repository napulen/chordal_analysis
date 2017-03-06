'''
Re-implementation of the chordal_analysis algorithms from Bryan Pardo, using Music21

Nestor Napoles (napulen@gmail.com), 2017
'''

import os, music21, json, time, sys
from natsort import natsorted, ns
import numpy as np
from pylab import *

INPUT_DIR = 'kpcorpus'
MINIMUM_INTEGER = -sys.maxint - 1

PITCH_CLASSES = 12

chord_templates = {
'dim':[
{0, 3, 6}, {1, 4, 7}, {2, 5, 8}, {3, 6, 9}, {4, 7, 10}, {5, 8, 11},
{6, 9, 0}, {7, 10, 1}, {8, 11, 2}, {9, 0, 3}, {10, 1, 4}, {11, 2, 5}
],
'min':[
{0, 3, 7}, {1, 4, 8}, {2, 5, 9}, {3, 6, 10}, {4, 7, 11}, {5, 8, 0},
{6, 9, 1}, {7, 10, 2}, {8, 11, 3}, {9, 0, 4}, {10, 1, 5}, {11, 2, 6}
],
'fdim':[
{0, 3, 6, 9}, {1, 4, 7, 10}, {2, 5, 8, 11}, {3, 6, 9, 0}, {4, 7, 10, 1}, {5, 8, 11, 2},
{6, 9, 0, 3}, {7, 10, 1, 4}, {8, 11, 2, 5}, {9, 0, 3, 6}, {10, 1, 4, 7}, {11, 2, 5, 8}
],
'maj':[
{0, 4, 7}, {1, 5, 8}, {2, 6, 9}, {3, 7, 10}, {4, 8, 11}, {5, 9, 0},
{6, 10, 1}, {7, 11, 2}, {8, 0, 3}, {9, 1, 4}, {10, 2, 5}, {11, 3, 6}
],
'hdim':[
{0, 3, 6, 10}, {1, 4, 7, 11}, {2, 5, 8, 0}, {3, 6, 9, 1}, {4, 7, 10, 2}, {5, 8, 11, 3},
{6, 9, 0, 4}, {7, 10, 1, 5}, {8, 11, 2, 6}, {9, 0, 3, 7}, {10, 1, 4, 8}, {11, 2, 5, 9}
],
'dom7':[
{0, 4, 7, 10}, {1, 5, 8, 11}, {2, 6, 9, 0}, {3, 7, 10, 1}, {4, 8, 11, 2}, {5, 9, 0, 3},
{6, 10, 1, 4}, {7, 11, 2, 5}, {8, 0, 3, 6}, {9, 1, 4, 7}, {10, 2, 5, 8}, {11, 3, 6, 9}
]
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

def compute_max_paths_u_to_v(scored_segments, origin, end):
	ms = scored_segments['minimal_segments']
	# Initialize the origin minimal segment
	ms[origin]['maxpath']['origin'] = 'HERE'
	ms[origin]['maxpath']['score'] = 0
	for u in sorted(ms.iterkeys())[origin:end]:
		s = ms[u]['segments']
		curr_u_score = ms[u]['maxpath']['score']
		for v in sorted(s.iterkeys())[:end]:
			curr_v_score = ms[v]['maxpath']['score']
			u_to_v = s[v]['score']
			if curr_u_score + u_to_v > curr_v_score:
				ms[v]['maxpath']['score'] = curr_u_score + u_to_v
				ms[v]['maxpath']['origin'] = u

def compute_max_paths(scored_segments):
	last_minseg = len(scored_segments['minimal_segments'])-1
	compute_max_paths_u_to_v(scored_segments, 0, last_minseg)

def score_segment(notes):
	max_score = MINIMUM_INTEGER
	chords = []
	for pitch_class in range(PITCH_CLASSES):
		for chord_type in chord_templates:
			weight = chord_templates[chord_type][pitch_class]
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
	scored_segments = {'minimal_segments':{}}
	minsegs_number = len(minimal_segments)
	for idu,u in enumerate(minimal_segments):
		print 'Scoring... {}/{}...'.format(idu,minsegs_number-1),
		start = time.time()
		# Initialize the segment tree
		segment_tree = {}
		scored_segments['minimal_segments'][idu] = {'segments':segment_tree, 'maxpath':{'score':MINIMUM_INTEGER,'origin':-1}}
		# Last minimal segment has always zero segments(edges) as it is the last node and it goes nowhere after
		if idu == minsegs_number-1:
			break
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
		end = time.time()
		print '{}s'.format(end-start)
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
		scored_segments = score_segments(minimal_segments)
		compute_max_paths(scored_segments)
		print json.dumps(scored_segments)
		#lyrics = music21.search.lyrics.LyricSearcher(score)

		#s.show()
		#mid.open(os.path.join)
		#mid.read()
		#mid.close()
		#mid = MidiFile(os.path.join(INPUT_DIR,f))
		#print mid
		break
