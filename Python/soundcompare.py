# file to write matches to
match_file = 'matches.txt'
# seconds to sample audio file for
sample_time = 5
# number of points to crop from beginning of fingerprint
# 4096 samples per frame / 11025 samples per second / 3 points per frame
# = 0.124 seconds per point
crop = 0
# number of points to scan cross correlation over
span = 1200
# step size (in points) of cross correlation
step = 3
# report match when cross correlation has a peak exceeding threshold
threshold = 0.5
# minimum number of points that must overlap in cross correlation
# exception is raised if this cannot be met
min_overlap = 200

################################################################################
# import modules
################################################################################

import os
import re
import subprocess
import numpy
import math
import acoustid
import chromaprint
import gst

################################################################################
# function definitions
################################################################################

# returns variance of list
def variance(listx):
    meanx = numpy.mean(listx)
    # get mean of x^2
    meanx_sqr = 0
    for x in listx:
        meanx_sqr += x**2
    meanx_sqr = meanx_sqr / float(len(listx))
    return meanx_sqr - meanx**2

# returns correlation between lists
def correlation(listx, listy):
    if len(listx) == 0 or len(listy) == 0:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception('Empty lists cannot be correlated.')
    if len(listx) > len(listy):
        listx = listx[:len(listy)]
    elif len(listx) < len(listy):
        listy = listy[:len(listx)]
    
    meanx = numpy.mean(listx)
    meany = numpy.mean(listy)
    
    covariance = 0
    for i in range(len(listx)):
        covariance += (listx[i] - meanx) * (listy[i] - meany)
    covariance = covariance / float(len(listx))
    
    return covariance / (math.sqrt(variance(listx)) * math.sqrt(variance(listy)))

# return cross correlation, with listy offset from listx
def cross_correlation(listx, listy, offset):
    if offset > 0:
        listx = listx[offset:]
        listy = listy[:len(listx)]
    elif offset < 0:
        offset = -offset
        listy = listy[offset:]
        listx = listx[:len(listy)]
    if min(len(listx), len(listy)) < min_overlap:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception('Overlap too small: %i' % min(len(listx), len(listy)))
    return correlation(listx, listy)

# cross correlate listx and listy with offsets from -span to span
def compare(listx, listy, span, step):
    if span > min(len(listx), len(listy)):
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception('span >= sample size: %i >= %i\n'
                        % (span, min(len(listx), len(listy)))
                        + 'Reduce span, reduce crop or increase sample_time.')
    corr_xy = []
    for offset in numpy.arange(-span, span + 1, step):
        corr_xy.append(cross_correlation(listx, listy, offset))
    return corr_xy

# return index of maximum value in list
def max_index(listx):
    max_index = 0
    max_value = listx[0]
    for i, value in enumerate(listx):
        if value > max_value:
            max_value = value
            max_index = i
    return max_index

# write to a file
def write_string(string, filename):
    file_out = open(filename, 'ab')
    file_out.write(string + '\n')
    file_out.close()

################################################################################
# main code
################################################################################

filelist_a = os.listdir('Default/')

for i, file_a in enumerate(filelist_a):
    # calculate fingerprint
    duration_a, fp_encoded_a = acoustid.fingerprint_file('Default/1.mp3')
    fingerprint_a, version_a = chromaprint.decode_fingerprint(fp_encoded_a)
    print(fingerprint_a)
    # check that fingerprint length meets minimum size
    if len(fingerprint_a) - crop - span < min_overlap:
        raise Exception('Fingerprint length less than required:\n'
                        + 'File: %s\n' % file_a
                        + 'Fingerprint length: %i\n' % len(fingerprint_a)
                        + 'Required length (crop + span + min_overlap): %i\n'
                        % (crop + span + min_overlap)
                        + 'Increase sample_time, reduce span or reduce crop.')

    file_b = 'Myuglyvoice.mp3'
    # calculate fingerprint
    fpcalc_out = subprocess.getoutput('fpcalc -raw -length %i %s'
                                    % (sample_time, file_b))
    fingerprint_index = fpcalc_out.find('FINGERPRINT=') + 12
    # convert fingerprint to list of integers
    fingerprint_b = list(map(int, fpcalc_out[fingerprint_index:].split(',')))
    # check that fingerprint length meets minimum size
    if len(fingerprint_b) - crop - span < min_overlap:
        raise Exception('Fingerprint length less than required:\n'
                        + 'File: %s\n' % file_b
                        + 'Fingerprint length: %i\n' % len(fingerprint_b)
                        + 'Required length (crop + span + min_overlap): %i\n'
                        % (crop + span + min_overlap)
                        + 'Increase sample_time, reduce span or reduce crop.')

     # cross correlation between fingerprints
    corr_ab = compare(fingerprint_a[crop:], fingerprint_b[crop:], span, step)
    max_corr_index = max_index(corr_ab)
    max_corr_offset = -span + max_corr_index * step

    # report matches
    if corr_ab[max_corr_index] > threshold:
        print('%s and %s match with correlation of %.4f at offset %i'
                % (file_a, file_b, corr_ab[max_corr_index], max_corr_offset))
        write_string('%s\t%s\t%.6f\t%i'
                    % (file_a, file_b, corr_ab[max_corr_index],
                    max_corr_offset),
                    match_file)