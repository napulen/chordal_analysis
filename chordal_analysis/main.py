'''
Re-implementation of the chordal_analysis algorithms from Bryan Pardo, using Music21
'''

import os, music21, json, time, sys
from natsort import natsorted, ns
import numpy as np
from pylab import *
from shutil import copyfile

INPUT_DIR = 'kpcorpus'
OUTPUT_DIR = 'output'
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

def get_pitch_class(note_str):
	''' This function converts a string note name
	into a pitch_class. WARNING: There is a really
	risky assumption here: The "b" (lowercase) symbol
	will always be used to represent "flat" and never
	the note "B" '''
	note_str = note_str.replace('b','-')
	pitch = music21.pitch.Pitch(note_str)
	return pitch.pitchClass

def compute_max_paths_u_to_v(scored_segments, origin, end):
	''' This function calculates the max path from one minimal segments
	to another, the indexes of both (origin, end) segments are mandatory '''
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
	# Trace back the whole path
	curr_node = end
	origin = ms[curr_node]['maxpath']['origin']
	maxpath = [end]
	while origin != 'HERE':
		curr_node = origin
		origin = ms[curr_node]['maxpath']['origin']
		maxpath.append(curr_node)
	maxpath = list(reversed(maxpath))
	scored_segments['maxpath'] = maxpath


def compute_max_paths(scored_segments):
	''' As the default case is to compute the max_path in the
	entire graph, adding this callback to calculate the last
	minimal segment and make it transparent to the main function '''
	last_minseg = len(scored_segments['minimal_segments'])-1
	compute_max_paths_u_to_v(scored_segments, 0, last_minseg)

def score_segment(notes):
	''' Computation of the score, iterates over the chord templates
	for each pitch class and outputs the score S and possible chord labels '''
	max_score = MINIMUM_INTEGER
	chords = []
	for pitch_class in range(PITCH_CLASSES):
		#print '\t\t{}...'.format(pitch_classes[pitch_class])
		for chord_type in chord_templates:
			template = chord_templates[chord_type][pitch_class]
			positive_list = [n for subnotes in notes for n in subnotes if n in template]
			negative_list = [n for subnotes in notes for n in subnotes if n not in template]
			#missing_list = [note for note in template for sublist in notes if note not in sublist]
			P = len(positive_list)
			N = len(negative_list)
			M = len(template) - len(set(positive_list))
			S = P - (M + N)
			#print '\t\t\t{}:{} = {} - ({} + {})'.format(chord_type, S,P,N,M)
			if S > max_score:
				chord = get_chord_name(pitch_class, chord_type)
				chords = [chord]
				max_score = S
			elif S == max_score:
				chord = get_chord_name(pitch_class, chord_type)
				chords.append(chord)
	#print '\t\t{}{}'.format(max_score,chords)
	return max_score,chords

def score_segments(minimal_segments):
	''' This function computes scores for every minimal segment
	in the score, and generates a "segment" tree that includes
	all the segments (edges) that start from this minimal segment (node) '''
	scored_segments = {'minimal_segments':{}}
	minsegs_number = len(minimal_segments)
	for idu,u in enumerate(minimal_segments):
		#print 'Scoring... {}/{}...'.format(idu,minsegs_number-1)
		start = time.time()
		# Initialize the segment tree
		segment_tree = {}
		scored_segments['minimal_segments'][idu] = {'segments':segment_tree, 'maxpath':{'score':MINIMUM_INTEGER,'origin':-1}}
		# Last minimal segment has always zero segments(edges) as it is the last node and it goes nowhere after
		if idu == minsegs_number-1:
			break
		# Segment starts with the notes of the first minimal segment
		u_notes = [note.pitch.pitchClass for note in u]
		segment_notes = [u_notes]
		# Then iterate over the rest of minimal segments
		for idv,v in enumerate(minimal_segments[idu+1:]):
			#print '\t{} to {}...'.format(idu,idu+idv+1)
			# Initialize this segment
			segment_tree[idu+idv+1] = {}
			segment = segment_tree[idu+idv+1]
			score,chords = score_segment(segment_notes)
			segment['score'] = score
			segment['chords'] = chords
			v_notes = [note.pitch.pitchClass for note in v]
			segment_notes.append(v_notes)
		end = time.time()
		#print '{}s'.format(end-start)
	return scored_segments

def get_minimal_segments(score):
	''' In this case, we are considering the minimal segments
	as the "chordify()" output from Music21, which is pretty
	similar and easy to get '''
	chords = score.chordify()
	score.insert(0, chords)
	minimal_segments = chords.recurse().getElementsByClass('Chord')
	return minimal_segments

def annotate_chords(chords, chordanalysis):
	''' This is the final step in the analysis, adding
	the possible chords as lyrics in the original score '''
	maxpath = chordanalysis['maxpath']
	ms = chordanalysis['minimal_segments']
	chordanalysis['chordal_analysis'] = {}
	end = maxpath[-1]
	for idx,origin in enumerate(maxpath):
		if origin != end:
			nextms = maxpath[idx+1]
			possible_chords = ms[origin]['segments'][nextms]['chords']
			chordanalysis['chordal_analysis'][origin] = possible_chords
			for chord in possible_chords:
				chords[origin].addLyric(chord)


def chordal_analysis(score):
	''' This is the main function, the input for This
	is a stream representation of Music21 that can be
	obtained with the music21.converter.parse() function '''
	chords = get_minimal_segments(score)
	chordanalysis = score_segments(chords)
	compute_max_paths(chordanalysis)
	annotate_chords(chords, chordanalysis)
	return chordanalysis

def chordify_with_lyrics(score):
	''' This is a function from Daniel Russo-Batterham to
	chordify the score with the lyric information, which
	in our case contains the chord ground-truth for the
	kpcorpus dataset '''
	labels = {}
	voice = score.parts[0]
	chords = score.chordify().recurse().getElementsByClass('Chord').stream()
	for idx,chord in enumerate(chords):
		chord_offset = chord.offset
		for melody_note in voice.flat.getElementsByOffset(chord_offset):
			try:
				lyric = melody_note.lyrics[0].rawText
				lyric = lyric.rsplit('_', 1)[0]
				chord.addLyric(lyric)
				labels[idx] = lyric
			except (IndexError, AttributeError):
				continue
	return labels

def are_chord_labels_equal(cl1, cl2):
	cl1 = cl1.split('_')
	pitch_class1 = cl1[0]
	chord_type1 = cl1[1]
	cl2 = cl2.split('_')
	pitch_class2 = cl2[0]
	chord_type2 = cl2[1]
	pc1 = get_pitch_class(pitch_class1)
	pc2 = get_pitch_class(pitch_class2)
	if pc1 == pc2:
		if chord_type1 == chord_type2:
			''' They are the same '''
			return True
	''' They are not the same '''
	return False

def compare_chord_labels(original, possible):
	possible_number = len(possible)
	for chord in possible:
		if are_chord_labels_equal(original, chord):
			return 1.0/possible_number
	return 0.0


def evaluate(original_score, chordalanalysis):
	orgnlabels = chordify_with_lyrics(original_score)
	analysislabels = chordalanalysis['chordal_analysis']
	minsegs_number = len(chordalanalysis['minimal_segments'])
	minseg_score = []
	for minseg_id in range(minsegs_number):
		if minseg_id in orgnlabels:
			curr_orgnl_label = orgnlabels[minseg_id]
		if minseg_id in analysislabels:
			curr_analysis_label = analysislabels[minseg_id]
		comparison = compare_chord_labels(curr_orgnl_label, curr_analysis_label)
		minseg_score.append(comparison)
		print '{} vs. {} = {}'.format(curr_orgnl_label, curr_analysis_label, comparison)
	percentage = (1.0*sum(minseg_score)/minsegs_number)*100.0
	return minseg_score, percentage

if __name__ == '__main__':
	files = os.listdir(INPUT_DIR)
	files = [x for x in files if x.endswith('.xml')]
	files = natsorted(files, key=lambda y: y.lower())
	for fname in files:
		print '{}... '.format(fname),
		fout_xml = '{}_analysis.xml'.format(fname[:-4])
		fout_json = '{}_analysis.json'.format(fname[:-4])
		fdir = os.path.join(INPUT_DIR,fname)
		score = music21.converter.parse(fdir)
		chordanalysis = chordal_analysis(score)
		x = score.write()
		copyfile(x, os.path.join(OUTPUT_DIR, fout_xml))
		with open(os.path.join(OUTPUT_DIR, fout_json), 'w') as f:
			f.write(json.dumps(chordanalysis, sort_keys=True, indent=4))
			f.close()
		minseg_score, perc = evaluate(score, chordanalysis)
		print perc
		score.show()
		print 'Done.'
		break
