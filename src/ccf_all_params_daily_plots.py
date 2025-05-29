import os
import ast
import math
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
from matplotlib.lines import Line2D

# --- Function Definitions ---

def load_ccf_data(file, foldername):
    df = pd.read_csv(os.path.join(foldername, file))
    file_base = os.path.basename(file)
    ccf_locations = ast.literal_eval(df.loc[0, 'ccf_locations'])
    x, y = ccf_locations[::2], ccf_locations[1::2]
    return df, file_base, x, y

def plot_kde(df, x, y, file_base, no_of_crickets, foldername):
    plt.figure(figsize=(10, 10))
    df1 = df[df['dlc_node'] == 1]
    sns.kdeplot(data=df1, x='ccf_zaber_x', y='ccf_zaber_y', fill=True, cmap="Greys", thresh=0.01, levels=1000)
    plt.scatter(x, y, marker='H', s=1000, color='black', edgecolors='black', alpha=0.2)
    for i, (xi, yi) in enumerate(zip(x, y), 1):
        plt.text(xi, yi, str(i), ha='center', va='center', fontsize=12, alpha=0.6, color='white')
    extra_info = r"$\bf{density\ of\ zaber\ positions}$"
    plt.title(f"{file_base}_{no_of_crickets}\n{extra_info}")
    save_path = os.path.join(foldername, f'kdeplot_{file_base}.png')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close()

def plot_trajectory(df, x, y, file_base, no_of_crickets, foldername):
    plt.figure(figsize=(12, 10))
    scatter = plt.scatter(df['ccf_zaber_x'], df['ccf_zaber_y'], c=df['relative_time'], cmap='viridis', s=10, alpha=0.5)
    plt.colorbar(scatter, label='Relative Time')
    plt.plot(df['ccf_zaber_x'], df['ccf_zaber_y'], c='lightblue', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.scatter(x, y, marker='H', s=1200, color='red', edgecolors='black', alpha=0.5)
    for i, (xi, yi) in enumerate(zip(x, y), 1):
        plt.text(xi, yi, str(i), ha='center', va='center', fontsize=12, fontweight='bold')
    plt.xlabel('zaber_x')
    plt.ylabel('zaber_y')
    plt.xlim(0, 320000)
    plt.ylim(0, 320000)
    extra_info = r"$\bf{zaber\ trajectory}$"
    plt.title(f"{file_base}_{no_of_crickets}\n{extra_info}")
    save_path = os.path.join(foldername, f'trajplot_{file_base}.png')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close()

def analyze_loss(df):
    zero_mask = df['dlc_node'] != 1
    run_ids = (zero_mask != zero_mask.shift()).cumsum()
    df['run_id'] = run_ids.where(zero_mask)
    run_lengths = df.groupby('run_id').size()
    valid_ids = run_lengths[run_lengths >= 13].index
    df['seconds'] = df['run_id'].map((run_lengths / 13).loc[valid_ids])
    return df

def plot_loss(df, x, y, file_base, no_of_crickets, foldername):
    filtered_df = df.dropna(subset=['seconds'])
    norm = Normalize(vmin=filtered_df['seconds'].min(), vmax=filtered_df['seconds'].max())

    plt.figure(figsize=(10, 10))
    sns.scatterplot(data=df, x='ccf_zaber_x', y='ccf_zaber_y', alpha=0.05, s=10, color='grey')
    scatter = sns.scatterplot(
        data=filtered_df,
        x='ccf_zaber_x',
        y='ccf_zaber_y',
        size='seconds',
        hue='relative_time',
        palette='viridis',
        sizes=(50, 500),
        alpha=0.5,
        legend='brief'
    )
    plt.scatter(x, y, marker='H', s=1200, color='black', edgecolors='black', alpha=0.2)

    hex_handle = Line2D([0], [0], marker='H', color='black', markerfacecolor='black',
                        markeredgecolor='black', alpha=0.2, markersize=15, linestyle='None',
                        label='Release Tile Locations')

    handles, labels = scatter.get_legend_handles_labels()
    handles.append(hex_handle)
    labels.append('Release Tile Locations')
    legend = plt.legend(handles=handles, labels=labels, bbox_to_anchor=(1, 1), loc='upper left', fontsize=14)
    for text in legend.get_texts():
        text.set_color("gray")
    legend.get_title().set_color("gray")
    legend.set_frame_on(False)

    for i, (xi, yi) in enumerate(zip(x, y), 1):
        plt.text(xi, yi, str(i), ha='center', va='center', fontsize=12, alpha=0.3)

    plt.xlabel('zaber_x')
    plt.ylabel('zaber_y')
    extra_info = r"$\bf{tracking\ loss\ (size\ indicates\ duration\ of\ loss)}$"
    plt.title(f"{file_base}_{no_of_crickets}\n{extra_info}")
    save_path = os.path.join(foldername, f'lossplot_{file_base}.png')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close()

def plot_release_tile_entry(df, trigger_times, file_base, foldername, ccf_locations_x, ccf_locations_y, title="Release Tile Entry Plot", threshold=5500):
    # --- Add distance and inside-tile indicators ---
    if len(ccf_locations_x) != 16 or len(ccf_locations_y) != 16:
        raise ValueError("ccf_locations_x and ccf_locations_y must each have 16 elements.")

    for i in range(16):
        tile_x = ccf_locations_x[i]
        tile_y = ccf_locations_y[i]
        dist_col = f'dist_to_release_tile_{i+1}'
        bin_col = f'inside_release_tile_{i+1}'

        distances = df.apply(
            lambda row: math.dist([row['ccf_zaber_x'], row['ccf_zaber_y']], [tile_x, tile_y]),
            axis=1
        )
        df[dist_col] = distances
        df[bin_col] = (distances < threshold).astype(int)

    # --- Plotting ---
    plt.figure(figsize=(40, 15.5))
    plt.ylim(0, 18)

    for t in trigger_times:
        plt.vlines(x=t, ymin=0, ymax=16, color='r')
    plt.vlines(x=0, ymin=0, ymax=16, color='g', linewidth=4)

    locations = list(range(1, 18))

    for i in locations:
        if i <= 16:
            plt.title(title, fontsize=20)
            inside_tile_times = df.relative_time[df[f'inside_release_tile_{i}'] == 1]
            plt.scatter(inside_tile_times, i * np.ones(len(inside_tile_times)), c='cornflowerblue', marker='|', s=800)

            chirped_at_tile = df.relative_time[
                (df[f'inside_release_tile_{i}'] == 1) & (df['chirped'] == 1)
            ].tolist()
            plt.scatter(chirped_at_tile, i * np.ones(len(chirped_at_tile)), c='r', marker='*', s=300, alpha=0.5)

        elif i == 17:
            chirped_times = df.relative_time[df['chirped'] == 1]
            bout_hues = df['chirp_bouts'][df['chirped'] == 1]
            sns.scatterplot(x=chirped_times, y=i * np.ones(len(chirped_times)), hue=bout_hues,
                            marker='|', s=300, alpha=0.5, legend=False)

            lost_tracking = df.relative_time[df['dlc_node'] != 1]
            sns.scatterplot(x=lost_tracking, y=i * np.ones(len(lost_tracking)), color='grey',
                            marker='|', alpha=0.01, s=2000, legend=False)

    for i in locations:
        if i <= 16:
            plt.axhline(y=i, xmin=0, color='red', linestyle='--', alpha=0.1)
        elif i == 17:
            plt.hlines(y=i, xmin=-100, xmax=np.max(df.relative_time), color='black', linestyle='-', alpha=0.1, linewidth=50)

    plt.xlim(-100, np.max(df.relative_time))
    plt.xticks(fontsize=30)
    plt.yticks(fontsize=30)
    plt.xlabel("Relative Time", fontsize=34, labelpad=20)
    plt.ylabel("Release Tile No.", fontsize=34, labelpad=20)

    extra_info = r"$\bf{entry\ into\ release tile\ and\ trigger\}$"
    plt.title(f"{file_base}_release_tile_entry\n{extra_info}", fontsize=30)

    save_path = os.path.join(foldername, f'release_tile_entry_{file_base}.png')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close()

# --- Main Script Execution ---

def main():
    parser = argparse.ArgumentParser(description="Process ccf_adj_all_params CSV files.")
    parser.add_argument("input_folder", help="Path to the input folder containing the CSV files")
    parser.add_argument("--output_folder", default=None, help="Optional path to the output folder (defaults to input folder)")
    args = parser.parse_args()

    infolder = args.input_folder
    outfolder = args.output_folder or infolder

    files = [f for f in os.listdir(infolder) if "ccf_adj_all_params" in f and f.lower().endswith('.csv')]

    for file in files:
        df, file_base, x, y = load_ccf_data(file, infolder)
        print("plotting for {}".format(file_base))
        trigger = np.unique(df.trigger.dropna())
        trigger_times = [0] + [float(df.relative_time[df.trigger == t].iloc[0]) for t in trigger]
        no_of_crickets = len(trigger)

        plot_kde(df, x, y, file_base, no_of_crickets, outfolder)
        plot_trajectory(df, x, y, file_base, no_of_crickets, outfolder)
        df = analyze_loss(df)
        plot_loss(df, x, y, file_base, no_of_crickets, outfolder)
        plot_release_tile_entry(df, trigger_times, file_base, outfolder, x, y)

if __name__ == "__main__":
    main()
