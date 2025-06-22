import os
import argparse
import numpy as np
import librosa 
import matplotlib.pyplot as plt

#CONSTANTS
SR = 22050
N_FFT = 4096
HOP_LENGTH = 512
N_BANDS = 5
AMP_THRESHOLD = -30 # dB
RADIUS = 10 # For Pruning

def plot(S_db,freqs,times,peaks,save_path = None):
    plt.figure(figsize=(10,6))

    librosa.display.specshow(
        S_db, sr = SR, hop_length= HOP_LENGTH, x_axis = 'time', y_axis = 'log', cmap = 'viridis'
    )

    plt.colorbar(format='%+2.0f dB')
    plt.title("Spectrogram with peaks")

    if peaks:
        fidx = [p[0] for p in peaks]
        tidx = [p[1] for p in peaks]

        fpeak = [freqs[f] for f in fidx]
        tpeak = [times[t] for t in tidx]

        plt.scatter(
            tpeak,fpeak,s = 10,c = 'cyan', edgecolors='black'
        )


    plt.xlabel("Time (MM:SS)")
    plt.ylabel("Frequency (Hz)")

    if save_path:
        folder = os.path.dirname(save_path)
        os.makedirs(folder,exist_ok = True)
        plt.savefig(save_path,dpi = 150)
        print("Saved to ",save_path)
    else:
        plt.show()


def prune(peaks,S_db):
    if len(peaks) == 0:
        return []
    
    amps = [S_db[f,t] for (f,t) in peaks]
    sort_amps = np.argsort(amps)[::-1]

    final = []

    occupied = np.zeros_like(S_db,dtype=bool) # Mask to mark occupied freq-time region (prune out weaker close by peaks)

    for i in sort_amps:
        f,t = peaks[i]
        if not occupied[f,t]:
            final.append((f,t))

            f_start = max(0,f-RADIUS)
            t_start = max(0,t-RADIUS)

            f_end = min(S_db.shape[0], f + RADIUS + 1) # end idx excl.
            t_end = min(S_db.shape[1],t + RADIUS + 1)

            occupied[f_start:f_end,t_start:t_end] = True

    return final


def find_peaks(S_db,freqs):
    n_times = S_db.shape[1]

    # To avoid log(0) errors
    ffreqs = freqs.copy()
    mask = ffreqs<=0
    ffreqs[mask] = 1e-6

    log_freqs = np.log10(ffreqs)

    # Divide into N_BANDS bands 
    bands = []
    edges = np.linspace(log_freqs[0],log_freqs[-1],N_BANDS+1)

    for i in range(5):
        band_idx = np.where((log_freqs>=edges[i]) & (log_freqs<edges[i+1]))[0]
        bands.append(band_idx)
    
    peaks = []
    for t in range(n_times):
        for band_idx in bands:
            if len(band_idx) == 0:
                continue

            band_val = S_db[band_idx,t]

            max_idx = np.argmax(band_val) # idx of max mag in band
            
            freq_idx = band_idx[max_idx] # map local to global

            if S_db[freq_idx,t] >= AMP_THRESHOLD:
                peaks.append((freq_idx,t))
    
    return peaks
    

def get_spectrogram(y, sr):
    stft = librosa.stft(y,n_fft=N_FFT,hop_length=HOP_LENGTH)
    magnitude = np.abs(stft)

    S_db = librosa.amplitude_to_db(magnitude,ref = np.max)

    freqs = librosa.fft_frequencies(sr = sr,n_fft= N_FFT)

    n_times = S_db.shape[1]
    frame_indices = np.arange(n_times)

    times = librosa.frames_to_time(frame_indices,sr = sr,hop_length= HOP_LENGTH)

    return S_db, freqs, times


def load_audio(file_path):
    y, sr = librosa.load(file_path,sr = SR, mono = True)
    
    return y ,sr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path")
    parser.add_argument("--plot",action="store_true")
    args = parser.parse_args()

    if not args.audio_path.lower().endswith(".mp3"):
        print("Only .mp3 files allowed.")
        exit(1)
    
    y,sr = load_audio(args.audio_path)

    S_db, freqs, times = get_spectrogram(y,sr)

    all_peaks = find_peaks(S_db,freqs)
    print("All Peaks: ",len(all_peaks))

    final_peaks = prune(all_peaks,S_db)

    print("Pruned Peaks: ",len(final_peaks))

    if args.plot:
        filename = os.path.splitext(os.path.basename(args.audio_path))[0]
        save_path = f"plots/{filename}_peaks.png"
        plot(S_db,freqs,times,final_peaks,save_path = save_path)
    else:
        plot(S_db,freqs,times,final_peaks)
