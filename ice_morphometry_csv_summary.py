import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
import psutil
import gc
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import datetime


def test_disk_write_speed(test_path: Path) -> float:
    """Quick test of disk write speed in MB/s."""
    data = "0123456789" * 1024 * 100  # ~1MB
    start = time.time()
    with open(test_path, "w") as f:
        for _ in range(100):  # ~100MB total
            f.write(data)
    end = time.time()
    os.remove(test_path)
    return 100 / (end - start)


def plot_lines_with_options(
    df: pd.DataFrame,
    df_all: pd.DataFrame,  # Add the original df_all
    out_path: Path,
    prefix: str,
    selected_columns: list,
    time_interval: int = 5,
    show_error_bars: bool = False,
    poly_degree: int = 0  # 0 means no polynomial fit
):
    """
    Plots lines for multiple columns on the same chart, with options for
    error bars (mean +/- std) and polynomial fits.

    :param df: DataFrame with average data (including 'Frame' column).
    :param df_all: The original, un-averaged DataFrame.
    :param out_path: Where to save the plot.
    :param prefix: Prefix for the output filename.
    :param selected_columns: List of columns to plot.
    :param time_interval: Time interval between frames.
    :param show_error_bars: If True, show error bars (mean +/- std).
    :param poly_degree: Degree of polynomial fit (0 for no fit).
    """

    plt.figure(figsize=(10, 6))
    plt.title(f"Metrics vs. Frame (Interval={time_interval}s)")
    plt.xlabel("Frame")
    plt.ylabel("Metric Value")

    for col in selected_columns:
        x_vals = df["Frame"].values
        y_vals = df[col].values

        # 1) Plot the line (mean)
        plt.plot(x_vals, y_vals, marker='o', linestyle='-', label=col)

        # 2) Error bars
        if show_error_bars:
            std_dev = df_all.groupby("Frame")[col].std().values  # Get std from original data
            plt.errorbar(
                x_vals,
                y_vals,
                yerr=std_dev,
                fmt='none',  # No marker/line for error bars themselves
                capsize=3,
                label=f"{col} ± Std Dev"
            )

        # 3) Polynomial fit
        if poly_degree > 0 and len(x_vals) > poly_degree:
            try:
                coeffs = np.polyfit(x_vals, y_vals, deg=poly_degree)
                poly_fn = np.poly1d(coeffs)
                x_fit = np.linspace(x_vals.min(), x_vals.max(), 100)
                y_fit = poly_fn(x_fit)
                plt.plot(x_fit, y_fit, '--', label=f"{col} Poly Fit (deg={poly_degree})")

                # ... (Trendline equation printing - as before, if needed)
            except np.RankWarning:
                print(f"Warning: Polynomial fit failed for {col} (not enough data points).")

    plt.legend()
    plt.tight_layout()

    # 4) Save plot
    out_file = out_path / f"{prefix}_metrics_vs_frame.png"
    plt.savefig(out_file, dpi=100)
    plt.close()


def reindex_and_analyze(
    input_folder: str,
    output_folder: str,
    selected_columns: list,
    time_interval: int = 5,
    use_parallel: bool = False,
    timestamp: str = None
):
    """
    1) Finds '*_morphometry_results.csv' in sorted order.
    2) Enumerates => Frame=1 => time=0s, Frame=2 => time=5s, etc.
    3) Merges all data => saves raw CSV => <prefix>_raw_data.csv
    4) Summaries for selected columns => mean/std/sem/count => <prefix>_summary_stats.csv
    5) System performance check (I/O), deciding on parallel processing.
    6) For each selected column => plot using new function.
    7) Prints final lines with references to raw data, summary, etc.
    """
    in_path = Path(input_folder)
    out_path = Path(output_folder)
    prefix = in_path.name  # e.g. if the folder is "R2", prefix = "R2"

    if not in_path.is_dir():
        raise FileNotFoundError(f"Input folder not found: {in_path}")
    if not out_path.is_dir():
        raise FileNotFoundError(f"Output folder not found: {out_path}")

    csv_files = sorted(in_path.glob("*_morphometry_results.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files matching '*_morphometry_results.csv' in input folder.")

    total_size = sum(f.stat().st_size for f in csv_files)
    print(f"📁 Found {len(csv_files)} files totaling {total_size / 1e6:.2f} MB in {in_path}")

    print("🧠 Estimating system performance (Disk I/O)...")
    disk_speed = test_disk_write_speed(out_path / "disk_test.tmp")
    print(f"📊 Disk write speed: {disk_speed:.2f} MB/s")

    use_parallel_determined = use_parallel  # Keep the user's choice initially

    # Add these diagnostic prints before the decision logic
    print("\n📊 System Performance Analysis:")
    print(f"💾 Disk I/O Speed: {disk_speed:.2f} MB/s")
    print(f"📋 Number of columns selected: {len(selected_columns)}")
    print(f"⚖️ Decision thresholds: Disk speed > 50 MB/s, Columns > 2")
    
    # Then your existing decision logic
    if disk_speed < 50:  # You can adjust this threshold
        print("⚠️  Disk I/O is slow. Disabling parallel processing.")
        use_parallel_determined = False
        print(f"   → Your disk speed ({disk_speed:.2f} MB/s) is below the 50 MB/s threshold.")
        print("   → Parallel processing with slow disks creates I/O contention, reducing performance.")
    elif len(selected_columns) <= 2:
        print("📉  Only few columns selected. Disabling parallel processing.")
        use_parallel_determined = False
        print(f"   → You selected only {len(selected_columns)} column(s).")
        print("   → The overhead of parallel processing exceeds benefits for small workloads.")
    else:
        print("✅ Disk I/O is adequate. Using parallel processing (if requested).")
        print(f"   → Your disk speed ({disk_speed:.2f} MB/s) exceeds the 50 MB/s threshold.")
        print(f"   → You selected {len(selected_columns)} columns, enough to justify parallelization.")
    
    # Final decision with clear explanation
    print(f"\n🔄 Final decision - Parallel processing enabled: {use_parallel_determined}")
    if use_parallel_determined:
        num_workers = min(os.cpu_count(), 8)  # Example: limit to 8 or available cores
        print(f"👥 Using {num_workers} worker processes")
        print(f"   → Your system has {os.cpu_count()} CPU cores available")
    else:
        print("   → Running in single-process mode for optimal performance given the constraints")

    print("🔍 Reading CSV files...")
    all_data = []
    for i, csv_file in enumerate(tqdm(csv_files, desc="Reading files"), start=1):
        frame_num = i
        time_sec = (i - 1) * time_interval

        df = pd.read_csv(csv_file)
        df["Frame"] = frame_num
        df["TimeSec"] = time_sec
        df["TimeMin"] = time_sec / 60
        df["SourceFile"] = csv_file.name
        all_data.append(df)

    df_all = pd.concat(all_data, ignore_index=True)
    print(f"✅ Merged data shape: {df_all.shape}")
    
    # Convert numeric columns to appropriate types
    numeric_columns = df_all.select_dtypes(include=['number']).columns.tolist()
    # Add known numeric columns that might not be detected
    for col in ['Frame', 'TimeSec', 'TimeMin']:
        if col in df_all.columns and col not in numeric_columns:
            numeric_columns.append(col)
    
    # Add selected columns that should be numeric
    for col in selected_columns:
        if col in df_all.columns and col not in numeric_columns:
            numeric_columns.append(col)
    
    # Convert to appropriate numeric types
    for col in numeric_columns:
        try:
            df_all[col] = pd.to_numeric(df_all[col])
        except:
            print(f"⚠️ Warning: Could not convert column '{col}' to numeric type.")
    
    print(f"✅ Applied numeric formatting to {len(numeric_columns)} columns")

    print("📈 Calculating summary statistics...")
    # Write raw data
    raw_data_file = out_path / f"{prefix}_raw_data_{timestamp}.csv"

    with open(raw_data_file, 'w', newline='') as csvfile:  # Open in write mode
        df_all.to_csv(csvfile, index=False)  # Write raw data

        # Add separator
        separator = pd.DataFrame([['NaN'] * len(df_all.columns)], columns=df_all.columns)
        separator.to_csv(csvfile, index=False, header=False)

        # Calculate and write averages
        average_data = df_all.groupby('Frame')[selected_columns].mean().reset_index()
        average_data.to_csv(csvfile, index=False, header=True)  # Write averages with header

    print(f"💾 Writing raw data and averages to {raw_data_file}")

    # If user selected columns that don't exist => skip or raise error?
    missing_cols = [c for c in selected_columns if c not in df_all.columns]
    if missing_cols:
        raise ValueError(f"Some selected columns not found: {missing_cols}")

    # We'll do a single groupby for all selected columns
    # => multi-level columns in the result: grouped_stats[column][mean/std/sem/count]
    grouped_stats = (
        df_all
        .groupby("Frame")[selected_columns]
        .agg(["mean", "std", "sem", "count"])
    )

    summary_file = out_path / f"{prefix}_summary_stats_{timestamp}.csv"
    # Flatten the multi-index columns for a nicer CSV
    grouped_stats.columns = [
        f"{col}_{stat}" for col, stat in grouped_stats.columns
    ]
    grouped_stats.reset_index(inplace=True)
    grouped_stats.to_csv(summary_file, index=False)
    print(f"💾 Writing summary stats to {summary_file}")

    # We'll reload it as a DataFrame with a hierarchical column index
    # so our plotting function can easily do grouped_stats[col]["mean"], etc.
    # Or we can keep the object before flattening if we want
    # For simplicity, let's do a second copy as 'grouped' for plotting:
    grouped = (
        df_all
        .groupby("Frame")[selected_columns]
        .agg(["mean", "std", "sem", "count"])
    )  # multi-level
    # => grouped.index = Frame

    cpu_load = psutil.cpu_percent(interval=1)
    print(f"📊 CPU load: {cpu_load:.1f}%")

    # Estimate plot time
    base_time = 0.4  # approximate time per plot
    eta = len(selected_columns) * base_time * (1 + (cpu_load / 100)) * (1 + (100 / max(disk_speed, 10)))
    print(f"⏱️ Estimated plot generation time: {eta:.1f} sec (~{eta / 60:.1f} min)")

    print(f"🎨 Generating plots for: {selected_columns}")

    # Calculate averages for plotting
    average_data = df_all.groupby('Frame')[selected_columns].mean().reset_index()

    plot_lines_with_options(
        average_data,
        df_all,  # Pass the original df_all
        out_path,
        prefix,
        selected_columns,
        time_interval,
        False,  # Error bars are now always off in this example
        0      # Poly degree is also off
    )

    print("\n✅ All done.")
    print(f"📁 Raw: {raw_data_file}")
    print(f"📁 Summary: {summary_file}")


def run_with_gui():
    """
    1) Ask user for input folder
    2) Ask user for output folder
    3) Show a column selection GUI based on the first CSV numeric columns
    4) Reindex & analyze & plot
    """
    root = tk.Tk()
    root.withdraw()

    # Prompt for input folder
    input_folder = filedialog.askdirectory(title="Select Input Folder (with *_morphometry_results.csv)")
    if not input_folder:
        messagebox.showerror("Error", "No input folder selected.")
        return

    # Check for at least one file
    test_dir = Path(input_folder)
    test_csvs = sorted(test_dir.glob("*_morphometry_results.csv"))
    if not test_csvs:
        messagebox.showerror("Error", "No CSV files found in input folder matching '*_morphometry_results.csv'")
        return

    # Prompt for output folder
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    if not output_folder:
        messagebox.showerror("Error", "No output folder selected.")
        return

    # Read the first CSV to find numeric columns
    temp_df = pd.read_csv(test_csvs[0])
    numeric_cols = temp_df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        messagebox.showerror("Error", "No numeric columns found in the first CSV.")
        return

    # Build a second window to select columns
    sel_win = tk.Toplevel()
    sel_win.title("Select Columns to Plot")

    tk.Label(sel_win, text="Choose columns to include in plotting:", font=("Arial", 12)).pack(pady=10)

    canvas = tk.Canvas(sel_win, width=400)
    scrollbar = tk.Scrollbar(sel_win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    column_vars = {}
    checkbuttons = []

    for col in numeric_cols:
        var = tk.BooleanVar(value=False)  # default not selected
        chk = tk.Checkbutton(scroll_frame, text=col, variable=var)
        chk.pack(anchor="w")
        column_vars[col] = var
        checkbuttons.append((chk, col))

    def run_analysis():
        chosen_cols = [c for c, v in column_vars.items() if v.get()]
        if not chosen_cols:
            messagebox.showerror("Error", "No columns selected!")
            return
        sel_win.destroy()
        try:
            # Generate timestamp for files
            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            
            reindex_and_analyze(
                input_folder=input_folder,
                output_folder=output_folder,
                selected_columns=chosen_cols,
                time_interval=5,  # seconds between frames
                use_parallel=False,  # Initially, don't force parallel
                timestamp=timestamp  # Pass timestamp for filenames
            )
            messagebox.showinfo("Done", f"Analysis complete!\nCheck '{output_folder}' for results.")
        except Exception as ex:
            messagebox.showerror("Error", f"Analysis failed:\n{ex}")

    tk.Button(sel_win, text="Run Analysis", bg="green", fg="white",
              command=run_analysis).pack(pady=10)

    sel_win.mainloop()


def main():
    run_with_gui()


if __name__ == "__main__":
    main()