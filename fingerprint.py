import argparse
from visualize import SR,N_FFT, HOP_LENGTH, load_audio, get_spectrogram, find_peaks, prune 

#CONSTANTS
FAN_VALUE = 15 # Degree of pairing per peak
MIN_TIME_DIFF = 0.0 # skip too close
MAX_TIME_DIFF = 2.0 # skip too far

def create_hash(peaks):
    sorted_peaks = sorted(peaks,key = lambda p : p[1])
    f_bins = [p[0] for p in sorted_peaks]
    t_idxs = [p[1] for p in sorted_peaks]

    t_sec = [idx* HOP_LENGTH/SR for idx in t_idxs]

    hashes = []
    n = len(peaks)

    for i in range(n):
        f1 = f_bins[i]
        t1 = t_sec[i]
        c = 0
        upper = min(n, i+1+FAN_VALUE*2) # limit of search

        for j in range(i+1, upper):
            f2 = f_bins[j]
            t2 = t_sec[j]
            dt = t2 - t1
            if dt < MIN_TIME_DIFF:
                continue
            if dt > MAX_TIME_DIFF:
                break

            hash = f"{f1}|{f2}|{dt:.2f}"
            hashes.append((hash,t1))
            c+=1
            if c>=FAN_VALUE:
                break

    return hashes


def fingerprint(audio_path):
    y,sr = load_audio(audio_path)
    S_db, freqs, times = get_spectrogram(y,sr)
    peaks = find_peaks(S_db,freqs)
    final = prune(peaks,S_db)

    return create_hash(final)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path")
    args = parser.parse_args()

    if not args.audio_path.lower().endswith(".mp3"):
        print("Only .mp3 files allowed.")
        exit(1)
    hashes = fingerprint(args.audio_path)

    print("Generated ",len(hashes)," hashes")
